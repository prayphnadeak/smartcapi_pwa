import requests
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"

def test_login_and_access():
    print("1. Attempting login as admincapi...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admincapi", "password": "supercapi"}
        )
        
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            return
            
        token = response.json()["access_token"]
        print(f"Login successful. Token: {token[:20]}...")
        
        print("\n2. Attempting to access protected endpoint (/interviews)...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/interviews", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Access successful! Retrieved {len(data)} interviews.")
        else:
            print(f"Access failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login_and_access()
