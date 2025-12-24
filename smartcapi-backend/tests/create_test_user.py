import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.username == "testuser").first()
        if user:
            print("Test user already exists.")
            return

        # Create new user
        new_user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            role="enumerator"
        )
        db.add(new_user)
        db.commit()
        print("[SUCCESS] Test user created: testuser / testpass123")
        
    except Exception as e:
        print(f"[ERROR] Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
