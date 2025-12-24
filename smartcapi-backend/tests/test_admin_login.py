import requests

# Test admin login
url = "http://127.0.0.1:8000/api/v1/auth/login"
data = {
    "username": "admincapi",
    "password": "supercapi"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Login successful!")
        print(f"User: {result.get('user', {}).get('username')}")
        print(f"Role: {result.get('user', {}).get('role')}")
        print(f"Token: {result.get('access_token', '')[:50]}...")
    else:
        print(f"\n❌ Login failed")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

