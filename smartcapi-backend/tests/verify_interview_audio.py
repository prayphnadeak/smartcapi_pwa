import sys
import os

# Adjust path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    print("SQLAlchemy imported.")
    
    from app.db.database import Base, get_db, SessionLocal
    from app.db.models import Interview, User
    print("App modules imported.")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error during import: {e}")
    sys.exit(1)

def check_interview(interview_id):
    db = SessionLocal()
    try:
        print(f"Checking Interview ID: {interview_id}")
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        
        if not interview:
            print("❌ Interview NOT FOUND in database.")
            return
            
        print(f"✅ Interview found.")
        print(f"   ID: {interview.id}")
        print(f"   Enumerator ID: {interview.enumerator_id}")
        print(f"   Raw Audio Path: {interview.raw_audio_path}")
        
        if not interview.raw_audio_path:
            print("❌ Interview has NO raw_audio_path.")
            return
            
        # Check file existence
        # The path in DB might be relative or absolute
        path = interview.raw_audio_path.lstrip("/")
        full_path = os.path.abspath(path)
        
        print(f"   Checking file at: {full_path}")
        
        if os.path.exists(full_path):
            print("✅ Audio file EXISTS on disk.")
        else:
            print("❌ Audio file NOT FOUND on disk.")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_interview(1)
