#!/usr/bin/env python3

import requests
import json

def test_login_json(email, password, name):
    """Test login with JSON payload"""
    print(f"\n=== Testing {name} Login ===")
    print(f"Email: {email}")
    
    try:
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS! Token received")
            print(f"Token type: {data.get('token_type', 'N/A')}")
            token = data.get('access_token', '')
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"FAILED! Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_protected_endpoint(token, name):
    """Test access to protected endpoint"""
    print(f"\n=== Testing {name} Protected Access ===")
    
    if not token:
        print("No token to test with")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test user profile
        response = requests.get(
            "http://localhost:8000/api/v1/auth/me",
            headers=headers
        )
        
        print(f"User profile status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"User: {user_data.get('email')} | Role: {user_data.get('role')}")
        
        # Test admin endpoint
        response = requests.get(
            "http://localhost:8000/api/v1/admin/users",
            headers=headers
        )
        print(f"Admin users status: {response.status_code}")
        
        # Test portfolio stats
        response = requests.get(
            "http://localhost:8000/api/v1/portfolios/stats/overview",
            headers=headers
        )
        print(f"Portfolio stats status: {response.status_code}")
        
    except Exception as e:
        print(f"ERROR testing endpoints: {e}")

def main():
    print("=" * 50)
    print("CLO SYSTEM LOGIN TESTING")
    print("=" * 50)
    
    # Test both accounts
    accounts = [
        ("admin@clo-system.com", "admin123", "Admin Account"),
        ("demo@clo-system.com", "demo12345", "Demo Account")
    ]
    
    for email, password, name in accounts:
        token = test_login_json(email, password, name)
        test_protected_endpoint(token, name)
        print("-" * 30)

if __name__ == "__main__":
    main()