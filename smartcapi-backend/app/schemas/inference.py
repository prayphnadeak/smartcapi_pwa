from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Schema for speaker recognition request
class SpeakerRecognitionRequest(BaseModel):
    audio_path: str
    user_id: Optional[int] = None

# Schema for speaker recognition response
class SpeakerRecognitionResponse(BaseModel):
    speaker: str  # "respondent" or "enumerator" or "unknown"
    confidence: float

# Schema for transcription request
class TranscriptionRequest(BaseModel):
    audio_path: str
    speaker: str  # "respondent" or "enumerator"

# Schema for transcription response
class TranscriptionResponse(BaseModel):
    transcript: str
    language: Optional[str] = None
    confidence: Optional[float] = None

# Schema for information extraction request
class InformationExtractionRequest(BaseModel):
    transcript: str
    questions: List[str]

# Schema for information extraction response
class InformationExtractionResponse(BaseModel):
    extracted_info: Dict[str, Any]
    confidence: float

# Schema for diarization request
class DiarizationRequest(BaseModel):
    audio_path: str
    interview_id: int

# Schema for diarization response
class DiarizationResponse(BaseModel):
    segments: List[Dict[str, Any]]  # List of segments with speaker, start_time, end_time