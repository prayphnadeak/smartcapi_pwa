
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.db.models import UserRole

# Base schema for User
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.ENUMERATOR
    is_active: bool = True

# Schema for creating a User
class UserCreate(UserBase):
    password: str

# Schema for updating a User
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

# Schema for User in database (base)
class UserInDBBase(UserBase):
    id: int
    voice_sample_path: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schema for User details
class User(UserInDBBase):
    interview_count: Optional[int] = 0

# Schema for User in database with password
class UserInDB(UserInDBBase):
    hashed_password: str