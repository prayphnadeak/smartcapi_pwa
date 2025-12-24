from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base schema for Transcript
class TranscriptBase(BaseModel):
    raw_transcript: Optional[str] = None
    cleaned_transcript: Optional[str] = None
    summary: Optional[str] = None

# Schema for creating a Transcript
class TranscriptCreate(TranscriptBase):
    interview_id: int

# Schema for updating a Transcript
class TranscriptUpdate(TranscriptBase):
    pass

# Schema for Transcript details
class Transcript(TranscriptBase):
    id: int
    interview_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Base schema for Question
class QuestionBase(BaseModel):
    question_number: Optional[int] = None
    variable_name: Optional[str] = None
    data_type: Optional[str] = None
    usage_reason: Optional[str] = None
    question_text: str
    is_active: bool = True

# Schema for creating a Question
class QuestionCreate(QuestionBase):
    pass

# Schema for updating a Question
class QuestionUpdate(BaseModel):
    question_number: Optional[int] = None
    variable_name: Optional[str] = None
    data_type: Optional[str] = None
    usage_reason: Optional[str] = None
    question_text: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for Question details
class Question(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Base schema for Answer
class AnswerBase(BaseModel):
    answer_text: Optional[str] = None
    transcript: Optional[str] = None
    confidence_score: Optional[float] = None

# Schema for creating an Answer
class AnswerCreate(AnswerBase):
    interview_id: int
    question_id: int

# Schema for updating an Answer
class AnswerUpdate(AnswerBase):
    pass

# Schema for Answer details
class Answer(AnswerBase):
    id: int
    interview_id: int
    question_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    question: Optional[Question] = None

    class Config:
        from_attributes = True
