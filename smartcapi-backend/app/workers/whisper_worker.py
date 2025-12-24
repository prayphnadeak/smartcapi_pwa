import asyncio
import json
import base64
import time
import numpy as np
import tempfile
import os
import traceback
from typing import Dict, List, Tuple
import collections

from app.core.config import settings
from app.core.logger import ml_logger
from app.core.redis_client import async_redis_client, RedisQueue, RedisChannel
from app.services.whisper_service import whisper_service
from app.processing.audio.audio_utils import save_audio, compute_rms
from app.processing.models.loader import load_rf_model
from app.processing.audio.feature_extractor import extract_mfcc_features
from app.db.database import SessionLocal
from app.db.models import LogType, ProcessingLog, Interview, RoleEventLog, RoleEventType, RoleActionTaken

# Configuration
# OpenAI Whisper API (Network latency implies we should be less aggressive than local)
TRANSCRIBE_INTERVAL = 2.0  # seconds
MIN_DURATION_TO_TRANSCRIBE = 2.0 # seconds
MAX_CONTEXT_WINDOW = 30.0 # seconds (keep reasonable context)
SAMPLE_RATE = settings.SAMPLE_RATE

class InterviewState:
    def __init__(self, interview_id):
        self.interview_id = interview_id
        # We keep a deque of float chunks for efficient appending/popping
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_start_time = 0.0 # Timeline position of the start of audio_buffer
        self.last_transcribe_time = 0.0
        
        # We track what we have "finalized" to avoid re-emitting
        # But for the model, we always feed some context (overlap)
        self.last_finalized_time = 0.0 
        self.accumulated_text = ""
        
        # VAD State
        self.is_speaking = False
        self.last_speech_time = 0.0
        self.silence_start_time = 0.0

    def add_audio(self, samples: np.ndarray, timestamp: float):
        if len(self.audio_buffer) == 0:
            self.buffer_start_time = timestamp
            self.audio_buffer = samples
        else:
            self.audio_buffer = np.concatenate((self.audio_buffer, samples))
            
        # Safety: Cap buffer size to avoid memory leak if no transcription happens
        max_samples = 60 * SAMPLE_RATE # 60 seconds max buffer
        if len(self.audio_buffer) > max_samples:
            # Drop oldest
            drop_count = len(self.audio_buffer) - max_samples
            self.audio_buffer = self.audio_buffer[drop_count:]
            self.buffer_start_time += (drop_count / SAMPLE_RATE)

    def get_processing_window(self) -> Tuple[np.ndarray, float]:
        """
        Get audio to transcribe. 
        We send the whole buffer up to 30s.
        """
        return self.audio_buffer, self.buffer_start_time

    def commit_segment(self, end_time: float):
        """
        Mark audio up to end_time as finalized. 
        We strip it from buffer, BUT keep some overlap for context!
        """
        # Calculate samples to drop
        # We want to drop audio that is older than end_time, 
        # BUT we might want to keep 1-2s for context? 
        # Actually FasterWhisper handles context if we give prompt, but prompt is text.
        # Giving audio context (overlap) is better for VAD.
        
        # For simplicity in this implementation: 
        # Drop everything up to end_time.
        
        duration_to_drop = end_time - self.buffer_start_time
        if duration_to_drop <= 0:
            return

        samples_to_drop = int(duration_to_drop * SAMPLE_RATE)
        
        if samples_to_drop >= len(self.audio_buffer):
            # Clear all
            self.audio_buffer = np.array([], dtype=np.float32)
            self.buffer_start_time = end_time
        else:
            self.audio_buffer = self.audio_buffer[samples_to_drop:]
            self.buffer_start_time += (samples_to_drop / SAMPLE_RATE)

# Global state
interviews: Dict[int, InterviewState] = {}
rf_model = None

