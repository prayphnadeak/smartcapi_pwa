import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adjust path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.db.database import SessionLocal
    from app.db.models import Interview
    
    db = SessionLocal()
    try:
        # Check for any interview with a recording
        interview_with_recording = db.query(Interview).filter(
            (Interview.raw_audio_path != None) & (Interview.raw_audio_path != "")
        ).first()
        
        if interview_with_recording:
            print(f"✅ Found interview with recording: ID {interview_with_recording.id}")
        else:
            print("❌ No interviews with recordings found.")
            
        # Check specifically for ID 1
        interview_1 = db.query(Interview).filter(Interview.id == 1).first()
        if interview_1:
            print(f"ℹ️ Interview 1 raw_audio_path: '{interview_1.raw_audio_path}'")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

except Exception as e:
    print(f"Setup Error: {e}")
