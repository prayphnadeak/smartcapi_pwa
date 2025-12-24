import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Respondent, User
from sqlalchemy import or_

def find_data():
    db = SessionLocal()
    try:
        search_terms = ["%Kopet%", "%Pertuli%"]
        print("Starting search...")
        
        # SEARCH RESPONDENTS
        print("\n--- Searching Respondents ---")
        for term in search_terms:
            respondents = db.query(Respondent).filter(Respondent.full_name.ilike(term)).all()
            if respondents:
                for r in respondents:
                    print(f"FOUND RESPONDENT: ID={r.id}, Name='{r.full_name}'")
            else:
                print(f"No respondents found for '{term}'")

        # SEARCH USERS
        print("\n--- Searching Users ---")
        for term in search_terms:
            users = db.query(User).filter(
                or_(
                    User.full_name.ilike(term),
                    User.username.ilike(term)
                )
            ).all()
            if users:
                for u in users:
                    print(f"FOUND USER: ID={u.id}, Username='{u.username}', Name='{u.full_name}'")
            else:
                print(f"No users found for '{term}'")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    find_data()
