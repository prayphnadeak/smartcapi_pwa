import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import verify_password, get_password_hash

def check_password():
    db = SessionLocal()
    try:
        username = "admincapi"
        password = "supercapi"
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"User {username} not found")
            return

        print(f"User: {user.username}")
        print(f"Stored Hash: {user.hashed_password}")
        
        is_valid = verify_password(password, user.hashed_password)
        print(f"Password '{password}' valid? {is_valid}")
        
        # Test hash generation
        new_hash = get_password_hash(password)
        print(f"New Hash: {new_hash}")
        print(f"Verify New Hash: {verify_password(password, new_hash)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_password()
