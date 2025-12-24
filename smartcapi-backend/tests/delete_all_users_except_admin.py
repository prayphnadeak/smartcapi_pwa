"""
Delete all users except admincapi from the database
"""
import os
import shutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User, Interview, VoiceProfile, AudioChunk, ExtractedAnswer, ProcessingLog, InterviewTranscript

def delete_non_admin_users():
    db = SessionLocal()
    
    try:
        # Get all users except admincapi
        users_to_delete = db.query(User).filter(User.username != "admincapi").all()
        
        if not users_to_delete:
            print("✅ Tidak ada user selain admincapi yang ditemukan.")
            return
        
        print(f"📋 Ditemukan {len(users_to_delete)} user yang akan dihapus:")
        for user in users_to_delete:
            print(f"   - {user.username} (ID: {user.id}, Email: {user.email})")
        
        confirm = input("\n⚠️  Apakah Anda yakin ingin menghapus semua user ini? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Pembatalan oleh user. Tidak ada yang dihapus.")
            return
        
        deleted_count = 0
        for user in users_to_delete:
            user_id = user.id
            username = user.username
            
            try:
                # Delete related records for this user
                # 1. Delete extracted answers for user's interviews
                user_interviews = db.query(Interview).filter(Interview.enumerator_id == user_id).all()
                for interview in user_interviews:
                    db.query(ExtractedAnswer).filter(ExtractedAnswer.interview_id == interview.id).delete()
                    db.query(ProcessingLog).filter(ProcessingLog.interview_id == interview.id).delete()
                    db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == interview.id).delete()
                    db.query(AudioChunk).filter(AudioChunk.interview_id == interview.id).delete()
                
                # 2. Delete interviews
                db.query(Interview).filter(Interview.enumerator_id == user_id).delete()
                
                # 3. Delete voice profiles
                db.query(VoiceProfile).filter(VoiceProfile.user_id == user_id).delete()
                
                # Delete user's voice samples directory
                voice_sample_dir = os.path.join("storage", "voice_samples", str(user_id))
                if os.path.exists(voice_sample_dir):
                    shutil.rmtree(voice_sample_dir)
                    print(f"   📁 Deleted voice samples for {username}")
                
                # Finally, delete the user
                db.delete(user)
                db.commit()
                
                deleted_count += 1
                print(f"   ✅ Deleted user: {username} (ID: {user_id})")
                
            except Exception as e:
                print(f"   ❌ Error deleting user {username}: {str(e)}")
                db.rollback()
                continue
        
        print(f"\n✅ Selesai! {deleted_count} user berhasil dihapus.")
        print(f"📊 User yang tersisa: admincapi")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  HAPUS SEMUA USER KECUALI ADMINCAPI")
    print("=" * 60)
    delete_non_admin_users()
