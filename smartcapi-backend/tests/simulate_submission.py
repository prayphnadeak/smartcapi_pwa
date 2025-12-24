import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://localhost:8001/api/v1"

def login(username, password):
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=payload, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: Status {response.status_code}, Response: {response.text}")
        return None

def create_interview(token, mode, respondent_name):
    url = f"{BASE_URL}/interviews/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "mode": mode,
        "respondent_data": {
            "full_name": respondent_name,
            "birth_year": 1990,
            "education": "S1",
            "address": "Test Address"
        },
        "duration": 120,
        "extracted_data": {
            "nama": respondent_name,
            "usia": 35
        }
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 200:
        print(f"✅ Created {mode} interview for {respondent_name}")
        return response.json()
    else:
        print(f"❌ Failed to create interview: {response.text}")
        return None

def get_interviews(token):
    url = f"{BASE_URL}/interviews/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to fetch interviews: {response.text}")
        return []

def main():
    # Login as admin (or enumerator if you prefer)
    token = login("admincapi", "supercapi")
    if not token:
        return

    # Create Manual Interview
    create_interview(token, "manual", "Manual Respondent Test")

    # Create AI Interview
    create_interview(token, "ai", "AI Respondent Test")

    # Fetch and Verify
    interviews = get_interviews(token)
    print(f"\n📊 Total Interviews Fetched: {len(interviews)}")
    
    manual_count = 0
    ai_count = 0
    
    for interview in interviews:
        print(f"- ID: {interview['id']}, Respondent: {interview['respondent_name']}, Mode: {interview['mode']}")
        if interview['mode'] == 'manual':
            manual_count += 1
        elif interview['mode'] == 'ai':
            ai_count += 1
            
    print(f"\nSummary:")
    print(f"Manual Interviews: {manual_count}")
    print(f"AI Interviews: {ai_count}")

if __name__ == "__main__":
    main()
