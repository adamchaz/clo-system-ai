#!/usr/bin/env python3

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_login(email, password, user_type):
    """Test user login and return access token"""
    print(f"\n=== Testing {user_type} Login ===")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    try:
        # Test login
        login_data = {
            "username": email,  # FastAPI OAuth2 uses 'username' field
            "password": password
        }
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            data=login_data,  # Form data for OAuth2
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"Login successful!")
            print(f"Token Type: {token_data.get('token_type', 'N/A')}")
            print(f"Access Token: {token_data.get('access_token', '')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"Login failed!")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_protected_endpoints(token, user_type):
    """Test access to protected endpoints"""
    print(f"\n=== Testing {user_type} API Access ===")
    
    if not token:
        print("❌ No token available for testing")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints based on user type
    endpoints_to_test = [
        ("/auth/me", "User Profile", "all"),
        ("/portfolios/", "Portfolios List", "all"),
        ("/portfolios/stats/overview", "Portfolio Stats", "all"),
        ("/admin/users", "Admin Users", "admin"),
        ("/admin/statistics", "Admin Statistics", "admin"),
        ("/admin/alerts", "Admin Alerts", "admin")
    ]
    
    for endpoint, name, required_role in endpoints_to_test:
        if required_role == "admin" and "admin" not in user_type.lower():
            print(f"⏭️  Skipping {name} (admin only)")
            continue
            
        try:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {name}: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")

def test_user_info(token, user_type):
    """Get detailed user information"""
    print(f"\n=== {user_type} Account Details ===")
    
    if not token:
        print("❌ No token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User Info Retrieved:")
            print(f"   User ID: {user_data.get('user_id', 'N/A')}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            print(f"   Role: {user_data.get('role', 'N/A')}")
            print(f"   Name: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
            print(f"   Active: {user_data.get('is_active', 'N/A')}")
        else:
            print(f"❌ Failed to get user info: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error getting user info: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("CLO SYSTEM USER ACCOUNT TESTING")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test accounts
    accounts = [
        ("admin@clo-system.com", "admin123", "Admin Account"),
        ("demo@clo-system.com", "demo12345", "Demo Account")
    ]
    
    results = {}
    
    for email, password, user_type in accounts:
        # Test login
        token = test_login(email, password, user_type)
        results[user_type] = {
            "login_success": token is not None,
            "token": token
        }
        
        # Test user info
        test_user_info(token, user_type)
        
        # Test API endpoints
        test_protected_endpoints(token, user_type)
        
        print("-" * 40)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TESTING SUMMARY")
    print("=" * 60)
    
    for user_type, result in results.items():
        status = "✅ PASS" if result["login_success"] else "❌ FAIL"
        print(f"{user_type}: {status}")
    
    print(f"\nTesting completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()