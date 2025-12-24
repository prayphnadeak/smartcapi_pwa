import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users in the database (via app.db.database)")
        print("-" * 50)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Full Name: {user.full_name}")
            print("-" * 50)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
