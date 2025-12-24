import requests
import os

BASE_URL = "http://127.0.0.1:8001/api/v1"

def reproduce():
    # 1. Login as admin
    print("Logging in as admin...")
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "admincapi", "password": "supercapi"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Get users to find admin ID
    print("Fetching users...")
    resp = requests.get(f"{BASE_URL}/users/", headers=headers)
    if resp.status_code != 200:
        print(f"Get users failed: {resp.text}")
        return
    users = resp.json()
    admin_user = next((u for u in users if u["username"] == "admincapi"), None)
    if not admin_user:
        print("Admin user not found in list.")
        return
    print(f"Admin user found: {admin_user}")

    # 3. Upload voice sample for admin
    print("Uploading voice sample...")
    # Create a dummy wav file
    with open("test_voice.wav", "wb") as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    
    files = {"voice_file": ("test_voice.wav", open("test_voice.wav", "rb"), "audio/wav")}
    resp = requests.post(f"{BASE_URL}/users/me/voice-sample", headers=headers, files=files)
    if resp.status_code != 200:
        print(f"Upload failed: {resp.text}")
        return
    
    updated_user = resp.json()
    print(f"Upload successful. Updated user: {updated_user}")
    print(f"Voice sample path: {updated_user.get('voice_sample_path')}")

    # 4. Verify file access
    path = updated_user.get('voice_sample_path')
    if path:
        file_url = f"http://127.0.0.1:8001/{path}"
        print(f"Trying to access file at: {file_url}")
        resp = requests.get(file_url)
        print(f"File access status: {resp.status_code}")
        if resp.status_code == 200:
            print("File access successful!")
        else:
            print("File access failed!")
    
    # Cleanup
    try:
        if os.path.exists("test_voice.wav"):
            os.remove("test_voice.wav")
    except Exception as e:
        print(f"Cleanup failed: {e}")

if __name__ == "__main__":
    reproduce()
