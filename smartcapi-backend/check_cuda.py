
import sys
import os

print("Checking CUDA availability...")

try:
    import torch
    print(f"Torch version: {torch.__version__}")
    print(f"CUDA available (torch): {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA NOT available for Torch.")
except ImportError:
    print("Torch not installed.")
except Exception as e:
    print(f"Error checking Torch: {e}")

print("-" * 20)

try:
    import ctranslate2
    print(f"ctranslate2 version: {ctranslate2.__version__}")
    # ctranslate2 doesn't have a simple is_available() similar to torch, 
    # but we can try to get supported devices
    print(f"ctranslate2 supported compute types for cuda: {ctranslate2.get_supported_compute_types('cuda')}")
    print("CUDA seems available for ctranslate2 (based on compute types query).")
except ImportError:
    print("ctranslate2 not installed.")
except ValueError as e:
    print(f"ctranslate2 error (likely execution provider missing): {e}")
except Exception as e:
    print(f"Error checking ctranslate2: {e}")

print("-" * 20)
print("Finished check.")
