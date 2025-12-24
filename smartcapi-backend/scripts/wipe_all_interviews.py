
import sys
import os

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import SessionLocal, engine
from app.db import models

def wipe_data():
    db = SessionLocal()
    try:
        print("⚠ WARNING: This will delete ALL interview data!")
        # Order matters for foreign keys if cascades aren't perfect
        # But we will use DELETE FROM to be fast
        
        tables_to_wipe = [
            "role_event_logs",
            "processing_logs",
            "extracted_answers",
            "interview_transcripts",
            "audio_chunks",
            "interviews",
            "respondents"
        ]
        
        for table in tables_to_wipe:
            print(f"Deleting from {table}...")
            db.execute(text(f"DELETE FROM {table}"))
            
        db.commit()
        print("✅ All interview data wiped successfully.")
        
    except Exception as e:
        print(f"❌ Error wiping data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    wipe_data()
