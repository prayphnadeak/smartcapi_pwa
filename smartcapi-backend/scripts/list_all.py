import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Respondent

def list_all():
    db = SessionLocal()
    try:
        count = db.query(Respondent).count()
        print(f"Total respondents: {count}")
        
        with open("all_respondents.txt", "w", encoding="utf-8") as f:
            for r in db.query(Respondent).all():
                f.write(f"ID: {r.id}, Name: {r.full_name}\n")
        print("Written to all_respondents.txt")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all()
