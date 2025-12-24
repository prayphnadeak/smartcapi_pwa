import asyncio
import json
import traceback
from collections import defaultdict
from typing import List, Dict

from app.core.config import settings
from app.core.logger import ml_logger
from app.core.redis_client import async_redis_client, RedisQueue, RedisChannel

class Interviewstate:
    def __init__(self, interview_id):
        self.interview_id = interview_id
        self.segments: List[dict] = [] # History of speaker segments
        self.current_transcript: str = ""
        self.last_finalized_time: float = 0.0
        self.silence_counter: int = 0  # Count continuous silence segments

    def add_segment(self, segment: dict):
        self.segments.append(segment)
        
        # Check silence for finalization
        if segment.get("is_silence"):
            duration = segment.get("end_time") - segment.get("start_time")
            self.silence_counter += duration
        else:
            self.silence_counter = 0.0

    def should_finalize(self) -> bool:
        # Finalize if we have > 1.0s of continuous silence
        return self.silence_counter >= 1.0 and self.current_transcript.strip()

    def get_majority_speaker(self, start: float, end: float) -> str:
        """
        Determine the dominant speaker in a given time range.
        """
        counts = defaultdict(float)
        total_overlap = 0.0
        
        for seg in self.segments:
            # Check overlap
            seg_start = seg.get("start_time", 0.0)
            seg_end = seg.get("end_time", 0.0)
            
            # Intersection
            overlap_start = max(start, seg_start)
            overlap_end = min(end, seg_end)
            
            if overlap_end > overlap_start:
                duration = overlap_end - overlap_start
                speaker = seg.get("speaker", "unknown")
                counts[speaker] += duration
                total_overlap += duration
                
        if not counts:
            return "unknown"
            
        # Return speaker with max duration
        # If 'respondent' exists and has significant presence, prefer it?
        # For now, strict majority.
        return max(counts, key=counts.get)

async def process_messages():
    ml_logger.info("Starting Merger/Aligner Worker...")
    
    interviews: Dict[int, Interviewstate] = {}
    
    try:
        await async_redis_client.ping()
        ml_logger.info("Connected to Redis.")
    except Exception as e:
        ml_logger.error(f"Failed to connect to Redis: {e}")
        return

    while True:
        try:
            # Pop from both queues (Prioritize TRANSCRIPTS!)
            result = await async_redis_client.blpop(
                [RedisQueue.MERGER_TRANSCRIPTS, RedisQueue.MERGER_SEGMENTS], 
                timeout=1
            )
            
            if not result:
                continue
                
            queue_name, data_json = result
            
            # CRITICAL FIX: Redis blpop returns bytes, decode to string
            if isinstance(queue_name, bytes):
                queue_name = queue_name.decode('utf-8')
            
            data = json.loads(data_json)
            interview_id = data.get("interview_id")
            
            # DEBUG LOG
            ml_logger.info(f"Merger received from {queue_name}: {str(data)[:100]}...")
            
            if not interview_id:
                continue
                
            if interview_id not in interviews:
                interviews[interview_id] = Interviewstate(interview_id)
            state = interviews[interview_id]
            
            if queue_name == RedisQueue.MERGER_SEGMENTS:
                # Handle Segment
                state.add_segment(data)
                
                # Check finalization trigger (Silence)
                if state.should_finalize():
                    final_text = state.current_transcript.strip()
                    
                    if final_text:
                        # Determine speaker for this block
                        # Heuristic: use majority speaker of the whole block time
                        # Not perfect but consistent
                        # We need start/end of the transcript. 
                        # Whisper gives it, but we stored it in state.current_transcript? No.
                        # We need to track the time range of current_transcript. 
                        # Simplification: Use the time of the last transcript update.
                        
                        # Better: Process Finalization when we receive a TRANSCRIPT update, not just silence.
                        # Or: just emit what we have.
                        
                        speaker = "respondent" # Default
                        # (TODO: Better speaker lookup for the whole finalized block)
                        
                        # Publish to LLM
                        payload = {
                            "interview_id": interview_id,
                            "text": final_text,
                            "speaker": speaker,
                            "is_final": True
                        }
                        await async_redis_client.rpush(RedisQueue.LLM_EXTRACTION, json.dumps(payload))
                        
                        # Notify UI of finalized block
                        channel = RedisChannel.interview_updates(interview_id)
                        await async_redis_client.publish(channel, json.dumps({
                            "type": "transcript_finalized",
                            "text": final_text,
                            "speaker": speaker
                        }))
                        
                        # Reset
                        state.current_transcript = ""
                        state.silence_counter = 0

            elif queue_name == RedisQueue.MERGER_TRANSCRIPTS:
                # Handle Transcript
                text = data.get("text", "")
                start = data.get("start_time")
                end = data.get("end_time")
                
                if not text:
                    continue
                
                # Update current view
                state.current_transcript = text
                
                # Identify speaker for this specific fragment
                speaker = state.get_majority_speaker(start, end)
                
                # Push real-time update to UI
                ml_logger.info(f"Partial Transcript Update: {text[:30]}... Speaker: {speaker}")
                channel = RedisChannel.interview_updates(interview_id)
                await async_redis_client.publish(channel, json.dumps({
                    "type": "transcript_partial",
                    "text": text,
                    "speaker": speaker,
                    "start": start,
                    "end": end
                }))
                
                # FIX: If transcript is FINAL, we should finalize this block immediately
                # Trust Whisper's endpoint detection
                is_final_segment = data.get("is_final", False)
                if is_final_segment:
                    ml_logger.info(f"Received FINAL transcript segment: {text} | Time: {start}-{end}")
                    ml_logger.info(f"Determined Majority Speaker for Final Segment: '{speaker}'")
                    
                    # Publish to LLM
                    # (Full Transcription Mode: Send ALL to LLM, let LLM extract semantically)
                    payload = {
                        "interview_id": interview_id,
                        "text": text,
                        "speaker": speaker, # Speaker from get_majority_speaker
                        "is_final": True
                    }
                    
                    # FILTER REMOVED: Per user request, we transcribe everything.
                    # LLM will handle extraction intelligently.
                    await async_redis_client.rpush(RedisQueue.LLM_EXTRACTION, json.dumps(payload))
                    ml_logger.info(f"Pushed to LLM Queue: {text[:50]}...")
                    
                    # Notify UI of finalized block
                    channel = RedisChannel.interview_updates(interview_id)
                    await async_redis_client.publish(channel, json.dumps({
                        "type": "transcript_finalized",
                        "text": text,
                        "speaker": speaker
                    }))
                    
                    # Reset state
                    state.current_transcript = ""
                    state.silence_counter = 0
                
        except Exception as e:
            ml_logger.error(f"Merger Loop Error: {e}")
            traceback.print_exc()
            await asyncio.sleep(1)

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(process_messages())
