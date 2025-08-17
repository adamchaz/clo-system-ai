#!/usr/bin/env python3
"""
Test authentication for demo@clo-system.com user
"""

import sys
import requests
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService

def test_demo_user_authentication():
    """Test authentication and endpoint access for demo@clo-system.com"""
    print("=== DEMO USER AUTHENTICATION TEST ===")
    
    auth_service = AuthService()
    
    print("1. Getting demo user from database...")
    user = auth_service.get_user_by_email("demo@clo-system.com")
    if user:
        print(f"   Found user: {user['email']}")
        print(f"   Role: {user['role']}")
        print(f"   Active: {user.get('is_active', 'Unknown')}")
        print(f"   Created: {user.get('created_at', 'Unknown')}")
    else:
        print("   ERROR: User not found in database!")
        return

    print("\n2. Creating authentication token...")
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": user["role"].value,  # Use .value to get string representation
        "permissions": ["deal_viewing", "basic_analytics"]
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"   Generated token: {token[:50]}...")
    
    print("\n3. Validating token...")
    user_from_token = auth_service.get_current_user(token)
    if user_from_token:
        print(f"   Token validation SUCCESS")
        print(f"   User from token: {user_from_token['email']}")
        print(f"   Role from token: {user_from_token['role']}")
    else:
        print("   ERROR: Token validation failed!")
        return
    
    print("\n4. Testing endpoint access with authentication...")
    
    base_url = "http://localhost:8003/api/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test various endpoint categories
    test_endpoints = [
        # Public endpoints (should work)
        ("/test", "Public test endpoint"),
        ("/monitoring/health", "System health"),
        
        # Portfolio endpoints (viewers should access)
        ("/portfolios/", "List CLO deals"),
        
        # Asset endpoints (viewers should access) 
        ("/assets/", "List assets"),
        
        # Admin endpoints (should fail for non-admin users)
        ("/admin/statistics", "Admin statistics"),
        ("/admin/users", "Admin users"),
        
        # Auth endpoints (should work)
        ("/auth/me", "Current user profile"),
    ]
    
    results = {"success": [], "failed": [], "total": len(test_endpoints)}
    
    for endpoint, description in test_endpoints:
        try:
            print(f"\n   Testing {endpoint} ({description})...")
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"     SUCCESS (200): {description}")
                results["success"].append(f"{endpoint} - {description}")
            elif response.status_code == 403:
                print(f"     FORBIDDEN (403): {description} - Access denied for user role")
                results["failed"].append(f"{endpoint} - 403 Forbidden")
            elif response.status_code == 401:
                print(f"     UNAUTHORIZED (401): {description} - Authentication issue")
                results["failed"].append(f"{endpoint} - 401 Unauthorized")
            elif response.status_code == 404:
                print(f"     NOT FOUND (404): {description} - Endpoint not found")
                results["failed"].append(f"{endpoint} - 404 Not Found")
            else:
                print(f"     OTHER ({response.status_code}): {description}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    print(f"       Detail: {error_detail}")
                except:
                    print(f"       Response: {response.text[:100]}")
                results["failed"].append(f"{endpoint} - {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"     REQUEST ERROR: {e}")
            results["failed"].append(f"{endpoint} - Connection Error")
    
    print(f"\n=== RESULTS ===")
    print(f"User: {user['email']} (Role: {user['role']})")
    print(f"Successful endpoints: {len(results['success'])}/{results['total']}")
    print(f"Failed endpoints: {len(results['failed'])}/{results['total']}")
    
    if results["success"]:
        print(f"\nSUCCESSFUL ENDPOINTS:")
        for endpoint in results["success"]:
            print(f"  ✅ {endpoint}")
    
    if results["failed"]:
        print(f"\nFAILED ENDPOINTS:")
        for endpoint in results["failed"]:
            print(f"  ❌ {endpoint}")
    
    # Test password authentication
    print(f"\n5. Testing password authentication...")
    try:
        authenticated_user = auth_service.authenticate_user("demo@clo-system.com", "demo123")
        if authenticated_user:
            print(f"   Password authentication SUCCESS for {authenticated_user['email']}")
        else:
            print(f"   Password authentication FAILED")
    except Exception as e:
        print(f"   Password authentication ERROR: {e}")

if __name__ == "__main__":
    test_demo_user_authentication()