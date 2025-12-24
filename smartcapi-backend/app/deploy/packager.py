import zipfile
import os
import shutil

EXCLUDES = {
    '.git', '.venv', 'node_modules', '__pycache__', '.idea', '.vscode', 'dist', 'build', 'coverage', '.DS_Store', 'storage'
}

def is_excluded(path):
    parts = path.split(os.sep)
    for part in parts:
        if part in EXCLUDES:
            return True
    return False

def zip_directory(source_dir, output_filename):
    print(f"Zipping {source_dir} to {output_filename}...")
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip excluded directories AND large model caches
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('models--')]
            
            for file in files:
                if file.endswith(('.zip', '.tar.gz', '.rar')): # Skip existing archives
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                
                if not is_excluded(file_path):
                    # Filter out large Whisper models (using API instead)
                    if file.endswith(('.pt', '.bin')) and 'rf_model' not in file:
                        print(f"Skipping large model: {arcname}")
                        continue
                        
                    print(f"Adding {arcname}")
                    zipf.write(file_path, arcname)
    print("Optimization complete.")

if __name__ == "__main__":
    # Zip from the project root (one level up from this script location if in deploy/)
    # Assuming this runs from project root
    zip_directory('.', 'smartcapi_deploy.zip')
