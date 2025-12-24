import asyncio
import json
import base64
import time
import numpy as np
import traceback

from app.core.config import settings
from app.core.logger import ml_logger
from app.core.redis_client import async_redis_client, RedisQueue, RedisChannel, redis_client as sync_redis_client
from app.services.silence_detector import silence_detector
from app.services.diarization_service import speaker_service
from app.db.database import SessionLocal
from app.db.models import Interview

async def process_audio_chunk(data: dict):
    """
    Process a single audio chunk from the queue.
    1. VAD check
    2. Speaker Identification (RF)
    3. Buffer Respondent Audio
    4. Trigger Extraction on Silence
    """
    try:
        audio_b64 = data.get("audio_data")
        interview_id = data.get("interview_id")
        user_id = data.get("user_id") # Dynamic Logged-in User
        timestamp = data.get("timestamp")
        
        if not audio_b64 or not interview_id:
            return

        # Redis Keys
        key_current_q = f"interview:{interview_id}:current_question"
        key_buffer = f"interview:{interview_id}:respondent_buffer"
        key_last_speech = f"interview:{interview_id}:last_speech_time"
        
        # 0. Get Current Question (Fast check)
        # If no question active, we might skip buffering to save memory, or buffer anyway?
        # Let's skip buffering if no question is focused, assuming interview hasn't started or is done.
        current_q_id = await async_redis_client.get(key_current_q)
        if not current_q_id:
            # Maybe just log debug and return, or allow standard processing without extraction?
            # For now, let's process standard "speaker detection" only for UI but skip buffering.
            pass

        # Decode audio
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # 1. Silence Detection
        is_silence = silence_detector.is_silence(audio_array)
        
        speaker_label = "silence"
        confidence = 1.0
        
        if not is_silence:
            # 2. Identify Speaker
            speaker_label, confidence = await speaker_service.predict_speaker_from_memory(
                audio_array, 
                settings.SAMPLE_RATE
            )
            
            # Update last speech time
            await async_redis_client.set(key_last_speech, timestamp)
            
            # 3. Buffer Respondent Audio
            # We ONLY want to extract Respondent answers.
            # 3. Buffer Respondent Audio
            # LOGIC:
            # - IF speaker is the enumerator -> SKIP (Don't buffer)
            # - IF speaker is NOT enumerator (Unknown, Other User, or explicitly Respondent) -> BUFFER (Process)
            
            should_process = True
            
            # 3a. Identify Current Enumerator (Dynamic or Cached)
            if user_id:
                # Priority: Use the user_id from the payload (The logged-in user conducting the interview)
                cached_enum_id = str(user_id)
            else:
                 # Fallback: Cache miss, fetch from DB
                 key_enum_id = f"interview:{interview_id}:enumerator_id"
                 cached_enum_id = await async_redis_client.get(key_enum_id)
            
            if not cached_enum_id:
                # Cache miss, fetch from DB
                try:
                    # Use sync session in async way or just quick lookup
                    # Since we are in async function, ideally we use async DB or run in executor
                    # But for now, SessionLocal is sync. 
                    # Optimization: This only happens ONCE per interview per worker restart.
                    db = SessionLocal()
                    interview = db.query(Interview).filter(Interview.id == interview_id).first()
                    if interview:
                        cached_enum_id = str(interview.enumerator_id)
                        await async_redis_client.set(key_enum_id, cached_enum_id, ex=3600*24) # 24h cache
                    db.close()
                except Exception as ex:
                    ml_logger.error(f"Error fetching enumerator ID: {ex}")
            
            if cached_enum_id:
                enumerator_label = f"user_{cached_enum_id}"
                
                # Check for Match
                # USER REQUEST: Process EVERYTHING. Do not filter Enumerator.
                # if speaker_label == enumerator_label or speaker_label == "enumerator":
                #      should_process = False
                # else:
                should_process = True
                # speaker_label = "respondent" # We can keep the label for UI, but process it.
            
            # 3b. Buffer if it is Valid Respondent Speech
            if speaker_label != "silence" and should_process:
                 if current_q_id:
                     await async_redis_client.rpush(key_buffer, audio_b64)
            
            # PUSH SEGMENT TO MERGER
            duration = len(audio_array) / settings.SAMPLE_RATE
            # Estimate end time (timestamp is start)
            # Ensure timestamp is float
            try:
                ts_float = float(timestamp)
            except:
                ts_float = time.time()
                
            segment_payload = {
                "interview_id": interview_id,
                "start_time": ts_float,
                "end_time": ts_float + duration,
                "is_silence": False,
                "speaker": speaker_label,
                "confidence": confidence
            }
            await async_redis_client.rpush(RedisQueue.MERGER_SEGMENTS, json.dumps(segment_payload))
        
        else:
            # IS SILECE
            # 4. Check for Trigger
            if current_q_id:
                last_speech = await async_redis_client.get(key_last_speech)
                if last_speech:
                    silence_duration = time.time() - float(last_speech)
                    
                    if silence_duration > settings.SILENCE_MIN_DURATION:
                        # Check buffer size
                        buffer_len = await async_redis_client.llen(key_buffer)
                        if buffer_len > 0:
                            ml_logger.info(f"Silence detected ({silence_duration:.2f}s) -> Triggering Extraction for Q {current_q_id}")
                            
                            # Legacy Extraction Trigger (DISABLED per User Request)
                            # Triggers on silence, but we now use Merger + Whisper Final
                            
                            # Just clear buffer to avoid memory leak if we are still buffering
                            await async_redis_client.delete(key_buffer)
                            
                            # audio_list_b64 = await async_redis_client.lrange(key_buffer, 0, -1)
                            # ... (Legacy code commented out) ...
                            ml_logger.info(f"Silence detected ({silence_duration:.2f}s) - Skipping legacy trigger (using Merger)")

        # UI Update (Speaker ID visualization)
        if not is_silence:
            ui_update = {
                "type": "speaker_detected",
                "speaker": speaker_label,
                "confidence": confidence
            }
            channel = RedisChannel.interview_updates(interview_id)
            await async_redis_client.publish(channel, json.dumps(ui_update))

    except Exception as e:
        ml_logger.error(f"Error processing audio chunk: {str(e)}")
        import traceback
        traceback.print_exc()

