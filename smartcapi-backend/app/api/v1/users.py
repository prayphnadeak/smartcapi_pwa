from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os
import shutil
import io
import csv
import numpy as np
import librosa

from app.api import deps
from app.db.database import get_db
from app.db.models import User, UserRole
from app.schemas.user import User as UserSchema, UserUpdate
from app.services.file_service import save_upload_file, generate_unique_filename
from app.processing.audio.feature_extractor import extract_33_mfcc_means, extract_mfcc_features
from app.services.diarization_service import speaker_service
from app.db.models import User, Interview, AudioChunk

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users. Admin sees all, regular user sees self.
    """
    if current_user.role != UserRole.ADMIN:
        count = db.query(Interview).filter(Interview.enumerator_id == current_user.id).count()
        current_user.interview_count = count
        return [current_user]
        
    users = db.query(User).offset(skip).limit(limit).all()
    for user in users:
        count = db.query(Interview).filter(Interview.enumerator_id == user.id).count()
        user.interview_count = count
        
    return users

@router.post("/me/voice-sample", response_model=UserSchema)
async def upload_voice_sample(
    *,
    db: Session = Depends(get_db),
    voice_file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Upload voice sample for current user and trigger model training.
    """
    # Create directory if not exists
    upload_dir = os.path.join("storage", "voice_samples", str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    filename = generate_unique_filename(voice_file.filename)
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    if not save_upload_file(voice_file, file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save voice file"
        )
    
    # Update user
    # Store path with forward slashes for URL compatibility
    relative_path = os.path.join("storage", "voice_samples", str(current_user.id), filename)
    current_user.voice_sample_path = relative_path.replace("\\", "/")
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    # Trigger training in background
    from app.services.diarization_service import speaker_service
    from app.core.training_state import update_training_status
    
    def train_task(user_id: int, file_path: str, speaker_label: str):
        def progress_callback(progress, status, message):
            update_training_status(user_id, progress, status, message)
            
        update_training_status(user_id, 0, "starting", "Starting training process...")
        speaker_service.add_voice_sample(file_path, speaker_label, progress_callback)
    
    # Assuming the user is an enumerator, but we can use role or just "user_{id}"
    speaker_label = f"user_{current_user.id}"
    background_tasks.add_task(train_task, current_user.id, file_path, speaker_label)
    
    return current_user

@router.get("/{user_id}/export-mfcc")
def export_user_mfcc(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export MFCC features for a user's voice sample.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.voice_sample_path:
        raise HTTPException(status_code=404, detail="User has no voice sample")
        
    # Construct full path
    path = user.voice_sample_path.lstrip("/")
    full_path = os.path.abspath(path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Voice sample file not found on server")
        
    try:
        # Load audio
        y, sr = librosa.load(full_path, sr=None)
        
        # Split into 5s chunks
        chunk_duration = 5 # seconds
        samples_per_chunk = chunk_duration * sr
        total_samples = len(y)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = ["Label", "Record Name"] + [f"MFCC_{i+1}" for i in range(33)]
        writer.writerow(header)
        
        num_chunks = int(np.ceil(total_samples / samples_per_chunk))
        
        for i in range(num_chunks):
            start = i * samples_per_chunk
            end = min((i + 1) * samples_per_chunk, total_samples)
            
            if end - start < sr: # Skip if less than 1 second
                continue
                
            chunk = y[start:end]
            
            # Extract MFCC
            mfccs = extract_33_mfcc_means(chunk, sr)
            
            if len(mfccs) == 33:
                row = ["Enumerator", f"{user.username}_{i+1}"] + mfccs.tolist()
                writer.writerow(row)
                
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=mfcc_export_{user.username}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@router.get("/{user_id}/export-interviews-mfcc")
def export_user_interviews_mfcc(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export MFCC features for all interviews conducted by a user.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    interviews = db.query(Interview).filter(Interview.enumerator_id == user_id).all()
    
    if not interviews:
        raise HTTPException(status_code=404, detail="No interviews found for this user")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ["Interview ID", "Label", "Record Name"] + [f"MFCC_{i+1}" for i in range(33)]
    writer.writerow(header)
    
    for interview in interviews:
        if not interview.raw_audio_path:
            continue
            
        path = interview.raw_audio_path.lstrip("/")
        full_path = os.path.abspath(path)
        
        if not os.path.exists(full_path):
            continue
            
        try:
            # Load audio
            y, sr = librosa.load(full_path, sr=None)
            
            # Split into 5s chunks
            chunk_duration = 5 # seconds
            samples_per_chunk = chunk_duration * sr
            total_samples = len(y)
            
            num_chunks = int(np.ceil(total_samples / samples_per_chunk))
            
            respondent_name = interview.respondent.full_name if interview.respondent else "Respondent"
            enumerator_username = user.username
            
            for i in range(num_chunks):
                start = i * samples_per_chunk
                end = min((i + 1) * samples_per_chunk, total_samples)
                
                if end - start < sr: # Skip if less than 1 second
                    continue
                    
                chunk = y[start:end]
                
                # Extract 33 MFCC means for CSV
                mfccs_33 = extract_33_mfcc_means(chunk, sr)
                
                # Extract features for prediction (198 features)
                features_for_pred = extract_mfcc_features(chunk, sr).flatten()
                
                # Predict speaker
                label = "Unknown"
                if len(features_for_pred) > 0:
                    features_reshaped = features_for_pred.reshape(1, -1)
                    try:
                        if speaker_service.model:
                            prediction = speaker_service.model.predict(features_reshaped)[0]
                            
                            expected_enumerator_label = f"user_{user.id}"
                            
                            if prediction == expected_enumerator_label or prediction == "enumerator":
                                label = "Enumerator"
                                record_name = f"{enumerator_username}_{i+1}"
                            else:
                                label = "Responden"
                                record_name = f"{respondent_name}_{i+1}"
                        else:
                            # No model loaded, default to Respondent or Unknown
                            label = "Responden"
                            record_name = f"{respondent_name}_{i+1}"
                            
                    except Exception as e:
                        label = "Responden" # Default to respondent
                        record_name = f"{respondent_name}_{i+1}"
                else:
                    label = "Responden"
                    record_name = f"{respondent_name}_{i+1}"
                
                if len(mfccs_33) == 33:
                    row = [interview.id, label, record_name] + mfccs_33.tolist()
                    writer.writerow(row)
                    
        except Exception as e:
            # Log error but continue with other interviews
            print(f"Error processing interview {interview.id}: {e}")
            continue

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mfcc_export_interviews_{user.username}.csv"}
    )

@router.delete("/{user_id}", response_model=UserSchema)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a user. Only admin can access this.
    This will also delete all related records (interviews, voice profiles, etc.)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # Import models needed for deletion
    from app.db.models import Interview, VoiceProfile, AudioChunk, ExtractedAnswer, ProcessingLog, InterviewTranscript
    
    # Delete related records in the correct order (respecting foreign key constraints)
    # 1. Delete extracted answers for user's interviews
    user_interviews = db.query(Interview).filter(Interview.enumerator_id == user_id).all()
    for interview in user_interviews:
        db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == interview.id).delete()
        db.query(ProcessingLog).filter(ProcessingLog.interview_id == interview.id).delete()
        db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == interview.id).delete()
        db.query(AudioChunk).filter(AudioChunk.interview_id == interview.id).delete()
    
    # 2. Delete interviews
    db.query(Interview).filter(Interview.enumerator_id == user_id).delete()
    
    # 3. Delete voice profiles
    db.query(VoiceProfile).filter(VoiceProfile.user_id == user_id).delete()
    
    # Delete user's voice samples directory
    voice_sample_dir = os.path.join("storage", "voice_samples", str(user_id))
    if os.path.exists(voice_sample_dir):
        shutil.rmtree(voice_sample_dir)

    # Finally, delete the user
    db.delete(user)
    db.commit()
    return user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user. Only admin can access this.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    update_data = user_in.dict(exclude_unset=True)
    
    # Handle password update separately if needed
    if "password" in update_data and update_data["password"]:
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        user.hashed_password = hashed_password
        
    for field, value in update_data.items():
        setattr(user, field, value)
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user == current_user:
        return user
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return user

@router.delete("/{user_id}", response_model=UserSchema)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a user. Only admin can access this.
    This will also delete all related records (interviews, voice profiles, etc.)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # Import models needed for deletion
    from app.db.models import Interview, VoiceProfile, AudioChunk, ExtractedAnswer, ProcessingLog, InterviewTranscript
    
    # Delete related records in the correct order (respecting foreign key constraints)
    # 1. Delete extracted answers for user's interviews
    user_interviews = db.query(Interview).filter(Interview.enumerator_id == user_id).all()
    for interview in user_interviews:
        db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == interview.id).delete()
        db.query(ProcessingLog).filter(ProcessingLog.interview_id == interview.id).delete()
        db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == interview.id).delete()
        db.query(AudioChunk).filter(AudioChunk.interview_id == interview.id).delete()
    
    # 2. Delete interviews
    db.query(Interview).filter(Interview.enumerator_id == user_id).delete()
    
    # 3. Delete voice profiles
    db.query(VoiceProfile).filter(VoiceProfile.user_id == user_id).delete()
    
    # Delete user's voice samples directory
    voice_sample_dir = os.path.join("storage", "voice_samples", str(user_id))
    if os.path.exists(voice_sample_dir):
        shutil.rmtree(voice_sample_dir)

    # Finally, delete the user
    db.delete(user)
    db.commit()
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a user. Only admin can access this.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    update_data = user_in.dict(exclude_unset=True)
    
    # Handle password update separately if needed
    if "password" in update_data and update_data["password"]:
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        user.hashed_password = hashed_password
        
    for field, value in update_data.items():
        setattr(user, field, value)
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def export_user_mfcc(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export MFCC features for a user's voice sample.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.voice_sample_path:
        raise HTTPException(status_code=404, detail="User has no voice sample")
        
    # Construct full path
    # Assuming voice_sample_path is relative to root (e.g. storage/...)
    # If it starts with /, remove it
    path = user.voice_sample_path.lstrip("/")
    full_path = os.path.abspath(path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Voice sample file not found on server")
        
    try:
        # Load audio
        y, sr = librosa.load(full_path, sr=None)
        
        # Split into 5s chunks
        chunk_duration = 5 # seconds
        samples_per_chunk = chunk_duration * sr
        total_samples = len(y)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = ["Label", "Record Name"] + [f"MFCC_{i+1}" for i in range(33)]
        writer.writerow(header)
        
        num_chunks = int(np.ceil(total_samples / samples_per_chunk))
        
        for i in range(num_chunks):
            start = i * samples_per_chunk
            end = min((i + 1) * samples_per_chunk, total_samples)
            
            # Skip short chunks (e.g. < 1s) if desired, but user didn't specify.
            # Let's keep all chunks that have some data.
            if end - start < sr: # Skip if less than 1 second
                continue
                
            chunk = y[start:end]
            
            # Extract MFCC
            mfccs = extract_33_mfcc_means(chunk, sr)
            
            if len(mfccs) == 33:
                row = ["Enumerator", f"{user.username}_{i+1}"] + mfccs.tolist()
                writer.writerow(row)
                
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=mfcc_export_{user.username}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@router.get("/{user_id}/export-interviews-mfcc")
def export_user_interviews_mfcc(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export MFCC features for all interviews conducted by a user.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    interviews = db.query(Interview).filter(Interview.enumerator_id == user_id).all()
    
    if not interviews:
        raise HTTPException(status_code=404, detail="No interviews found for this user")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ["Interview ID", "Label", "Record Name"] + [f"MFCC_{i+1}" for i in range(33)]
    writer.writerow(header)
    
    for interview in interviews:
        if not interview.raw_audio_path:
            continue
            
        path = interview.raw_audio_path.lstrip("/")
        full_path = os.path.abspath(path)
        
        if not os.path.exists(full_path):
            continue
            
        try:
            # Load audio
            y, sr = librosa.load(full_path, sr=None)
            
            # Split into 5s chunks
            chunk_duration = 5 # seconds
            samples_per_chunk = chunk_duration * sr
            total_samples = len(y)
            
            num_chunks = int(np.ceil(total_samples / samples_per_chunk))
            
            respondent_name = interview.respondent.full_name if interview.respondent else "Respondent"
            enumerator_username = user.username
            
            for i in range(num_chunks):
                start = i * samples_per_chunk
                end = min((i + 1) * samples_per_chunk, total_samples)
                
                if end - start < sr: # Skip if less than 1 second
                    continue
                    
                chunk = y[start:end]
                
                # Extract 33 MFCC means for CSV
                mfccs_33 = extract_33_mfcc_means(chunk, sr)
                
                # Extract features for prediction (198 features)
                features_for_pred = extract_mfcc_features(chunk, sr).flatten()
                
                # Predict speaker
                label = "Unknown"
                if len(features_for_pred) > 0:
                    features_reshaped = features_for_pred.reshape(1, -1)
                    try:
                        if speaker_service.model:
                            prediction = speaker_service.model.predict(features_reshaped)[0]
                            
                            expected_enumerator_label = f"user_{user.id}"
                            
                            if prediction == expected_enumerator_label or prediction == "enumerator":
                                label = "Enumerator"
                                record_name = f"{enumerator_username}_{i+1}"
                            else:
                                label = "Responden"
                                record_name = f"{respondent_name}_{i+1}"
                        else:
                            # No model loaded, default to Respondent or Unknown
                            label = "Responden"
                            record_name = f"{respondent_name}_{i+1}"
                            
                    except Exception as e:
                        # api_logger.warning(f"Prediction failed for chunk {i}: {e}")
                        label = "Responden" # Default to respondent
                        record_name = f"{respondent_name}_{i+1}"
                else:
                    label = "Responden"
                    record_name = f"{respondent_name}_{i+1}"
                
                if len(mfccs_33) == 33:
                    row = [interview.id, label, record_name] + mfccs_33.tolist()
                    writer.writerow(row)
                    
        except Exception as e:
            # Log error but continue with other interviews
            print(f"Error processing interview {interview.id}: {e}")
            continue

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mfcc_export_interviews_{user.username}.csv"}
    )
