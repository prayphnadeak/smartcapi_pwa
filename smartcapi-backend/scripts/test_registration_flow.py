import requests
import time
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "test_user_flow",
    "password": "password123",
    "email": "test_flow@example.com",
    "full_name": "Test User Flow",
    "phone": "08123456789",
    "role": "enumerator"
}

def run_test():
    print("--- Starting Registration Flow Verification ---")

    # 1. Register
    print("\n[1] Registering User...")
    try:
        reg_response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
        if reg_response.status_code == 200:
            print(" -> Registration Success!")
        else:
            # Handle user already exists
            if "already exists" in reg_response.text:
                print(" -> User already exists (Skipping registration)")
            else:
                print(f" -> Registration Failed: {reg_response.text}")
                return
    except Exception as e:
        print(f" -> Registration Network Error: {e}")
        return

    # 2. Login
    print("\n[2] Logging In...")
    try:
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        # FastAPI OAuth2PasswordRequestForm expects form data, not json
        login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f" -> Login Failed: {login_response.text}")
            return
            
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(" -> Login Success! Token acquired.")
    except Exception as e:
        print(f" -> Login Network Error: {e}")
        return

    # 3. Upload Voice Sample
    print("\n[3] Uploading Voice Sample (Simulating RegisterVoice.vue)...")
    try:
        # Create a dummy wav file
        with open("test_voice.wav", "wb") as f:
            # Min header for a valid wav? Or just junk bytes might fail librosa.
            # Let's try to send junk first, backend might error on librosa.
            # Ideally we need a valid wav. 
            # Writing 10kb of zero bytes might be interpreted as silence/improper wav.
            # But the 'Upload' step just saves the file. The 'Background Task' processes it.
            # So Upload should succeed 200 OK.
            f.write(b'\x00' * 1024) 
        
        with open("test_voice.wav", "rb") as f_up:
            files = {
                'voice_file': ('recording.wav', f_up, 'audio/wav')
            }
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # NOTE: This endpoint triggers the background training
            upload_response = requests.post(f"{BASE_URL}/users/me/voice-sample", files=files, headers=headers)
        
        if upload_response.status_code == 200:
            print(" -> Upload Success!")
        else:
            print(f" -> Upload Failed: {upload_response.text}")
            return

    except Exception as e:
        print(f" -> Upload Network Error: {e}")
        return
    finally:
        if os.path.exists("test_voice.wav"):
            os.remove("test_voice.wav")

    # 4. Check Training Progress
    print("\n[4] Polling Training Progress (Simulating TrainingProgress.vue)...")
    headers = {'Authorization': f'Bearer {access_token}'}
    
    for i in range(5):
        try:
            progress_response = requests.get(f"{BASE_URL}/training/progress", headers=headers)
            if progress_response.status_code == 200:
                data = progress_response.json()
                print(f" -> Poll {i+1}: Progress={data.get('progress')}% Status={data.get('status')} Msg={data.get('message')}")
                if data.get('status') == 'error':
                    # It will likely error because my wav file was junk
                    print(" -> (Expected) Error detected (due to junk audio), but polling works!")
                    break
            else:
                print(f" -> Poll Failed: {progress_response.status_code}")
        except Exception as e:
            print(f" -> Polling Error: {e}")
        
        time.sleep(1)

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
