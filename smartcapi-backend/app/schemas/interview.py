from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models import InterviewMode, SyncStatus, InterviewStatus, SpeakerLabel
from app.schemas.respondent import Respondent, RespondentCreate
from app.schemas.questionnaire import Answer

# Interview Schemas
# Base schema for Interview
class InterviewBase(BaseModel):
    mode: InterviewMode
    respondent_id: Optional[int] = None

# Schema for creating an Interview
class InterviewCreate(InterviewBase):
    # Allow creating respondent inline or passing ID
    respondent_data: Optional[RespondentCreate] = None
    duration: Optional[int] = None
    # extracted_data is removed from model but might still be passed from frontend
    # We will handle it by saving to ExtractedAnswer or ignoring for now
    extracted_data: Optional[Dict[str, Any]] = None 

# Schema for updating an Interview
class InterviewUpdate(BaseModel):
    mode: Optional[InterviewMode] = None
    duration: Optional[int] = None
    status: Optional[InterviewStatus] = None
    sync_status: Optional[SyncStatus] = None
    extracted_data: Optional[Dict[str, Any]] = None

# Schema for Interview details
class Interview(InterviewBase):
    id: int
    enumerator_id: int
    duration: Optional[int] = None
    raw_audio_path: Optional[str] = None
    status: InterviewStatus
    sync_status: SyncStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    respondent: Optional[Respondent] = None
    extracted_answers: List[Answer] = []
    
    class Config:
        from_attributes = True

# Audio Chunk Schemas
# Base schema for Audio Chunk
class AudioChunkBase(BaseModel):
    chunk_order: int
    speaker_label: Optional[SpeakerLabel] = None
    transcript: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

# Schema for creating an Audio Chunk
class AudioChunkCreate(AudioChunkBase):
    interview_id: int

# Schema for Audio Chunk details
class AudioChunk(AudioChunkBase):
    id: int
    interview_id: int
    file_path: str
    speaker_confidence: Optional[float] = None
    transcript_confidence: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Summary Schema
# Schema for Interview summary
class InterviewSummary(BaseModel):
    id: int
    respondent_name: Optional[str] = None # Derived from respondent relationship
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models import InterviewMode, SyncStatus, InterviewStatus, SpeakerLabel
from app.schemas.respondent import Respondent, RespondentCreate
from app.schemas.questionnaire import Answer

# Interview Schemas
class InterviewBase(BaseModel):
    mode: InterviewMode
    respondent_id: Optional[int] = None

class InterviewCreate(InterviewBase):
    # Allow creating respondent inline or passing ID
    respondent_data: Optional[RespondentCreate] = None
    duration: Optional[int] = None
    # extracted_data is removed from model but might still be passed from frontend
    # We will handle it by saving to ExtractedAnswer or ignoring for now
    extracted_data: Optional[Dict[str, Any]] = None 

class InterviewUpdate(BaseModel):
    mode: Optional[InterviewMode] = None
    duration: Optional[int] = None
    status: Optional[InterviewStatus] = None
    sync_status: Optional[SyncStatus] = None
    extracted_data: Optional[Dict[str, Any]] = None
    respondent_data: Optional[RespondentCreate] = None

class Interview(InterviewBase):
    id: int
    enumerator_id: int
    duration: Optional[int] = None
    raw_audio_path: Optional[str] = None
    status: InterviewStatus
    sync_status: SyncStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    respondent: Optional[Respondent] = None
    extracted_answers: List[Answer] = []
    
    class Config:
        from_attributes = True

# Audio Chunk Schemas
class AudioChunkBase(BaseModel):
    chunk_order: int
    speaker_label: Optional[SpeakerLabel] = None
    transcript: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class AudioChunkCreate(AudioChunkBase):
    interview_id: int

class AudioChunk(AudioChunkBase):
    id: int
    interview_id: int
    file_path: str
    speaker_confidence: Optional[float] = None
    transcript_confidence: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Summary Schema
class InterviewSummary(BaseModel):
    id: int
    respondent_name: Optional[str] = None # Derived from respondent relationship
    mode: InterviewMode
    duration: Optional[int] = None
    status: InterviewStatus
    has_recording: bool
    created_at: datetime
    
    # Added fields
    respondent: Optional[Respondent] = None
    enumerator_id: Optional[int] = None
    extracted_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True