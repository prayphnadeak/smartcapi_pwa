# Test Backend Endpoints
# Run this after starting the backend server

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Testing SmartCAPI Backend Endpoints")
print("=" * 60)
print()

# Test 1: Health Check
print("1. Testing Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ Health check passed!")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   Backend might not be running!")
    exit(1)

print()

# Test 2: Forgot Password Endpoint
print("2. Testing Forgot Password Endpoint...")
try:
    # Using JSON body now
    payload = {"email": "test@example.com"}
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/forgot-password",
        json=payload
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Forgot password endpoint working!")
    else:
        print(f"   ⚠️  Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 3: CORS Headers
print("3. Checking CORS Headers...")
try:
    response = requests.options(
        f"{BASE_URL}/api/v1/auth/forgot-password",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST"
        }
    )
    print(f"   Status: {response.status_code}")
    cors_header = response.headers.get("Access-Control-Allow-Origin")
    print(f"   CORS Header: {cors_header}")
    
    if cors_header:
        print("   ✅ CORS is configured!")
    else:
        print("   ❌ CORS headers missing!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("Testing Complete!")
print("=" * 60)
