import subprocess
import sys
import time
import os

# List of worker modules to run
workers = [
    "app.workers.audio_processor",
    "app.workers.whisper_worker",
    "app.workers.merger",
    "app.workers.llm_worker"
]

def main():
    processes = []
    
    print("Starting SmartCAPI Hybrid Workers...")
    print(f"Python executable: {sys.executable}")
    
    try:
        for worker in workers:
            print(f"Launching {worker}...")
            # Use -m to run as module so imports work correctly
            p = subprocess.Popen([sys.executable, "-m", worker], cwd=os.getcwd())
            processes.append(p)
            
        print("All workers started. Press Ctrl+C to stop.")
        
        while True:
            # Check if any process died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"Worker {workers[i]} died with code {p.returncode}. Restarting...")
                    processes[i] = subprocess.Popen([sys.executable, "-m", workers[i]], cwd=os.getcwd())
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping workers...")
        for p in processes:
            p.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