async def publish_progress(interview_id, message):
    try:
        if async_redis_client:
            channel = RedisChannel.interview_updates(interview_id)
            await async_redis_client.publish(channel, json.dumps(message))
    except:
        pass

async def main():
    ml_logger.info("Starting Audio Processor Worker...")
    
    # Ensure Redis is connected
    try:
        ping = await async_redis_client.ping()
        if ping:
            ml_logger.info("Connected to Redis.")
    except Exception as e:
        ml_logger.error(f"Failed to connect to Redis: {e}")
        return

    from app.db.database import SessionLocal
    from app.services.realtime_extraction import realtime_extraction_service
    from app.services.question_manager import QuestionManager # If needed to get Question object
    from app.db.models import QuestionnaireQuestion

    # Internal helper to get DB session
    def get_db_session():
        return SessionLocal()

    while True:
        try:
            # Blocking pop from queue
            result = await async_redis_client.blpop(RedisQueue.AUDIO_PROCESSING, timeout=1)
            
            if result:
                queue_name, data_json = result
                data = json.loads(data_json)
                
                # --- PROCESS AUDIO CHUNK ---
                # We inline the logic here or keep calling process_audio_chunk, 
                # but we need to inject the new logic. 
                # For cleaner code, let's update process_audio_chunk itself or wrap it.
                # Since we are replacing the file content, let's just call the updated process_audio_chunk 
                # (which we need to define/update in the file).
                
                # ... Wait, I am replacing 'main' but I also need to update 'process_audio_chunk'.
                # Let's do a multi_replace for both if possible, or just replace the whole file if it's cleaner.
                # actually, let's just call process_audio_chunk and update that function in a separate call 
                # to keep this tool call simple or do it all here? 
                # The tool call replaces lines. I will do 2 calls.
                
                await process_audio_chunk(data)
                
        except Exception as e:
            ml_logger.error(f"Worker Loop Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
