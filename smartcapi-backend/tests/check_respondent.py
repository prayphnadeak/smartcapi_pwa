import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Respondent
from sqlalchemy import func

def check_respondent():
    db = SessionLocal()
    try:
        target_name = "Henny Rimawati Simatupang"
        # Case insensitive search
        respondent = db.query(Respondent).filter(func.lower(Respondent.full_name) == target_name.lower()).first()
        
        with open("respondents_list.txt", "w", encoding="utf-8") as f:
            if respondent:
                f.write(f"Found respondent: {respondent.full_name} (ID: {respondent.id})\n")
            else:
                f.write(f"Respondent '{target_name}' not found.\n")
                
            f.write("\nList of respondents in database (first 20):\n")
            others = db.query(Respondent).limit(20).all()
            if not others:
                f.write("No respondents found in the database.\n")
            for r in others:
                f.write(f"- {r.full_name} (ID: {r.id})\n")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_respondent()
