import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent, User
import json

def check_manual_interviews():
    db = SessionLocal()
    try:
        # Get all manual interviews
        interviews = db.query(Interview).filter(Interview.mode == 'manual').all()
        print(f"Found {len(interviews)} manual interviews")
        print("-" * 50)
        
        for interview in interviews:
            respondent_name = interview.respondent.full_name if interview.respondent else "Unknown"
            # Manually fetch enumerator if relationship is missing
            enumerator = db.query(User).filter(User.id == interview.enumerator_id).first()
            enumerator_name = enumerator.username if enumerator else f"Unknown (ID: {interview.enumerator_id})"
            
            print(f"ID: {interview.id}")
            print(f"Enumerator: {enumerator_name}")
            print(f"Respondent: {respondent_name}")
            print(f"Created At: {interview.created_at}")
            print(f"Duration: {interview.duration} seconds")
            
            # Print extracted answers
            if interview.extracted_answers:
                print("Extracted Answers:")
                for answer in interview.extracted_answers:
                    question_text = answer.question.question_text if answer.question else "Unknown Question"
                    print(f"  - {question_text}: {answer.answer_text}")
            else:
                print("No extracted answers found.")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_manual_interviews()
