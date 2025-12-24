
import time
import os
import sys
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

print("Setting up benchmark...")

try:
    from faster_whisper import WhisperModel
    import torch
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

model_size = "small"
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

print(f"Device being tested: {device}")
print(f"Compute Type: {compute_type}")
print(f"Model: {model_size}")

if device == "cpu":
    print("WARNING: Testing on CPU. Performance will be slow.")

try:
    start_load = time.time()
    model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root="./app/processing/models")
    end_load = time.time()
    print(f"Model loaded in {end_load - start_load:.2f} seconds.")

    # Create dummy audio (10 seconds of silence/noise)
    # faster-whisper accepts path or array. Let's use array to skip I/O
    # 16000 Hz * 10s
    audio = np.random.uniform(-0.1, 0.1, 16000 * 10).astype(np.float32)
    
    print("Starting transcription benchmark (10s random audio)...")
    start_transcribe = time.time()
    segments, info = model.transcribe(audio, language="en", beam_size=1)
    # Consume generator
    list(segments)
    end_transcribe = time.time()
    
    print(f"Transcription took {end_transcribe - start_transcribe:.2f} seconds.")
    print("Benchmark completed successfully.")

except Exception as e:
    print(f"Benchmark Failed: {e}")
    import traceback
    traceback.print_exc()
