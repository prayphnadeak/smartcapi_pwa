import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"{'ID':<5} {'Username':<20} {'Role':<10}")
    print("-" * 40)
    for u in users:
        print(f"{u.id:<5} {u.username:<20} {u.role:<10}")
finally:
    db.close()
