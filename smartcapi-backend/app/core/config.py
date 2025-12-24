from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Base Directory (Dynamically calculated)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Storage Paths
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")
    INTERVIEW_STORAGE_DIR: str = os.path.join(BASE_DIR, "storage", "interviews")

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SmartCAPI"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'smartcapi.db')}"
    
    # OpenAI
    OPENAI_API_KEY: str = "Your Own Open AI API Key"
    
    # Model paths
    RF_MODEL_PATH: str = os.path.join(BASE_DIR, "app", "processing", "models", "rf_model.pkl")
    WHISPER_MODEL_PATH: str = os.path.join(BASE_DIR, "app", "processing", "models", "whisper_medium.pt") # Unused (API)
    WHISPER_MODEL_SIZE: str = "medium"  # Unused (Using OpenAI API)

    
    # Audio processing
    SAMPLE_RATE: int = 16000
    CHUNK_DURATION: int = 5  # seconds
    SILENCE_THRESHOLD: float = 0.1  # Increased to reduce noise hallucinations (was 0.05)
    MIN_SILENCE_DURATION: float = 1.0  # Minimum silence duration in seconds
    
    # Real-time extraction settings
    SILENCE_MIN_DURATION: float = 1.5  # Silence window for auto-extraction (1-2 seconds)
    AUTO_EXTRACTION_ENABLED: bool = True  # Enable automatic extraction after silence
    CHUNK_BUFFER_SIZE: int = 50  # Maximum audio chunks to buffer per question
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # File storage
    UPLOAD_DIR: str = "./app/storage/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Email settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Password reset
    RESET_TOKEN_EXPIRE_HOURS: int = 1
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()