import os
import tempfile
import pickle
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.db.models import User, VoiceProfile
from app.services.file_service import save_upload_file, generate_unique_filename
from app.services.diarization_service import speaker_service
from app.core.logger import api_logger
from app.core.config import settings

router = APIRouter()

@router.post("/add-voice-sample")
def add_voice_sample(
    *,
    db: Session = Depends(get_db),
    audio_file: UploadFile = File(...),
    speaker_label: str = Form(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add a voice sample for training the speaker recognition model
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            save_upload_file(audio_file, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Add voice sample to training data
        success = speaker_service.add_voice_sample(tmp_path, speaker_label)
        
        # Clean up temporary file
        os.remove(tmp_path)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to add voice sample"
            )
        
        # Create voice profile record if it doesn't exist
        voice_profile = db.query(VoiceProfile).filter(
            VoiceProfile.user_id == current_user.id
        ).first()
        
        if not voice_profile:
            voice_profile = VoiceProfile(
                user_id=current_user.id,
                mfcc_features_path=f"voice_features_{current_user.id}.pkl"
            )
            db.add(voice_profile)
            db.commit()
        
        return {"message": "Voice sample added successfully"}
    except Exception as e:
        api_logger.error(f"Error adding voice sample: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add voice sample: {str(e)}"
        )

@router.post("/train-speaker-model")
def train_speaker_model(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Train the speaker recognition model with collected voice samples
    """
    try:
        # Load training data
        training_data_path = os.path.join(
            os.path.dirname(settings.RF_MODEL_PATH), "training_data.pkl"
        )
        
        if not os.path.exists(training_data_path):
            raise HTTPException(
                status_code=404,
                detail="No training data found. Add voice samples first."
            )
        
        with open(training_data_path, 'rb') as f:
            training_data = pickle.load(f)
        
        features = training_data['features']
        labels = training_data['labels']
        
        # Train model
        success = speaker_service.train_model(features, labels)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to train speaker model"
            )
        
        return {"message": "Speaker model trained successfully"}
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error training speaker model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to train speaker model: {str(e)}"
        )

@router.get("/progress")
def get_training_progress(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get training progress for current user.
    """
    from app.core.training_state import get_training_status
    return get_training_status(current_user.id)