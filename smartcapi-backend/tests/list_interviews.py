import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import Interview, User, Respondent

db = SessionLocal()
try:
    interviews = db.query(Interview).all()
    print(f"{'ID':<5} {'Mode':<15} {'Enumerator ID':<15} {'Respondent Name':<30}")
    print("-" * 70)
    for i in interviews:
        respondent_name = i.respondent.full_name if i.respondent else "Unknown"
        print(f"{i.id:<5} {i.mode:<15} {i.enumerator_id:<15} {respondent_name:<30}")
finally:
    db.close()
