from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Base schema for queue messages
class BaseMessage(BaseModel):
    job_id: str
    timestamp: float

# Message schema for audio chunks
class AudioChunkMessage(BaseMessage):
    interview_id: int
    user_id: int
    audio_data_b64: str
    sample_rate: int = 16000

# Message schema for ready segments
class SegmentReadyMessage(BaseMessage):
    interview_id: int
    segment_path: str
    speaker: str
    duration: float
    metadata: Optional[Dict[str, Any]] = None

# Message schema for ready transcripts
class TranscriptReadyMessage(BaseMessage):
    interview_id: int
    segment_path: str
    text: str
    language: str = "id"
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

# Message schema for ready extraction
class ExtractionReadyMessage(BaseMessage):
    interview_id: int
    extracted_data: Dict[str, Any]
    source_segments: List[str]

# Message schema for progress updates
class ProgressMessage(BaseMessage):
    interview_id: int
    stage: str  # "audio", "transcription", "extraction"
    progress: float  # 0.0 to 1.0
    message: str
    metadata: Optional[Dict[str, Any]] = None