async def process_audio_chunk(data: dict):
    try:
        audio_b64 = data.get("audio_data")
        interview_id = data.get("interview_id")
        timestamp = data.get("timestamp")
        
        if not audio_b64 or not interview_id:
            return

        # Decode
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        if interview_id not in interviews:
            interviews[interview_id] = InterviewState(interview_id)
        
        state = interviews[interview_id]
        
        # 0. Check RMS for Activity (Robust VAD)
        # We use a slightly higher threshold here to avoid noise triggering
        # silence_detector is robust, but we can also do a quick check
        from app.services.silence_detector import silence_detector
        
        # Use simple RMS first for speed, but rely on silence_detector thresholds
        rms = compute_rms(audio_array)
        
        # Use a hardcoded higher threshold if noise is issue (User log showed 0.05)
        # but let's trust the settings or override if needed. 
        # Plan: "Tune VAD". Let's set a local effective threshold.
        # If logs showed 0.05, that's high. If it was hallucinating, maybe it wasn't detecting silence?
        # Actually, if it hallucinates "during silence", it means it THOUGHT it was speech (or processed silence as speech).
        # Increasing threshold prevents processing noise as speech.
        
        # UPDATE: Tuning for VPS Hallucinations.
        # The previous override to 0.01 was too sensitive (triggered on noise).
        # We will respect settings.SILENCE_THRESHOLD if reasonable, or default to 0.02.
        EFFECTIVE_THRESHOLD = getattr(settings, 'SILENCE_THRESHOLD', 0.02)
        
        # Safety clamp: Don't let it be too high (miss speech) or too low (hallucinate)
        # 0.1 is too high (cuts speech). 0.005 is too low (noise).
        # Let's clamp it between 0.015 and 0.05
        EFFECTIVE_THRESHOLD = max(0.015, min(EFFECTIVE_THRESHOLD, 0.05))

        is_silence_frame = rms < EFFECTIVE_THRESHOLD
        
        now = time.time()
        
        if not is_silence_frame:
            # Speaking
            state.is_speaking = True
            state.last_speech_time = now
            state.silence_start_time = 0.0
        else:
            # Silent
            if state.is_speaking:
                # Just stopped speaking?
                if state.silence_start_time == 0.0:
                    state.silence_start_time = now
            
            # If silence persists...
            # User requested "utuh" (whole) transcription. Increasing wait time to 1.2s
            # prevents cutting off mid-thought pauses.
            if state.silence_start_time > 0 and (now - state.silence_start_time) > 1.2: 
                 state.is_speaking = False

        # Add to buffer
        state.add_audio(audio_array, timestamp)

        # DECISION: To Transcribe or Not?
        # Trigger conditions:
        # 1. We were speaking, and now we've been silent for > 0.5s (End of sentence/phrase)
        # 2. Buffer is getting too full (> 10s) and we assume valid speech (latency safeguard)
        
        should_transcribe = False
        
        audio_duration = len(state.audio_buffer) / SAMPLE_RATE
        
        # Condition 1: Silence detected after speech
        # We need to detect the EDGE of silence. 
        # Logic: If we are NOT speaking (meaning silence verified) AND we have enough audio.
        if not state.is_speaking and audio_duration > MIN_DURATION_TO_TRANSCRIBE and (now - state.last_transcribe_time) > TRANSCRIBE_INTERVAL:
             should_transcribe = True
        
        # Condition 2: Buffer overflow protection (Real-time fallback)
        if audio_duration > 10.0:
             should_transcribe = True

        if should_transcribe:
            state.last_transcribe_time = now
            state.silence_start_time = 0.0 # Reset detection to avoid double triggers
            
            # 1. Get Audio
            audio_window, window_start = state.get_processing_window()
            
            if len(audio_window) == 0:
                return

            # --- SPEAKER IDENTIFICATION SKIPPED (Full Transcription Mode) ---
            # Policy: "Transkripsi dilakukan tanpa memandang enumerator atau responden."
            # We process all audio that triggered VAD/Silence logic.
            
            ml_logger.info(f"Processing audio segment ({len(audio_window)/SAMPLE_RATE:.2f}s) for Full Transcription...")

            # 2. Save to temp
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name
            
            save_audio(audio_window, temp_path, SAMPLE_RATE)
            
            try:
                # 3. Transcribe with OpenAI / Whisper
                # It returns segments!
                result = await whisper_service.transcribe(
                    temp_path, 
                    language="id", 
                    initial_prompt=state.accumulated_text[-200:] # Feed last text as prompt context
                )
                
                segments = result.get("segments", [])
                
                final_text_chunk = ""
                final_end_time = window_start
                has_final = False
                
                # Logic: Since we triggered on silence, we assume the ENTIRE buffer is a valid phrase.
                # We can mark it all as final.
                
                for seg in segments:
                    # Handle both object and dict access for robustness
                    if isinstance(seg, dict):
                         final_text_chunk += seg.get("text", "") + " "
                         final_end_time = window_start + seg.get("end", 0)
                    else:
                         final_text_chunk += seg.text + " "
                         final_end_time = window_start + seg.end
                    has_final = True
                
                if has_final:
                    state.accumulated_text += final_text_chunk
                    
                    # Emit Final
                    payload_final = {
                        "interview_id": interview_id,
                        # We don't have perfect start time for merged chunks easily here,
                        # but Merger handles sequence.
                        "start_time": window_start, 
                        "end_time": final_end_time,
                        "text": final_text_chunk.strip(),
                        "is_final": True
                    }
                    if async_redis_client:
                         ml_logger.info(f"VAD Triggered: Sending FINAL transcript: {final_text_chunk[:50]}...")
                         await async_redis_client.rpush(RedisQueue.MERGER_TRANSCRIPTS, json.dumps(payload_final))
                    
                    # Commit (Clear Buffer)
                    state.commit_segment(final_end_time)
            
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    except Exception as e:
        ml_logger.error(f"Whisper Worker Error: {str(e)}")
        # traceback.print_exc()

async def main():
    ml_logger.info("Starting Streaming Whisper Worker (GPU)...")
    
    try:
        await async_redis_client.ping()
        ml_logger.info("Connected to Redis.")
        
        global rf_model
        rf_model = load_rf_model()
        if rf_model:
            ml_logger.info("Speaker Identification Model (RF) Enabled.")
        else:
            ml_logger.warning("Speaker Identification Model (RF) NOT found. All audio will be transcribed.")
            
    except Exception as e:
        ml_logger.error(f"Failed to connect to Redis or Load Model: {e}")
        return

    while True:
        try:
            result = await async_redis_client.blpop(RedisQueue.AUDIO_WHISPER, timeout=1)
            
            if result:
                _, data_json = result
                data = json.loads(data_json)
                await process_audio_chunk(data)
                
        except Exception as e:
            ml_logger.error(f"Whisper Loop Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
