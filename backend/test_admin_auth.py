#!/usr/bin/env python3
"""
Test script to generate JWT token and test admin endpoints
"""

import sys
import requests
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService
from app.schemas.auth import UserRole

def create_test_token():
    """Create a test JWT token for admin user"""
    print("Creating test JWT token...")
    
    auth_service = AuthService()
    
    # Create token for admin user
    token_data = {
        "sub": "admin@clo-system.com",  # subject (user email)
        "user_id": "admin_001",
        "role": UserRole.ADMIN,
        "permissions": ["read", "write", "admin"]
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"Generated token: {token[:50]}...")
    
    return token

def test_admin_endpoints(token):
    """Test admin endpoints with authentication"""
    print("\nTesting admin endpoints...")
    
    base_url = "http://localhost:8003/api/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test endpoints
    endpoints = [
        "/admin/test",
        "/admin/statistics", 
        "/admin/users",
        "/admin/alerts",
        "/admin/health"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {str(data)[:100]}...")
            else:
                print(f"  Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"  Request failed: {e}")

if __name__ == "__main__":
    print("CLO System Admin Authentication Test\n")
    
    try:
        # Generate test token
        token = create_test_token()
        
        # Test endpoints
        test_admin_endpoints(token)
        
        print("\n=== AUTHENTICATION TEST COMPLETE ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()