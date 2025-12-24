import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.models import User
from app.db.database import SessionLocal

def check_audio():
    db = SessionLocal()
    try:
        # Find user pray25
        user = db.query(User).filter(User.username == "pray25").first()
        if not user:
            print("User pray25 not found!")
            return

        print(f"User: {user.username}")
        print(f"Voice Sample Path (DB): {user.voice_sample_path}")
        
        if user.voice_sample_path:
            # Check if file exists
            abs_path = os.path.abspath(user.voice_sample_path)
            print(f"Absolute Path: {abs_path}")
            if os.path.exists(abs_path):
                print("✅ File exists on disk.")
            else:
                print("❌ File NOT found on disk.")
                
            # Check URL construction simulation
            url_path = user.voice_sample_path.replace("\\", "/")
            print(f"Constructed URL segment: {url_path}")
            print(f"Full URL would be: http://127.0.0.1:8001/{url_path}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_audio()
