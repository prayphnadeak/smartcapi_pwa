
import os
import numpy as np
import time
from celery import shared_task
from app.core.logger import ml_logger
from app.services.diarization_service import speaker_service
from app.core.config import settings
import redis
import json

# Redis connection for publishing events
redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)

@shared_task(name="process_audio_chunk", ignore_result=True)
def process_audio_chunk(audio_bytes: bytes, interview_id: int, timestamp: float, chunk_seq: int):
    """
    Process a raw audio chunk:
    1. Validate Audio (Simple VAD check via RMS)
    2. Identify Speaker (RF Model)
    3. Publish 'segment.speaker' event
    """
    try:
        t0 = time.time()
        
        # Convert bytes to numpy float32
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # 1. Simple VAD (RMS)
        rms = np.sqrt(np.mean(audio_array**2))
        
        # Determine silence
        # (Using a slightly higher threshold for 'active processing' decision vs mere silence detection)
        is_speech = rms > 0.01 
        
        speaker_label = "silence"
        confidence = 1.0
        
        if is_speech:
            # 2. Speaker Prediction
            # Run RF model on this chunk
            # Note: 0.5s chunks might be too short for high accuracy, but it's "real-time" labeling
            # ideally we accumulate a bit, but here we process what we get
            speaker_label, confidence = speaker_service.predict_speaker_from_memory_sync(audio_array, settings.SAMPLE_RATE)
        
        # 3. Publish Result
        payload = {
            "type": "segment.speaker",
            "interview_id": interview_id,
            "timestamp": timestamp, # Start time of this chunk
            "duration": len(audio_array) / settings.SAMPLE_RATE,
            "chunk_seq": chunk_seq,
            "speaker": speaker_label,
            "confidence": confidence,
            "rms": float(rms)
        }
        
        redis_client.publish(f"interview.{interview_id}.events", json.dumps(payload))
        
        dt = time.time() - t0
        # ml_logger.debug(f"AudioWorker: Processed chunk {chunk_seq} ({speaker_label}) in {dt:.3f}s")
        
    except Exception as e:
        ml_logger.error(f"AudioWorker Error: {str(e)}")
