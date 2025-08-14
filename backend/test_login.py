#!/usr/bin/env python3
"""
Test login functionality for the CLO Management System
"""

import requests
import json

def test_login():
    """Test different login approaches"""
    
    base_url = "http://localhost:8000"
    
    # Test credentials to try
    credentials = [
        {"username": "admin@clo-system.com", "password": "admin123"},
        {"username": "demo@clo-system.com", "password": "demo12345"}, 
        {"username": "test@clo-system.com", "password": "password123"},
        {"username": "demo@example.com", "password": "demo12345"},
    ]
    
    print("=== Testing Login Endpoints ===\n")
    
    for i, cred in enumerate(credentials, 1):
        print(f"{i}. Testing: {cred['username']}")
        
        # Try token endpoint (OAuth2 format)
        try:
            response = requests.post(
                f"{base_url}/api/v1/auth/token",
                data={"username": cred["username"], "password": cred["password"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"   Token endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
                print(f"   Role: {data.get('user', {}).get('role', 'N/A')}")
                return cred
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
    
    print("❌ No working credentials found")
    return None

if __name__ == "__main__":
    working_creds = test_login()
    
    if working_creds:
        print("\n🎉 WORKING LOGIN CREDENTIALS:")
        print(f"   Email: {working_creds['username']}")  
        print(f"   Password: {working_creds['password']}")
        print(f"   URL: http://localhost:3001")
    else:
        print("\n⚠️  No working credentials found. Backend authentication needs fixing.")