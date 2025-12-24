from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.db.models import ModelType

# Base schema for ML Model
class MLModelBase(BaseModel):
    name: str
    version: str
    model_type: ModelType
    file_path: str
    metrics: Optional[str] = None  # JSON string
    parameters: Optional[str] = None  # JSON string
    is_active: bool = True

# Schema for creating an ML Model
class MLModelCreate(MLModelBase):
    pass

# Schema for updating an ML Model
class MLModelUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    model_type: Optional[ModelType] = None
    file_path: Optional[str] = None
    metrics: Optional[str] = None
    parameters: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for ML Model details
class MLModel(MLModelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
