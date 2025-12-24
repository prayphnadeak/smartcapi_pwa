import os
import json
import tempfile
from typing import Any, List, Dict
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
import io
import csv
import numpy as np
import librosa
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.db.models import User, Interview, AudioChunk, Respondent, InterviewStatus, ExtractedAnswer, QuestionnaireQuestion, InterviewTranscript, ProcessingLog, UserRole
from app.schemas.interview import (
    Interview as InterviewSchema,
    InterviewCreate,
    InterviewUpdate,
    InterviewSummary,
    AudioChunk as AudioChunkSchema,
)
from app.services.file_service import (
    save_upload_file,
    generate_unique_filename,
    get_audio_storage_path,
    get_file_size,
)
from app.services.whisper_service import whisper_service
from app.services.diarization_service import diarization_service
from app.services.llm_service import llm_service
from app.processing.audio.audio_utils import load_audio, save_audio
from app.processing.audio.feature_extractor import extract_33_mfcc_means, extract_mfcc_features
from app.services.diarization_service import speaker_service
from app.core.logger import api_logger
from app.core.redis_client import redis_client, RedisQueue

router = APIRouter()

@router.get("/", response_model=List[InterviewSummary])
def get_interviews(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve interviews for the current user (or all for admin)
    """
    if current_user.role == "admin":
        interviews = db.query(Interview).offset(skip).limit(limit).all()
    else:
        interviews = db.query(Interview).filter(
            Interview.enumerator_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    result = []
    for interview in interviews:
        has_recording = bool(interview.raw_audio_path) or db.query(AudioChunk).filter(
            AudioChunk.interview_id == interview.id
        ).count() > 0
        
        respondent_name = interview.respondent.full_name if interview.respondent else "Unknown"
        api_logger.info(f"Summary for Interview {interview.id}: Mode={interview.mode}, RespID={interview.respondent_id}, RespName='{respondent_name}'")

        # Fetch extracted answers
        extracted_answers = db.query(ExtractedAnswer).filter(
            ExtractedAnswer.interview_id == interview.id
        ).all()
        
        extracted_data = {}
        for answer in extracted_answers:
            if answer.question and answer.question.variable_name:
                extracted_data[answer.question.variable_name] = answer.answer_text

        # Fallback/Override: If extracted 'nama' exists and is not empty, prefer it over "New Respondent"
        # Check multiple possible keys for robustness
        name_keys = ["nama", "Nama", "nama_lengkap", "Nama Lengkap", "name", "Name"]
        ext_name = None
        
        for key in name_keys:
             val = extracted_data.get(key)
             if val and str(val).strip().lower() not in ["none", "null", "", "-"]:
                 ext_name = val
                 break
                 
        if ext_name:
             # Logic: if respondent_name is generic, use extracted.
             if respondent_name in ["New Respondent", "Unknown", "Responden Baru"]:
                 respondent_name = str(ext_name)

        result.append(InterviewSummary(
            id=interview.id,
            respondent_name=respondent_name,
            mode=interview.mode,
            duration=interview.duration,
            status=interview.status,
            has_recording=has_recording,
            created_at=interview.created_at,
            respondent=interview.respondent,
            enumerator_id=interview.enumerator_id,
            extracted_data=extracted_data
        ))
    
    return result

@router.post("/", response_model=InterviewSchema)
def create_interview(
    *,
    db: Session = Depends(get_db),
    interview_in: InterviewCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new interview
    """
    # Flush Redis Queues to prevent stale data from previous sessions
    # redis_client.delete block removed to prevent clearing queues for other active interviews
    pass

    # Handle Respondent creation or linking
    respondent_id = interview_in.respondent_id
    
    if not respondent_id and interview_in.respondent_data:
        # Create new respondent
        respondent = Respondent(
            full_name=interview_in.respondent_data.full_name,
            birth_year=interview_in.respondent_data.birth_year,
            education=interview_in.respondent_data.education,
            address=interview_in.respondent_data.address
        )
        db.add(respondent)
        db.commit()
        db.refresh(respondent)
        respondent_id = respondent.id
    
    interview = Interview(
        enumerator_id=current_user.id,
        respondent_id=respondent_id,
        mode=interview_in.mode,
        duration=interview_in.duration,
        status=InterviewStatus.ACTIVE
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Save extracted_data if present
    if interview_in.extracted_data:
        for key, value in interview_in.extracted_data.items():
            # Find question by variable_name
            question = db.query(QuestionnaireQuestion).filter(QuestionnaireQuestion.variable_name == key).first()
            if question:
                ans_text = str(value)
                transcript_text = None
                
                # Check for rich object {answer: ..., transcript: ...}
                if isinstance(value, dict):
                     ans_text = str(value.get('answer_text', value.get('answer', '')))
                     transcript_text = value.get('transcript')
                
                answer = ExtractedAnswer(
                    interview_id=interview.id,
                    question_id=question.id,
                    answer_text=ans_text,
                    transcript=transcript_text,
                    confidence_score=1.0
                )
                db.add(answer)
        db.commit()
        db.refresh(interview)
    
    return interview

@router.get("/{interview_id}", response_model=InterviewSchema)
def get_interview(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get interview by ID
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.enumerator_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    return interview

@router.put("/{interview_id}", response_model=InterviewSchema)
def update_interview(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    interview_in: InterviewUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an interview
    """
    # Allow Admin to update ANY interview, Enumerator only their own
    role_str = str(current_user.role).lower().split('.')[-1]
    
    if role_str == "admin" or current_user.role == UserRole.ADMIN:
        interview = db.query(Interview).filter(
            Interview.id == interview_id
        ).first()
    else:
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.enumerator_id == current_user.id
        ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or you don't have permission to edit it"
        )
    
    # Update interview fields
    # EXCLUDE respondent_data and extracted_data from generic Interview update
    update_data = interview_in.dict(exclude_unset=True, exclude={'extracted_data', 'respondent_data'})
    
    api_logger.info(f"Update Interview {interview_id}: update_data keys = {update_data.keys()}")
    
    for field, value in update_data.items():
        setattr(interview, field, value)
    
    # Update Respondent Data if provided
    if interview_in.respondent_data:
        resp_data = interview_in.respondent_data.dict(exclude_unset=True)
        api_logger.info(f"Updating Respondent Data: {resp_data}")
        
        if interview.respondent:
            for key, value in resp_data.items():
                setattr(interview.respondent, key, value)
            db.add(interview.respondent)
            api_logger.info(f"Updated existing Respondent {interview.respondent.id} details")
        else:
            # Create new respondent if missing
            from app.db.models import Respondent
            new_respondent = Respondent(
                full_name=resp_data.get("full_name", "New Respondent"),
                birth_year=resp_data.get("birth_year"),
                education=resp_data.get("education"),
                address=resp_data.get("address")
            )
            db.add(new_respondent)
            db.commit() # Commit to get ID
            db.refresh(new_respondent)
            
            interview.respondent_id = new_respondent.id
            db.add(interview)
            db.commit() # Allow relationship to re-sync
            db.refresh(interview) # Load interview.respondent
            api_logger.info(f"Created new Respondent {new_respondent.id} and linked to Interview {interview.id}. Name: {new_respondent.full_name}")
            
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Update extracted_data if present
    if interview_in.extracted_data:
        for key, value in interview_in.extracted_data.items():
            # SYNC RESPONDENT NAME
            if key == "nama" and value:
                name_val = value
                if isinstance(value, dict):
                     name_val = value.get('answer_text', value.get('answer', ''))
                     
                if interview.respondent:
                    interview.respondent.full_name = str(name_val)
                    db.add(interview.respondent)
                    api_logger.info(f"Updated Respondent Name to '{name_val}' from extracted_data 'nama' field")
                else:
                    api_logger.warning("Attempted to sync 'nama' but interview.respondent is still None!")

            question = db.query(QuestionnaireQuestion).filter(QuestionnaireQuestion.variable_name == key).first()
            
            ans_val = value
            transcript_val = None
            if isinstance(value, dict):
                 ans_val = value.get('answer_text', value.get('answer', ''))
                 transcript_val = value.get('transcript')

            if question:
                # Check if answer exists
                answer = db.query(ExtractedAnswer).filter(
                    ExtractedAnswer.interview_id == interview.id,
                    ExtractedAnswer.question_id == question.id
                ).first()
                
                if answer:
                    answer.answer_text = str(ans_val)
                    if transcript_val:
                         answer.transcript = transcript_val
                    answer.confidence_score = 1.0
                else:
                    answer = ExtractedAnswer(
                        interview_id=interview.id,
                        question_id=question.id,
                        answer_text=str(ans_val),
                        transcript=transcript_val,
                        confidence_score=1.0
                    )
                    db.add(answer)
        db.commit()
        db.refresh(interview)
    
    return interview

@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete an interview
    """
    # Allow Admin to delete ANY interview, Enumerator only their own
    # Use string comparison for robustness regarding Enum handling
    # Check both "admin" string and Enum match
    role_str = str(current_user.role).lower().split('.')[-1] # Handle "UserRole.ADMIN" -> "admin"
    if role_str == "admin" or current_user.role == UserRole.ADMIN:
        interview = db.query(Interview).filter(
            Interview.id == interview_id
        ).first()
    else:
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.enumerator_id == current_user.id
        ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    try:
        # Manually delete related records to avoid foreign key constraint errors
        # (Cascade delete is not configured in DB models)
        from app.db.models import RoleEventLog  # Import here to avoid circular import
        
        db.query(AudioChunk).filter(AudioChunk.interview_id == interview.id).delete(synchronize_session=False)
        db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == interview.id).delete(synchronize_session=False)
        db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == interview.id).delete(synchronize_session=False)
        db.query(ProcessingLog).filter(ProcessingLog.interview_id == interview.id).delete(synchronize_session=False)
        db.query(RoleEventLog).filter(RoleEventLog.interview_id == interview.id).delete(synchronize_session=False)  # NEW
        
        db.delete(interview)
        db.commit()
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        api_logger.error(f"Error deleting interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete interview: {str(e)}"
        )

@router.post("/{interview_id}/upload-audio")
async def upload_audio(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload audio file for an interview
    """
    # Check if interview exists and belongs to current user
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.enumerator_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Generate unique filename
    filename = generate_unique_filename(audio_file.filename)
    file_path = get_audio_storage_path(interview_id, filename)
    
    # Save file
    if not save_upload_file(audio_file, file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save audio file"
        )
    
    # Update interview with audio path
    interview.raw_audio_path = file_path
    db.commit()
    
    return {"message": "Audio uploaded successfully", "file_path": file_path}

@router.post("/{interview_id}/process-audio")
async def process_audio(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Process audio file for an interview (transcription and information extraction)
    """
    # Check if interview exists and belongs to current user
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.enumerator_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Logic to handle streamed audio file if raw_audio_path is missing
    streamed_file_path = os.path.join(settings.INTERVIEW_STORAGE_DIR, f"{interview_id}.wav")
    if not interview.raw_audio_path and os.path.exists(streamed_file_path):
        interview.raw_audio_path = streamed_file_path
        db.commit()
        
    if not interview.raw_audio_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file found for this interview"
        )
        
    # Check if the audio file works, if not, it might be raw PCM from WebSocket
    if interview.raw_audio_path and os.path.exists(interview.raw_audio_path):
        import wave
        try:
            with wave.open(interview.raw_audio_path, 'rb') as f:
                pass # It's a valid WAV
        except wave.Error:
            # Likely raw PCM data saving as .wav (headerless)
            # We need to convert it to valid WAV
            api_logger.info(f"Detected invalid WAV (likely raw PCM). Fixing header for {interview.raw_audio_path}")
            try:
                # Read raw data
                with open(interview.raw_audio_path, 'rb') as pcm_file:
                    raw_data = pcm_file.read()
                
                # Write back with valid header
                # Create a temporary path or overwrite? Overwriting is risky if it fails mid-way but simpler for path consistency.
                # Let's write to temp then rename.
                fixed_path = interview.raw_audio_path + ".fixed.wav"
                with wave.open(fixed_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2) # 16-bit
                    wav_file.setframerate(16000)
                    wav_file.writeframes(raw_data)
                
                # Replace original
                os.replace(fixed_path, interview.raw_audio_path)
                api_logger.info("Fixed WAV header successfully.")
            except Exception as e:
                api_logger.error(f"Failed to fix WAV header: {e}")
                # We continue, maybe ffmpeg can handle it or it fails again
    
    try:
        # Create output directory for processed audio
        output_dir = os.path.join(os.path.dirname(interview.raw_audio_path), "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process audio stream with diarization
        processed_segments = diarization_service.process_audio_stream(
            interview.raw_audio_path, interview_id, output_dir
        )
        
        # --- NEW LOGIC: Transcribe ALL segments for correction context ---
        import soundfile as sf
        
        full_transcript_segments = []
        raw_audio_data, sr = librosa.load(interview.raw_audio_path, sr=16000)
        
        api_logger.info(f"Transcribing {len(processed_segments)} segments for full context...")
        
        # Sort by start_time just in case
        processed_segments.sort(key=lambda x: x.get("start_time", 0))
        
        # Initialize variable
        respondent_audio_path = None

        for segment in processed_segments:
            # Skip the 'respondent_full' summary chunk but save the path
            if segment.get("segment_id") == "respondent_full":
                respondent_audio_path = segment.get("file_path")
                continue
                
            # Get segment audio from raw data (more reliable than reading temp files again if deleted)
            start_sample = int(segment["start_time"] * sr)
            end_sample = int(segment["end_time"] * sr)
            
            # Safety check
            if end_sample > len(raw_audio_data):
                end_sample = len(raw_audio_data)
                
            if start_sample >= end_sample:
                continue
                
            seg_audio = raw_audio_data[start_sample:end_sample]
            
            # Save to temp for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_seg:
                tmp_seg_path = tmp_seg.name
            
            try:
                sf.write(tmp_seg_path, seg_audio, sr)
                
                # Transcribe
                seg_result = await whisper_service.transcribe(tmp_seg_path)
                seg_text = seg_result.get("text", "").strip()
                
                if seg_text:
                    full_transcript_segments.append({
                        "speaker": segment.get("speaker", "unknown"),
                        "text": seg_text,
                        "start": segment["start_time"],
                        "end": segment["end_time"]
                    })
            except Exception as e:
                api_logger.warning(f"Failed to transcribe segment {segment}: {e}")
            finally:
                if os.path.exists(tmp_seg_path):
                    os.remove(tmp_seg_path)

        # Apply Diarization Correction
        api_logger.info("Applying LLM Diarization Correction...")
        correction_result = llm_service.correct_diarization(full_transcript_segments)
        corrected_segments = correction_result.get("segments", [])
        
        # If correction failed or returned empty, fallback to original
        if not corrected_segments:
            api_logger.warning("Diarization correction returned empty, using original segments.")
            corrected_segments = []
            for s in full_transcript_segments:
                corrected_segments.append({
                    "speaker_corrected": s["speaker"], # Map to expected key
                    "text": s["text"]
                })

        # Construct Full Transcript Text
        formatted_transcript_parts = []
        respondent_text_parts = []
        
        for seg in corrected_segments:
            speaker = seg.get("speaker_corrected", "Unknown")
            text = seg.get("text", "")
            if not text: continue
            
            formatted_transcript_parts.append(f"{speaker}: {text}")
            
            if speaker.lower() == "respondent":
                respondent_text_parts.append(text)
                
        full_transcript_text = "\n\n".join(formatted_transcript_parts)
        respondent_only_text = " ".join(respondent_text_parts)
        
        # Use respondent text for extraction? 
        # User prompt requests extraction "based on specific question". 
        # But here we do Batch extraction. 
        # Ideally Batch extraction should use respondent_only_text but verify with context if needed.
        # For compatibility with existing Batch Extraction prompt, let's use the FULL CONTEXT but maybe prompt needs adaptation?
        # The existing batch prompt (llm_service.extract_information) takes raw text.
        # Let's pass the FULL transcript (with speaker labels) so LLM can differentiate questions vs answers!
        # This is a significant improvement.
        
        transcript_text = full_transcript_text

        # Apply Transcription Normalization
        api_logger.info("Applying Transcription Normalization...")
        normalized_transcript = llm_service.normalize_transcript(transcript_text)
        
        # Determine strictness: If normalization fails or returns empty, fallback to original
        if not normalized_transcript:
            normalized_transcript = transcript_text
            
        # Use Normalized Text for saving and extraction
        final_transcript_text = normalized_transcript
        
        # Save transcript to file (User Request)
        try:
            transcript_path = os.path.join(output_dir, "transcript.txt")
            with open(transcript_path, "w", encoding="utf-8") as tf:
                tf.write(final_transcript_text)
            api_logger.info(f"Saved full transcript to {transcript_path}")
        except Exception as e:
            api_logger.error(f"Failed to save text transcript: {e}")

        # Create or update transcript
        existing_transcript = db.query(InterviewTranscript).filter(
            InterviewTranscript.interview_id == interview.id
        ).first()
        
        if existing_transcript:
            existing_transcript.cleaned_transcript = final_transcript_text
            existing_transcript.raw_transcript = transcript_text # Keep raw diarized version
        else:
            new_transcript = InterviewTranscript(
                interview_id=interview.id,
                raw_transcript=transcript_text,
                cleaned_transcript=final_transcript_text
            )
            db.add(new_transcript)
        
        db.commit()
        
        # Extract information using LLM
        # Use NORMALIZED transcript for best extraction results
        api_logger.info(f"Batch Transcript for extraction (len={len(final_transcript_text)})")
        extracted_info = llm_service.extract_information(final_transcript_text)
        api_logger.info(f"Batch Extracted Info: {extracted_info}")
        
        # Save extracted information to ExtractedAnswer table
        if extracted_info:
            # FLUSH OLD EXTRACTIONS TO PREVENT STALE DATA
            # This ensures that re-processing an interview doesn't retain old/stale fields
            db.query(ExtractedAnswer).filter(
                ExtractedAnswer.interview_id == interview.id
            ).delete(synchronize_session=False)
            db.commit()
            
            for key, value in extracted_info.items():
                if not value: continue
                    
                # Find question by variable_name
                question = db.query(QuestionnaireQuestion).filter(
                    QuestionnaireQuestion.variable_name == key
                ).first()
                
                if question:
                    # Check existing answer
                    answer = db.query(ExtractedAnswer).filter(
                        ExtractedAnswer.interview_id == interview.id,
                        ExtractedAnswer.question_id == question.id
                    ).first()
                    
                    if answer:
                        answer.answer_text = str(value)
                        answer.confidence_score = 1.0 # Batch mode assumes high confidence or we can get it from LLM
                    else:
                        answer = ExtractedAnswer(
                            interview_id=interview.id,
                            question_id=question.id,
                            answer_text=str(value),
                            confidence_score=1.0
                        )
                        db.add(answer)
            
            db.commit()
        
        return {
            "message": "Audio processed successfully with Diarization Correction & Normalization",
            "transcript": final_transcript_text,
            "extracted_info": extracted_info,
            "respondent_audio_path": respondent_audio_path # Still return this useful path
        }
    except Exception as e:
        api_logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio: {str(e)}"
        )

@router.get("/{interview_id}/chunks", response_model=List[AudioChunkSchema])
def get_audio_chunks(
    *,
    db: Session = Depends(get_db),
    interview_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get audio chunks for an interview
    """
    # Check if interview exists and belongs to current user
    role_str = str(current_user.role).lower().split('.')[-1]
    if role_str == "admin" or current_user.role == UserRole.ADMIN:
        interview = db.query(Interview).filter(
            Interview.id == interview_id
        ).first()
    else:
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.enumerator_id == current_user.id
        ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    chunks = db.query(AudioChunk).filter(
        AudioChunk.interview_id == interview_id
    ).order_by(AudioChunk.chunk_order).all()
    
    return chunks

@router.get("/{interview_id}/transcript", response_model=Dict[str, str])
def get_interview_transcript(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get full transcript for an interview by aggregating audio chunks
    """
    role_str = str(current_user.role).lower().split('.')[-1]
    if role_str == "admin" or current_user.role == UserRole.ADMIN:
        interview = db.query(Interview).filter(
            Interview.id == interview_id
        ).first()
    else:
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.enumerator_id == current_user.id
        ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    # Try to get from InterviewTranscript first
    if interview.transcript and interview.transcript.cleaned_transcript:
        return {"transcript": interview.transcript.cleaned_transcript}
        
    # Fallback 1: Aggregate from AudioChunks (Prioritize raw speech)
    chunks = db.query(AudioChunk).filter(
        AudioChunk.interview_id == interview_id,
        AudioChunk.transcript.isnot(None)
    ).order_by(AudioChunk.chunk_order).all()
    
    full_transcript = " ".join([chunk.transcript for chunk in chunks if chunk.transcript])
    
    if full_transcript.strip():
        return {"transcript": full_transcript}

    # Fallback 2: Construct from ExtractedAnswer (Last resort)
    extracted_answers = db.query(ExtractedAnswer).filter(
        ExtractedAnswer.interview_id == interview_id
    ).all()
    
    if extracted_answers:
        transcript_parts = []
        for ans in extracted_answers:
            question = db.query(QuestionnaireQuestion).filter(QuestionnaireQuestion.id == ans.question_id).first()
            q_text = question.question_text if question else f"Question {ans.question_id}"
            transcript_parts.append(f"Q: {q_text}\nA: {ans.answer_text}\n")
        
        full_transcript = "\n".join(transcript_parts)
        return {"transcript": full_transcript}

    return {"transcript": "Belum ada transkripsi tersedia."}

@router.get("/{interview_id}/audio")
def get_interview_audio(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get the full audio recording of the interview
    """
    # Admin can access any interview, enumerators can only access their own
    # Robust Role Check
    role_str = str(current_user.role).lower().split('.')[-1]
    if role_str == "admin" or current_user.role == UserRole.ADMIN:
        interview = db.query(Interview).filter(
            Interview.id == interview_id
        ).first()
    else:
        interview = db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.enumerator_id == current_user.id
        ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
        
    # Path logic: Matches ws.py save location
    file_path = os.path.join(settings.INTERVIEW_STORAGE_DIR, f"{interview_id}.wav")
    
    if not os.path.exists(file_path):
        # Fallback to interview.raw_audio_path if uploaded manually
        if interview.raw_audio_path and os.path.exists(interview.raw_audio_path):
            file_path = interview.raw_audio_path
        else:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio recording not found"
            )

    # AUTO-FIX: Check if WAV header is valid, if not (Raw PCM), fix it
    import wave
    try:
        with wave.open(file_path, 'rb') as f:
            pass # Valid WAV
    except (wave.Error, EOFError):
        # Invalid or headerless. Try to treat as Raw PCM 16-bit 16kHz Mono
        try:
            api_logger.info(f"Auto-fixing headerless WAV: {file_path}")
            with open(file_path, 'rb') as pcm:
                raw_data = pcm.read()
            
            # Avoid fixing empty files
            if len(raw_data) > 0:
                temp_path = file_path + ".fixed.wav"
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2) # 16-bit
                    wav_file.setframerate(16000)
                    wav_file.writeframes(raw_data)
                
                # Replace original
                os.replace(temp_path, file_path)
                api_logger.info(f"Fixed WAV header for {file_path}")
        except Exception as e:
            api_logger.error(f"Failed to fix WAV header for {file_path}: {e}")
            # Continue to try serving, browser might report error or play static
            
    return FileResponse(file_path, media_type="audio/wav", filename=f"interview_{interview_id}.wav")

@router.get("/{interview_id}/export-mfcc")
def export_interview_mfcc(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Export MFCC features for an interview's audio.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.enumerator_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    if not interview.raw_audio_path:
        raise HTTPException(status_code=404, detail="Interview has no audio recording")
        
    # Construct full path
    path = interview.raw_audio_path.lstrip("/")
    full_path = os.path.abspath(path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Audio file not found on server")
        
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
        
        respondent_name = interview.respondent.full_name if interview.respondent else "Respondent"
        enumerator_username = current_user.username
        
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
                        
                        expected_enumerator_label = f"user_{current_user.id}"
                        
                        if prediction == expected_enumerator_label or prediction == "enumerator":
                            label = "Enumerator"
                            record_name = f"{enumerator_username}_{i+1}"
                        else:
                            label = "Responden"
                            record_name = f"{respondent_name}_{i+1}"
                    else:
                        label = "Responden"
                        record_name = f"{respondent_name}_{i+1}"
                        
                except Exception as e:
                    api_logger.warning(f"Prediction failed for chunk {i}: {e}")
                    label = "Responden" # Default to respondent
                    record_name = f"{respondent_name}_{i+1}"
            else:
                label = "Responden"
                record_name = f"{respondent_name}_{i+1}"
            
            if len(mfccs_33) == 33:
                row = [label, record_name] + mfccs_33.tolist()
                writer.writerow(row)
                
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=mfcc_export_interview_{interview.id}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")