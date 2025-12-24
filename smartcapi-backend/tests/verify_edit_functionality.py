import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def verify_edit(token, interview_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Payload simulating the frontend edit form
    payload = {
        "respondent_data": {
            "full_name": "Pray Putra Hasianro Nadeak (Edited)",
            "birth_year": 1995,
            "education": "S1",
            "address": "Jl. Test No. 123 (Edited)"
        },
        "extracted_data": {
            "nama": "Pray Putra Hasianro Nadeak (Edited)",
            "tempat_lahir": "Medan",
            "tanggal_lahir": "1995-01-01",
            "usia": "29",
            "pendidikan": "S1",
            "alamat": "Jl. Test No. 123 (Edited)",
            "pekerjaan": "Software Engineer",
            "hobi": "Coding",
            "nomor_telepon": "081234567890",
            "alamat_email": "pray@example.com"
        }
    }
    
    print(f"Updating interview {interview_id}...")
    response = requests.put(f"{BASE_URL}/interviews/{interview_id}", json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Update successful!")
        data = response.json()
        print("Updated Data:")
        print(json.dumps(data, indent=2))
        
        # Verify extracted answers
        extracted = data.get("extracted_answers", [])
        if extracted:
            print(f"Found {len(extracted)} extracted answers.")
            for ans in extracted:
                print(f"- {ans['question']['variable_name']}: {ans['answer_text']}")
        else:
            print("WARNING: No extracted answers returned in response.")
            
    else:
        print(f"Update failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    token = login("prayndk22", "password123") # Assuming this user exists and owns the interview
    if token:
        # Use ID 8 as seen in previous step
        verify_edit(token, 8)
