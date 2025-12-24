import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def reset_password():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "testuser").first()
        if user:
            user.hashed_password = get_password_hash("testpass123")
            db.commit()
            print("[SUCCESS] Password reset for testuser")
        else:
            print("[ERROR] User testuser not found")
    except Exception as e:
        print(f"[ERROR] Error resetting password: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
