import os
import tempfile
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.db.models import User
from app.schemas.inference import (
    SpeakerRecognitionRequest,
    SpeakerRecognitionResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    InformationExtractionRequest,
    InformationExtractionResponse,
)
from app.services.file_service import save_upload_file, generate_unique_filename
from app.services.whisper_service import whisper_service
from app.services.diarization_service import speaker_service
from app.services.llm_service import llm_service
from app.core.logger import api_logger

router = APIRouter()

@router.post("/speaker-recognition", response_model=SpeakerRecognitionResponse)
def recognize_speaker(
    *,
    db: Session = Depends(get_db),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Recognize speaker from audio file
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            save_upload_file(audio_file, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Recognize speaker
        speaker, confidence = speaker_service.predict_speaker(tmp_path)
        
        # Clean up temporary file
        os.remove(tmp_path)
        
        return SpeakerRecognitionResponse(
            speaker=speaker,
            confidence=confidence
        )
    except Exception as e:
        api_logger.error(f"Error recognizing speaker: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to recognize speaker: {str(e)}"
        )

@router.post("/transcription", response_model=TranscriptionResponse)
def transcribe_audio(
    *,
    db: Session = Depends(get_db),
    audio_file: UploadFile = File(...),
    speaker: str = Form(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Transcribe audio file using Whisper
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            save_upload_file(audio_file, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Transcribe audio
        result = whisper_service.transcribe(tmp_path)
        transcript = result.get("text", "")
        language = result.get("language", "id")
        
        # Clean up temporary file
        os.remove(tmp_path)
        
        return TranscriptionResponse(
            transcript=transcript,
            language=language
        )
    except Exception as e:
        api_logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to transcribe audio: {str(e)}"
        )

@router.post("/extract-information", response_model=InformationExtractionResponse)
def extract_information(
    *,
    db: Session = Depends(get_db),
    request: InformationExtractionRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Extract information from transcript using LLM
    """
    try:
        # Extract information using LLM
        extracted_info = llm_service.extract_information(request.transcript)
        
        return InformationExtractionResponse(
            extracted_info=extracted_info,
            confidence=0.8  # Placeholder confidence score
        )
    except Exception as e:
        api_logger.error(f"Error extracting information: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract information: {str(e)}"
        )