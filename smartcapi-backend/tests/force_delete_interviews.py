import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent, AudioChunk, ExtractedAnswer, InterviewTranscript, ProcessingLog
from sqlalchemy import text

def force_delete_all():
    db = SessionLocal()
    try:
        print("Starting force deletion of all interview data...")
        
        # Delete related tables first
        print("Deleting AudioChunks...")
        db.query(AudioChunk).delete()
        
        print("Deleting ExtractedAnswers...")
        db.query(ExtractedAnswer).delete()
        
        print("Deleting InterviewTranscripts...")
        db.query(InterviewTranscript).delete()
        
        print("Deleting ProcessingLogs...")
        db.query(ProcessingLog).delete()
        
        # Delete Interviews
        print("Deleting Interviews...")
        num_interviews = db.query(Interview).delete()
        print(f"Deleted {num_interviews} interviews.")
        
        # Delete Respondents
        print("Deleting Respondents...")
        num_respondents = db.query(Respondent).delete()
        print(f"Deleted {num_respondents} respondents.")
        
        db.commit()
        print("[SUCCESS] All interview and respondent data deleted successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during deletion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_delete_all()
