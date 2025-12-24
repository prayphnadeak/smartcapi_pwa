import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Interview

def check_paths():
    db = SessionLocal()
    try:
        interviews = db.query(Interview).limit(5).all()
        print(f"{'ID':<5} | {'Raw Audio Path'}")
        print("-" * 50)
        for i in interviews:
            print(f"{i.id:<5} | {i.raw_audio_path}")
    finally:
        db.close()

if __name__ == "__main__":
    check_paths()
