#!/usr/bin/env python3
"""
Final authentication test with actual database user
"""

import sys
import requests
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService

def test_with_real_user():
    """Test authentication with real database user"""
    print("=== FINAL AUTHENTICATION TEST ===")
    
    auth_service = AuthService()
    
    print("1. Getting demo user from database...")
    user = auth_service.get_user_by_email("demo@clo-system.com")
    if user:
        print(f"   Found user: {user['email']} with role: {user['role']}")
    else:
        print("   ERROR: User not found in database!")
        return
    
    print("2. Creating token for database user...")
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": str(user["role"]),
        "permissions": ["read", "write", "admin"]
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"   Generated token: {token[:50]}...")
    
    print("3. Validating token...")
    user_from_token = auth_service.get_current_user(token)
    if user_from_token:
        print(f"   Token validation SUCCESS: {user_from_token['email']}")
    else:
        print("   ERROR: Token validation failed!")
        return
    
    print("4. Testing admin endpoints with valid token...")
    
    base_url = "http://localhost:8003/api/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/admin/test",
        "/admin/statistics", 
        "/admin/users",
        "/admin/alerts",
        "/admin/health"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            print(f"\\n   Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"     SUCCESS (200): Endpoint accessible")
                success_count += 1
            else:
                print(f"     FAILED ({response.status_code}): {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"     REQUEST ERROR: {e}")
    
    print(f"\\n=== RESULTS ===")
    print(f"Successful endpoints: {success_count}/{len(endpoints)}")
    if success_count == len(endpoints):
        print("🎉 ALL ADMIN ENDPOINTS WORKING WITH AUTHENTICATION!")
    else:
        print("⚠️  Some endpoints still failing")

if __name__ == "__main__":
    test_with_real_user()