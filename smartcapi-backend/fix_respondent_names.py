import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent, ExtractedAnswer, QuestionnaireQuestion

def fix_names():
    db = SessionLocal()
    interviews = db.query(Interview).all()
    count = 0
    
    print("Scanning for generic respondent names...")
    
    for i in interviews:
        if not i.respondent:
            continue
            
        current_name = i.respondent.full_name
        
        # Check if name is generic
        if current_name in ["New Respondent", "Unknown", "Responden Baru", "Responden"]:
            print(f"Checking Interview {i.id} (Current: {current_name})...")
            
            # Find extracted name
            answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == i.id).all()
            found_name = None
            
            for ans in answers:
                q = db.query(QuestionnaireQuestion).filter(QuestionnaireQuestion.id == ans.question_id).first()
                if q and q.variable_name in ["nama", "Nama", "nama_lengkap", "Name"]:
                    if ans.answer_text and ans.answer_text not in ["None", "null", "-", ""]:
                        found_name = ans.answer_text
                        break
            
            if found_name:
                print(f" -> FOUND FIX: '{found_name}'. Updating DB...")
                i.respondent.full_name = found_name
                db.add(i.respondent)
                count += 1
            else:
                print(" -> No extracted name found.")
        else:
            # print(f"Interview {i.id} has valid name: {current_name}")
            pass
            
    if count > 0:
        db.commit()
        print(f"Successfully updated/fixed {count} respondent names!")
    else:
        print("No generic names found that could be fixed.")
        
    db.close()

if __name__ == "__main__":
    fix_names()
