#!/usr/bin/env python3
"""
Simple authentication test
"""

import sys
import requests
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService

def simple_test():
    """Simple authentication test"""
    print("=== SIMPLE AUTHENTICATION TEST ===")
    
    auth_service = AuthService()
    
    # Get user
    user = auth_service.get_user_by_email("demo@clo-system.com")
    if not user:
        print("ERROR: User not found")
        return
    
    print(f"User: {user['email']}")
    print(f"Role: {user['role']}")
    print(f"Role value: {user['role'].value}")  # Get the enum value
    
    # Create token with correct role value
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": user["role"].value,  # Use .value to get "admin" not "UserRole.ADMIN"
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"Token created: {token[:50]}...")
    
    # Test token validation
    user_from_token = auth_service.get_current_user(token)
    if user_from_token:
        print(f"Token valid for: {user_from_token['email']}")
    else:
        print("ERROR: Token validation failed")
        return
    
    # Test endpoint
    print("\\nTesting /admin/statistics endpoint...")
    try:
        response = requests.get(
            "http://localhost:8003/api/v1/admin/statistics",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Admin endpoint accessible!")
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
        else:
            print(f"FAILED: {response.text}")
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    simple_test()