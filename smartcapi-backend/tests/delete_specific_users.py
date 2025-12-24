import sqlite3
import os

# Database path
DB_PATH = 'smartcapi.db'

def delete_user(username):
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User '{username}' not found.")
            return

        user_id = user[0]
        print(f"Found user '{username}' with ID: {user_id}")

        # 1. Get interview IDs for this user
        cursor.execute("SELECT id FROM interviews WHERE enumerator_id = ?", (user_id,))
        interviews = cursor.fetchall()
        interview_ids = [i[0] for i in interviews]
        
        if interview_ids:
            print(f"Found {len(interview_ids)} interviews. Deleting related records...")
            placeholders = ','.join('?' * len(interview_ids))
            
            # Delete extracted answers
            cursor.execute(f"DELETE FROM extracted_answers WHERE interview_id IN ({placeholders})", interview_ids)
            print(f"Deleted {cursor.rowcount} extracted_answers")

            # Delete processing logs
            cursor.execute(f"DELETE FROM processing_logs WHERE interview_id IN ({placeholders})", interview_ids)
            print(f"Deleted {cursor.rowcount} processing_logs")

            # Delete transcripts
            cursor.execute(f"DELETE FROM interview_transcripts WHERE interview_id IN ({placeholders})", interview_ids)
            print(f"Deleted {cursor.rowcount} interview_transcripts")

            # Delete audio chunks
            cursor.execute(f"DELETE FROM audio_chunks WHERE interview_id IN ({placeholders})", interview_ids)
            print(f"Deleted {cursor.rowcount} audio_chunks")

            # Delete interviews
            cursor.execute("DELETE FROM interviews WHERE enumerator_id = ?", (user_id,))
            print(f"Deleted {cursor.rowcount} interviews")
        else:
            print("No interviews found for this user.")

        # 2. Delete voice profiles
        cursor.execute("DELETE FROM voice_profiles WHERE user_id = ?", (user_id,))
        print(f"Deleted {cursor.rowcount} voice_profiles")

        # 3. Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"Deleted user '{username}' (ID: {user_id})")

        conn.commit()
        print("Deletion complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting force delete...")
    delete_user('prayndk')
    print("-" * 30)
    delete_user('pray25')
