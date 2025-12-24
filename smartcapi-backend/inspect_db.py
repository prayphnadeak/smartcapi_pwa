import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import Interview, Respondent, ExtractedAnswer, QuestionnaireQuestion

db = SessionLocal()
interviews = db.query(Interview).all()

print(f"Total Interviews: {len(interviews)}")

for i in interviews:
    print("-" * 50)
    print(f"ID: {i.id} | Mode: {i.mode} | RespID: {i.respondent_id}")
    
    if i.respondent:
        print(f"Respondent: ID={i.respondent.id}, Name='{i.respondent.full_name}'")
    else:
        print("Respondent: NONE")
        
    print("Extracted Answers:")
    answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == i.id).all()
    for ans in answers:
        q = db.query(QuestionnaireQuestion).filter(QuestionnaireQuestion.id == ans.question_id).first()
        var_name = q.variable_name if q else "UNKNOWN"
        print(f"  - [{var_name}] = '{ans.answer_text}'")
        
db.close()
