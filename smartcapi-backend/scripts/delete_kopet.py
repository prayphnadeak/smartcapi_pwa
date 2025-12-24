import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Respondent, Interview, AudioChunk, ExtractedAnswer, InterviewTranscript, ProcessingLog, RoleEventLog

def delete_data():
    db = SessionLocal()
    try:
        respondent_id = 16
        print(f"Targeting Respondent ID: {respondent_id}")
        
        respondent = db.query(Respondent).filter(Respondent.id == respondent_id).first()
        if not respondent:
            print("Respondent not found!")
            return

        print(f"Found Respondent: {respondent.full_name}")
        
        # 1. Find all interviews
        interviews = db.query(Interview).filter(Interview.respondent_id == respondent_id).all()
        print(f"Found {len(interviews)} interviews to delete.")
        
        for i in interviews:
            print(f"  Processing Interview ID {i.id}...")
            
            # Delete dependents
            
            # Logs
            num_logs = db.query(ProcessingLog).filter(ProcessingLog.interview_id == i.id).delete()
            print(f"    - Deleted {num_logs} ProcessingLogs")
            
            num_roles = db.query(RoleEventLog).filter(RoleEventLog.interview_id == i.id).delete()
            print(f"    - Deleted {num_roles} RoleEventLogs")
            
            # Data
            num_chunks = db.query(AudioChunk).filter(AudioChunk.interview_id == i.id).delete()
            print(f"    - Deleted {num_chunks} AudioChunks")
            
            num_answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == i.id).delete()
            print(f"    - Deleted {num_answers} ExtractedAnswers")
            
            num_transcripts = db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == i.id).delete()
            print(f"    - Deleted {num_transcripts} InterviewTranscripts")
            
            # Delete Interview itself
            db.delete(i)
            print(f"    - Deleted Interview ID {i.id}")
            
        # 2. Delete Respondent
        db.delete(respondent)
        print(f"Deleted Respondent ID {respondent_id}")
        
        db.commit()
        print("\nSUCCESS: All data deleted.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_data()
