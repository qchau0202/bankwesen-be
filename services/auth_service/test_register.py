"""
Test script for User Registration
Tests the /register endpoint with various scenarios
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
API_KEY = "bankwesen-api-key-2024-secure-change-in-production"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_response(response: requests.Response):
    """Print formatted response."""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_register_success():
    """Test successful user registration."""
    print_section("Test 1: Successful Registration")
    
    url = f"{AUTH_URL}/register"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {
        "username": f"testuser_{timestamp}",
        "password": "securePassword123",
        "confirm_password": "securePassword123",
        "full_name": "Test User",
        "email": f"testuser_{timestamp}@example.com",
        "phone_number": "1234567890"
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print_response(response)
        
        if response.status_code == 201:
            print("\n✅ Registration successful!")
            return response.json()
        else:
            print("\n❌ Registration failed")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_register_password_mismatch():
    """Test registration with mismatched passwords."""
    print_section("Test 2: Registration with Password Mismatch")
    
    url = f"{AUTH_URL}/register"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {
        "username": f"testuser_{timestamp}",
        "password": "password123",
        "confirm_password": "different_password",
        "full_name": "Test User",
        "email": f"testuser_{timestamp}@example.com",
        "phone_number": "1234567890"
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print_response(response)
        
        if response.status_code == 400:
            print("\n✅ Correctly rejected - passwords don't match!")
        else:
            print("\n❌ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_register_duplicate_username():
    """Test registration with existing username."""
    print_section("Test 3: Registration with Duplicate Username")
    
    url = f"{AUTH_URL}/register"
    payload = {
        "username": "student1",  # Existing user
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "Test User",
        "email": "newemail@example.com",
        "phone_number": "1234567890"
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print_response(response)
        
        if response.status_code == 409:
            print("\n✅ Correctly rejected - username already exists!")
        else:
            print("\n❌ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_register_without_api_key():
    """Test registration without API key."""
    print_section("Test 4: Registration without API Key")
    
    url = f"{AUTH_URL}/register"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    payload = {
        "username": f"testuser_{timestamp}",
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "Test User",
        "email": f"testuser_{timestamp}@example.com",
        "phone_number": "1234567890"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("Headers: (no API key)")
    
    try:
        response = requests.post(url, json=payload)
        print_response(response)
        
        if response.status_code == 401:
            print("\n✅ Correctly rejected - API key required!")
        else:
            print("\n❌ Unexpected response")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_with_new_user(username: str, password: str):
    """Test login with newly registered user."""
    print_section(f"Test 5: Login with New User ({username})")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Login successful with new credentials!")
            return True
        else:
            print("\n❌ Login failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all registration tests."""
    print("\n" + "="*80)
    print("  🔐 USER REGISTRATION TESTING")
    print("="*80)
    print(f"\n📍 Testing: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:30]}...")
    
    # Test 1: Successful registration
    result = test_register_success()
    
    # Test 2: Password mismatch
    test_register_password_mismatch()
    
    # Test 3: Duplicate username
    test_register_duplicate_username()
    
    # Test 4: Without API key
    test_register_without_api_key()
    
    # Test 5: Login with newly created user
    if result and "user_info" in result:
        username = result["user_info"]["username"]
        test_login_with_new_user(username, "securePassword123")
    
    print("\n" + "="*80)
    print("  ✅ ALL REGISTRATION TESTS COMPLETED")
    print("="*80)
    print("\n💡 Registration endpoint usage:")
    print(f"   POST {AUTH_URL}/register")
    print(f"   Header: X-API-Key: {API_KEY}")
    print("""   Body: {
     "username": "newuser",
     "password": "password123",
     "confirm_password": "password123",
     "full_name": "Full Name",
     "email": "email@example.com",
     "phone_number": "1234567890"
   }""")
    print("\n")


if __name__ == "__main__":
    main()
