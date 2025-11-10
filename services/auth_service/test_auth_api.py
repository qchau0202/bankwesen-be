"""
Test script for Authentication API
Tests login, token verification, and role-based access control
"""

import requests
import json
from typing import Optional

# API base URL
BASE_URL = "http://localhost:8001"  # Update port if different
AUTH_URL = f"{BASE_URL}/api/v1/auth"


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


def test_login(username: str, password: str) -> Optional[str]:
    """Test login endpoint and return access token if successful."""
    print_section(f"Testing Login - {username}")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print_response(response)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"\n✅ Login successful!")
            print(f"🔑 Access Token: {token[:50]}...")
            return token
        else:
            print(f"\n❌ Login failed!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_get_current_user(token: str):
    """Test getting current user info."""
    print_section("Testing Get Current User Info")
    
    url = f"{AUTH_URL}/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"GET {url}")
    print(f"Headers: Authorization: Bearer {token[:30]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Successfully retrieved user info")
        else:
            print("\n❌ Failed to retrieve user info")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_verify_token(token: str):
    """Test token verification."""
    print_section("Testing Token Verification")
    
    url = f"{AUTH_URL}/verify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"GET {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Token is valid")
        else:
            print("\n❌ Token is invalid")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_admin_endpoint(token: str, role: str):
    """Test admin-only endpoint."""
    print_section(f"Testing Admin Endpoint (as {role})")
    
    url = f"{AUTH_URL}/admin/users"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"GET {url}")
    print(f"Expected: {'✅ Success' if role == 'admin' else '❌ Forbidden'}")
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Admin access granted")
        elif response.status_code == 403:
            print("\n⛔ Access denied (as expected for non-admin users)")
        else:
            print(f"\n❌ Unexpected status code")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_staff_endpoint(token: str, role: str):
    """Test staff endpoint."""
    print_section(f"Testing Staff Endpoint (as {role})")
    
    url = f"{AUTH_URL}/staff/dashboard"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"GET {url}")
    print(f"Expected: {'✅ Success' if role in ['admin', 'staff'] else '❌ Forbidden'}")
    
    try:
        response = requests.get(url, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Staff access granted")
        elif response.status_code == 403:
            print("\n⛔ Access denied (as expected for students)")
        else:
            print(f"\n❌ Unexpected status code")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_invalid_credentials():
    """Test login with invalid credentials."""
    print_section("Testing Invalid Credentials")
    
    url = f"{AUTH_URL}/login"
    payload = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("Expected: ❌ 401 Unauthorized")
    
    try:
        response = requests.post(url, json=payload)
        print_response(response)
        
        if response.status_code == 401:
            print("\n✅ Correctly rejected invalid credentials")
        else:
            print("\n❌ Unexpected status code")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_no_token():
    """Test accessing protected endpoint without token."""
    print_section("Testing Access Without Token")
    
    url = f"{AUTH_URL}/me"
    
    print(f"GET {url}")
    print("Expected: ❌ 403 Forbidden (no token provided)")
    
    try:
        response = requests.get(url)
        print_response(response)
        
        if response.status_code == 403:
            print("\n✅ Correctly rejected request without token")
        else:
            print("\n❌ Unexpected status code")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("\n" + "🔐"*40)
    print("  AUTHENTICATION API TEST SUITE")
    print("🔐"*40)
    
    # Test 1: Invalid credentials
    test_invalid_credentials()
    
    # Test 2: No token
    test_no_token()
    
    # Test 3: Student login and access
    print("\n" + "📚"*40)
    print("  STUDENT USER TESTS")
    print("📚"*40)
    student_token = test_login("student1", "password123")
    if student_token:
        test_get_current_user(student_token)
        test_verify_token(student_token)
        test_staff_endpoint(student_token, "student")  # Should fail
        test_admin_endpoint(student_token, "student")  # Should fail
    
    # Test 4: Staff login and access
    print("\n" + "👔"*40)
    print("  STAFF USER TESTS")
    print("👔"*40)
    staff_token = test_login("staff1", "staff123")
    if staff_token:
        test_get_current_user(staff_token)
        test_verify_token(staff_token)
        test_staff_endpoint(staff_token, "staff")  # Should succeed
        test_admin_endpoint(staff_token, "staff")  # Should fail
    
    # Test 5: Admin login and access
    print("\n" + "🔐"*40)
    print("  ADMIN USER TESTS")
    print("🔐"*40)
    admin_token = test_login("admin", "admin123")
    if admin_token:
        test_get_current_user(admin_token)
        test_verify_token(admin_token)
        test_staff_endpoint(admin_token, "admin")  # Should succeed
        test_admin_endpoint(admin_token, "admin")  # Should succeed
    
    print("\n" + "="*80)
    print("  TEST SUITE COMPLETED")
    print("="*80)
    print("\n✅ All tests executed. Review the results above.\n")


if __name__ == "__main__":
    main()
