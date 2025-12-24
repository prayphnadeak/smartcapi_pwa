import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User

def check_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 2).first()
        if user:
            print(f"User ID 2: Username={user.username}, Full Name={user.full_name}, Role={user.role}")
        else:
            print("User ID 2 not found.")
            
        # Also list all users to be sure
        users = db.query(User).all()
        print("\nAll Users:")
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()
