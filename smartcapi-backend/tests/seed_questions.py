import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import QuestionnaireQuestion

def seed_questions():
    db = SessionLocal()
    
    questions = [
        {"variable_name": "nama", "question_text": "Nama Lengkap", "data_type": "text", "question_number": 1},
        {"variable_name": "tempat_lahir", "question_text": "Tempat Lahir", "data_type": "text", "question_number": 2},
        {"variable_name": "tanggal_lahir", "question_text": "Tanggal Lahir", "data_type": "date", "question_number": 3},
        {"variable_name": "usia", "question_text": "Usia", "data_type": "number", "question_number": 4},
        {"variable_name": "pendidikan", "question_text": "Pendidikan Terakhir", "data_type": "select", "question_number": 5},
        {"variable_name": "alamat", "question_text": "Alamat Lengkap", "data_type": "text", "question_number": 6},
        {"variable_name": "pekerjaan", "question_text": "Pekerjaan", "data_type": "text", "question_number": 7},
        {"variable_name": "hobi", "question_text": "Hobi", "data_type": "text", "question_number": 8},
        {"variable_name": "nomor_telepon", "question_text": "Nomor Telepon", "data_type": "text", "question_number": 9},
        {"variable_name": "alamat_email", "question_text": "Alamat Email", "data_type": "email", "question_number": 10},
    ]
    
    try:
        for q_data in questions:
            # Check if exists
            existing = db.query(QuestionnaireQuestion).filter(
                QuestionnaireQuestion.variable_name == q_data["variable_name"]
            ).first()
            
            if not existing:
                question = QuestionnaireQuestion(**q_data)
                db.add(question)
                print(f"Added question: {q_data['variable_name']}")
            else:
                print(f"Question exists: {q_data['variable_name']}")
        
        db.commit()
        print("Seeding completed successfully.")
        
    except Exception as e:
        print(f"Error seeding questions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_questions()
