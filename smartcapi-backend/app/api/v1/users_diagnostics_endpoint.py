"""
New endpoint for user diagnostics - add this to users.py
"""

@router.get("/diagnostics/{username}")
def get_user_diagnostics(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get comprehensive diagnostics data for a user including:
    - Voice sample registration
    - MFCC profile
    - Interview audio
    - Audio chunks
    - Respondent data
    """
    from app.db.models import VoiceProfile, Interview, Respondent, AudioChunk
    
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get voice profile
    voice_profile = db.query(VoiceProfile).filter(VoiceProfile.user_id == user.id).first()
    
    # Get interviews
    interviews = db.query(Interview).filter(Interview.enumerator_id == user.id).all()
    
    # Build response
    result = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at,
        "voice_sample_path": user.voice_sample_path,
        "voice_sample_exists": False,
        "voice_sample_size": None,
        "mfcc_profile": None,
        "interviews": []
    }
    
    # Check voice sample file
    if user.voice_sample_path:
        path = user.voice_sample_path.lstrip("/")
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            result["voice_sample_exists"] = True
            file_size = os.path.getsize(full_path)
            result["voice_sample_size"] = f"{file_size} bytes ({file_size / 1024:.2f} KB)"
    
    # Add voice profile
    if voice_profile:
        result["mfcc_profile"] = {
            "id": voice_profile.id,
            "mfcc_features_path": voice_profile.mfcc_features_path,
            "is_active": voice_profile.is_active,
            "created_at": voice_profile.created_at
        }
    
    # Add interviews
    for interview in interviews:
        interview_data = {
            "id": interview.id,
            "mode": interview.mode,
            "status": interview.status,
            "duration": interview.duration,
            "raw_audio_path": interview.raw_audio_path,
            "audio_exists": False,
            "audio_size": None,
            "created_at": interview.created_at,
            "respondent": None,
            "audio_chunks": []
        }
        
        # Check audio file
        if interview.raw_audio_path:
            path = interview.raw_audio_path.lstrip("/")
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                interview_data["audio_exists"] = True
                file_size = os.path.getsize(full_path)
                interview_data["audio_size"] = f"{file_size} bytes ({file_size / 1024:.2f} KB)"
        
        # Add respondent data
        if interview.respondent:
            interview_data["respondent"] = {
                "id": interview.respondent.id,
                "full_name": interview.respondent.full_name,
                "birth_year": interview.respondent.birth_year,
                "education": interview.respondent.education,
                "address": interview.respondent.address
            }
        
        # Add audio chunks
        audio_chunks = db.query(AudioChunk).filter(AudioChunk.interview_id == interview.id).all()
        for chunk in audio_chunks:
            interview_data["audio_chunks"].append({
                "id": chunk.id,
                "chunk_order": chunk.chunk_order,
                "file_path": chunk.file_path,
                "speaker_label": chunk.speaker_label,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time
            })
        
        result["interviews"].append(interview_data)
    
    return result
