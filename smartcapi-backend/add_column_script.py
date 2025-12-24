
import sqlite3
import os

DB_PATH = "c:/xampp/htdocs/smartcapi_pwa/smartcapi-backend/smartcapi.db"

def add_transcript_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(extracted_answers)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "transcript" not in columns:
            print("Adding 'transcript' column to 'extracted_answers' table...")
            cursor.execute("ALTER TABLE extracted_answers ADD COLUMN transcript TEXT")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'transcript' column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_transcript_column()
