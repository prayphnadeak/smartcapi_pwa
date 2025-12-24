import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
