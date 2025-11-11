"""
Test script for Auth Service with API Key protection
Demonstrates how to make requests with API key authentication
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
API_KEY = "bankwesen-api-key-2024-secure-change-in-production"  # Change this to match your .env


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_login_without_api_key():
    """Test login without API key - should fail."""
    print_section("Test 1: Login WITHOUT API Key (Should Fail)")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": "student1",
        "password": "password123"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("Headers: (no API key)")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("\n✅ Correctly rejected - API key is required!")
        else:
            print("\n❌ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_with_invalid_api_key():
    """Test login with invalid API key - should fail."""
    print_section("Test 2: Login WITH Invalid API Key (Should Fail)")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": "student1",
        "password": "password123"
    }
    headers = {
        "X-API-Key": "wrong-api-key"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: X-API-Key: wrong-api-key")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 403:
            print("\n✅ Correctly rejected - Invalid API key!")
        else:
            print("\n❌ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_with_valid_api_key():
    """Test login with valid API key - should succeed."""
    print_section("Test 3: Login WITH Valid API Key (Should Succeed)")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": "student1",
        "password": "password123"
    }
    headers = {
        "X-API-Key": API_KEY
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: X-API-Key: {API_KEY[:30]}...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Login successful with valid API key!")
            token = response.json().get("access_token")
            return token
        else:
            print("\n❌ Login failed")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_verify_token(token: str):
    """Test token verification endpoint."""
    print_section("Test 4: Verify Token")
    
    url = f"{AUTH_URL}/verify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"GET {url}")
    print(f"Headers: Authorization: Bearer {token[:30]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Token is valid!")
        else:
            print("\n❌ Token verification failed")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  🔐 AUTH SERVICE API KEY TESTING")
    print("="*80)
    print(f"\n📍 Testing: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:30]}...")
    
    # Test 1: Without API key
    test_login_without_api_key()
    
    # Test 2: With invalid API key
    test_login_with_invalid_api_key()
    
    # Test 3: With valid API key
    token = test_login_with_valid_api_key()
    
    # Test 4: Verify token
    if token:
        test_verify_token(token)
    
    print("\n" + "="*80)
    print("  ✅ ALL TESTS COMPLETED")
    print("="*80)
    print("\n💡 To use the API from your frontend:")
    print(f"   Add header: X-API-Key: {API_KEY}")
    print("\n")


if __name__ == "__main__":
    main()
