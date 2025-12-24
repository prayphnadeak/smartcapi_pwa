
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent

def check_interviews(enumerator_id):
    output_lines = []
    db = SessionLocal()
    try:
        output_lines.append(f"Checking interviews for Enumerator ID: {enumerator_id}\n")

        interviews = db.query(Interview).filter(Interview.enumerator_id == enumerator_id).order_by(Interview.created_at.desc()).all()
        
        if interviews:
            output_lines.append(f"Found {len(interviews)} interviews:\n")
            for iv in interviews:
                respondent_name = iv.respondent.full_name if iv.respondent else "Unknown"
                output_lines.append(f"ID={iv.id}, Date={iv.created_at}, Status={iv.status}, Mode={iv.mode}, Respondent={respondent_name}")
        else:
            output_lines.append("No interviews found for this enumerator.")

    except Exception as e:
        output_lines.append(f"Error querying database: {e}")
    finally:
        db.close()
    
    with open("check_interviews_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

if __name__ == "__main__":
    check_interviews(5) # ID for Idanur
