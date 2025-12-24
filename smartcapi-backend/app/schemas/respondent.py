from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base schema for Respondent
class RespondentBase(BaseModel):
    full_name: Optional[str] = None
    birth_year: Optional[int] = None
    education: Optional[str] = None
    address: Optional[str] = None

# Schema for creating a Respondent
class RespondentCreate(RespondentBase):
    full_name: str  # Required for creation

# Schema for updating a Respondent
class RespondentUpdate(RespondentBase):
    pass

# Schema for Respondent details
class Respondent(RespondentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
