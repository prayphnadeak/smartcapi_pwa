import requests

# Test the /users endpoint
print("Testing GET /api/v1/users endpoint...")
print("=" * 60)

# First login as admin
login_response = requests.post(
    "http://127.0.0.1:8001/api/v1/auth/login",
    data={"username": "admincapi", "password": "supercapi"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print("✅ Admin login successful\n")
    
    # Test GET /users
    headers = {"Authorization": f"Bearer {token}"}
    users_response = requests.get("http://127.0.0.1:8001/api/v1/users/", headers=headers)
    
    print(f"Status Code: {users_response.status_code}")
    print(f"Response:\n{users_response.text[:500]}")
    
    if users_response.status_code == 200:
        users = users_response.json()
        print(f"\n✅ API returned {len(users)} users:")
        for user in users:
            print(f"   - {user.get('username')} (ID: {user.get('id')}, Email: {user.get('email')})")
    else:
        print(f"❌ Error: {users_response.status_code}")
else:
    print(f"❌ Login failed: {login_response.status_code}")
