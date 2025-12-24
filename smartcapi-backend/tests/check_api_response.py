import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent, User
from app.schemas.interview import InterviewSummary

def check_api_response():
    db = SessionLocal()
    try:
        # Get the interview for user 2
        interviews = db.query(Interview).filter(Interview.enumerator_id == 2).all()
        print(f"Found {len(interviews)} interviews for User ID 2")
        
        for interview in interviews:
            # Simulate what the API does
            respondent_name = interview.respondent.full_name if interview.respondent else "Unknown"
            
            summary = InterviewSummary(
                id=interview.id,
                respondent_name=respondent_name,
                mode=interview.mode,
                duration=interview.duration,
                status=interview.status,
                has_recording=bool(interview.raw_audio_path),
                created_at=interview.created_at
            )
            
            print(f"Interview ID: {interview.id}")
            print(f"  Mode: {interview.mode}")
            print(f"  Respondent Name: {respondent_name}")
            print(f"  Serialized: {summary.model_dump()}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_api_response()
