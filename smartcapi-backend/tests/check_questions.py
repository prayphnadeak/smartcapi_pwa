import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import QuestionnaireQuestion

db = SessionLocal()
try:
    questions = db.query(QuestionnaireQuestion).all()
    print(f"{'ID':<5} {'Variable Name':<30}")
    print("-" * 40)
    for q in questions:
        print(f"{q.id:<5} {q.variable_name:<30}")
finally:
    db.close()
