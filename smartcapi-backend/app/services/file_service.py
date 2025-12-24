import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings
from app.core.logger import api_logger

# Function to ensure directory exists
def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure that a directory exists, create if it doesn't"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        api_logger.error(f"Error creating directory {directory_path}: {str(e)}")
        return False

# Function to save uploaded file
def save_upload_file(upload_file: UploadFile, destination: str) -> bool:
    """Save an uploaded file to the specified destination"""
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return True
    except Exception as e:
        api_logger.error(f"Error saving file to {destination}: {str(e)}")
        return False

# Function to generate unique filename
def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the original extension"""
    file_extension = os.path.splitext(original_filename)[1]
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"

# Function to get file size
def get_file_size(file_path: str) -> Optional[int]:
    """Get the size of a file in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        api_logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return None

# Function to delete file
def delete_file(file_path: str) -> bool:
    """Delete a file from the filesystem"""
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        api_logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False

# Function to get audio storage path
def get_audio_storage_path(interview_id: int, filename: str) -> str:
    """Get the storage path for an audio file"""
    audio_dir = os.path.join(settings.UPLOAD_DIR, "audio", str(interview_id))
    ensure_directory_exists(audio_dir)
    return os.path.join(audio_dir, filename)

# Function to get voice sample storage path
def get_voice_sample_storage_path(user_id: int, filename: str) -> str:
    """Get the storage path for a voice sample file"""
    voice_dir = os.path.join(settings.UPLOAD_DIR, "voices", str(user_id))
    ensure_directory_exists(voice_dir)
    return os.path.join(voice_dir, filename)