import redis
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logger import api_logger

try:
    # Sync client for worker processes (non-async)
    redis_client = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=False)
    
    # Async client for FastAPI (ws.py)
    # decode_responses=True for Channels (strings), False for Queues might be mixed.
    # We will use two async clients if needed, or just handle bytes.
    # Let's use decode_responses=False for maximum flexibility.
    async_redis_client = aioredis.from_url(settings.CELERY_BROKER_URL, decode_responses=False)
except Exception as e:
    api_logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None
    async_redis_client = None

class RedisQueue:
    # Input Queues (Workers consume these)
    AUDIO_PROCESSING = "queue:audio_processing"  # (interview_id, timestamp, audio_base64)
    AUDIO_WHISPER = "queue:audio_whisper"        # (interview_id, timestamp, audio_base64)
    
    # Internal component queues
    MERGER_SEGMENTS = "queue:merger:segments"    # From RF Worker -> (interview_id, start, end, speaker)
    MERGER_TRANSCRIPTS = "queue:merger:transcripts" # From Whisper Worker -> (interview_id, start, end, text)
    LLM_EXTRACTION = "queue:llm_extraction"      # From Merger -> (interview_id, transcript_with_speaker)

class RedisChannel:
    # PubSub Channels
    @staticmethod
    def interview_updates(interview_id: int) -> str:
        return f"channel:interview_updates:{interview_id}"
