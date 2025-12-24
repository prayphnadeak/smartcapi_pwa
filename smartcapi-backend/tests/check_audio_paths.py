
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.database import SessionLocal
from app.db.models import Interview


def check_audio_paths():
    output_lines = []
    db = SessionLocal()
    try:
        output_lines.append("Checking audio paths for interviews 6, 7, 8...\n")
        
        ids = [6, 7, 8]
        interviews = db.query(Interview).filter(Interview.id.in_(ids)).all()
        
        for iv in interviews:
            output_lines.append(f"ID={iv.id}, Mode={iv.mode}, Raw Audio Path={iv.raw_audio_path}")
            # Check if file exists if path is not None
            if iv.raw_audio_path:
                abs_path = iv.raw_audio_path
                # backend might store relative or absolute. Let's see.
                exists = os.path.exists(abs_path)
                output_lines.append(f"  -> File Exists on Disk: {exists}")
            else:
                output_lines.append("  -> No audio path recorded.")

    except Exception as e:
        output_lines.append(f"Error querying database: {e}")
    finally:
        db.close()
    
    with open("check_audio_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

if __name__ == "__main__":
    check_audio_paths()
