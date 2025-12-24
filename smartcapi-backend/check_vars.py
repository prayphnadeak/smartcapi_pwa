
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.database import SessionLocal
from app.db.models import QuestionnaireQuestion

db = SessionLocal()
qs = db.query(QuestionnaireQuestion).all()
print("Variable Names:")
for q in qs:
    print(f"- {q.variable_name} (Active: {q.is_active})")
db.close()
