from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENUMERATOR = "enumerator"

class InterviewMode(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"

class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"

class InterviewStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ModelType(str, enum.Enum):
    RF = "rf"
    WHISPER = "whisper"
    LLM = "llm"

class SpeakerLabel(str, enum.Enum):
    RESPONDENT = "respondent"
    ENUMERATOR = "enumerator"
    UNKNOWN = "unknown"

class LogType(str, enum.Enum):
    SYSTEM = "system"
    AUDIO_PROCESSING = "audio_processing"
    WHISPER = "whisper"
    RF = "rf"
    LLM = "llm"
    SYNC = "sync"
    ROLE_CONFLICT = "role_conflict"

class RoleEventType(str, enum.Enum):
    ROLE_CONFLICT = "role_conflict"
    ROLE_AMBIGUITY = "role_ambiguity"

class RoleActionTaken(str, enum.Enum):
    LOG_ONLY = "log_only"
    SKIP_TRANSCRIPTION = "skip_transcription"
    ALLOW = "allow"

# Models

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.ENUMERATOR)
    is_active = Column(Boolean, default=True)
    voice_sample_path = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Respondent(Base):
    __tablename__ = "respondents"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    birth_year = Column(Integer)
    education = Column(String(100))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    interviews = relationship("Interview", back_populates="respondent")

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    file_path = Column(String(255), nullable=False)
    metrics = Column(Text)
    parameters = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    enumerator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    respondent_id = Column(Integer, ForeignKey("respondents.id"))
    mode = Column(Enum(InterviewMode), nullable=False)
    duration = Column(Integer)
    raw_audio_path = Column(String(255))
    
    rf_model_id = Column(Integer, ForeignKey("ml_models.id"))
    whisper_model_id = Column(Integer, ForeignKey("ml_models.id"))
    llm_model_id = Column(Integer, ForeignKey("ml_models.id"))
    
    status = Column(Enum(InterviewStatus), default=InterviewStatus.ACTIVE)
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    respondent = relationship("Respondent", back_populates="interviews")
    
    audio_chunks = relationship("AudioChunk", back_populates="interview")
    transcript = relationship("InterviewTranscript", back_populates="interview", uselist=False)
    extracted_answers = relationship("ExtractedAnswer", back_populates="interview")
    logs = relationship("ProcessingLog", back_populates="interview")

class AudioChunk(Base):
    __tablename__ = "audio_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    chunk_order = Column(Integer, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    file_path = Column(String(255), nullable=False)
    speaker_label = Column(Enum(SpeakerLabel))
    speaker_confidence = Column(Float)
    transcript = Column(Text)
    transcript_confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="audio_chunks")

class InterviewTranscript(Base):
    __tablename__ = "interview_transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    raw_transcript = Column(Text)
    cleaned_transcript = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    interview = relationship("Interview", back_populates="transcript")

class QuestionnaireQuestion(Base):
    __tablename__ = "questionnaire_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_number = Column(Integer)
    variable_name = Column(String(100))
    data_type = Column(String(50))
    usage_reason = Column(Text)
    question_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExtractedAnswer(Base):
    __tablename__ = "extracted_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questionnaire_questions.id"), nullable=False)
    answer_text = Column(Text)
    transcript = Column(Text)
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    interview = relationship("Interview", back_populates="extracted_answers")
    question = relationship("QuestionnaireQuestion")

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mfcc_features_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    log_type = Column(Enum(LogType))
    message = Column(Text)
    log_metadata = Column(Text) # JSON, renamed from metadata to avoid conflict
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview", back_populates="logs")

class RoleEventLog(Base):
    __tablename__ = "role_event_logs"
    
    event_id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    segment_id = Column(Integer, nullable=True) # Optional link to AudioChunk
    
    expected_role = Column(String(50)) # e.g. "RESPONDENT"
    detected_speaker_id = Column(String(50)) # e.g. "user_3"
    detected_role = Column(String(50)) # e.g. "ENUMERATOR"
    
    confidence = Column(Float)
    event_type = Column(Enum(RoleEventType))
    action_taken = Column(Enum(RoleActionTaken))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview = relationship("Interview")