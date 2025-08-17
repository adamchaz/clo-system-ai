#!/usr/bin/env python3
"""
Test authentication for demo viewer and other viewer users
"""

import sys
import requests
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService

def test_user_access(email, role_name):
    """Test endpoint access for a specific user"""
    print(f"\n=== TESTING {role_name.upper()} USER: {email} ===")
    
    auth_service = AuthService()
    
    # Get user from database
    print("1. Getting user from database...")
    user = auth_service.get_user_by_email(email)
    if not user:
        print(f"   ERROR: User {email} not found!")
        return
    
    print(f"   Found: {user['email']} (Role: {user['role']})")
    
    # Create token directly (bypass password auth due to bcrypt issue)
    print("2. Creating authentication token...")
    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "role": user["role"].value,
        "permissions": ["deal_viewing", "basic_analytics"] if user["role"].value == "viewer" else ["deal_management", "user_management", "system_configuration"]
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"   Generated token: {token[:50]}...")
    
    # Test token validation
    print("3. Validating token...")
    user_from_token = auth_service.get_current_user(token)
    if not user_from_token:
        print("   ERROR: Token validation failed!")
        return
    
    print(f"   SUCCESS: Token valid for {user_from_token['email']} ({user_from_token['role']})")
    
    # Test endpoints
    print("4. Testing endpoint access...")
    
    base_url = "http://localhost:8003/api/v1"
    headers = {"Authorization": f"Bearer {token}"}
    
    test_endpoints = [
        ("/test", "Public test endpoint"),
        ("/monitoring/health", "System health"),
        ("/portfolios/", "List CLO deals"),
        ("/assets/", "List assets"),
        ("/admin/statistics", "Admin statistics"),
        ("/admin/users", "Admin user management"),
        ("/auth/me", "Current user profile"),
    ]
    
    results = {"accessible": [], "forbidden": [], "errors": []}
    
    for endpoint, description in test_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                results["accessible"].append(f"{endpoint} - {description}")
                print(f"   ✓ SUCCESS (200): {description}")
            elif response.status_code == 403:
                results["forbidden"].append(f"{endpoint} - {description}")
                print(f"   ✗ FORBIDDEN (403): {description}")
            elif response.status_code == 401:
                results["errors"].append(f"{endpoint} - 401 Unauthorized")
                print(f"   ! UNAUTHORIZED (401): {description}")
            else:
                results["errors"].append(f"{endpoint} - {response.status_code}")
                print(f"   ? OTHER ({response.status_code}): {description}")
                
        except Exception as e:
            results["errors"].append(f"{endpoint} - Connection Error")
            print(f"   ! ERROR: {e}")
    
    # Summary
    print(f"\n   SUMMARY for {role_name.upper()}:")
    print(f"   - Accessible: {len(results['accessible'])}")
    print(f"   - Forbidden: {len(results['forbidden'])}")
    print(f"   - Errors: {len(results['errors'])}")
    
    return results

def main():
    """Test both users and compare access"""
    print("=== COMPREHENSIVE USER AUTHENTICATION TEST ===")
    
    # Test viewer user (demo account)
    demo_results = test_user_access("demo@clo-system.com", "viewer")
    
    # Test viewer user  
    viewer_results = test_user_access("viewer@clo-system.com", "viewer")
    
    if demo_results and viewer_results:
        print(f"\n=== COMPARISON SUMMARY ===")
        print(f"DEMO VIEWER USER (demo@clo-system.com):")
        print(f"  - Can access: {len(demo_results['accessible'])} endpoints")
        print(f"  - Forbidden from: {len(demo_results['forbidden'])} endpoints")
        
        print(f"\nVIEWER USER (viewer@clo-system.com):")
        print(f"  - Can access: {len(viewer_results['accessible'])} endpoints")
        print(f"  - Forbidden from: {len(viewer_results['forbidden'])} endpoints")
        
        # Find differences
        demo_accessible = set(demo_results['accessible'])
        viewer_accessible = set(viewer_results['accessible'])
        
        demo_only = demo_accessible - viewer_accessible
        viewer_only = viewer_accessible - demo_accessible
        
        if demo_only:
            print(f"\nDEMO-ONLY ACCESS:")
            for endpoint in demo_only:
                print(f"  - {endpoint}")
        
        if viewer_only:
            print(f"\nOTHER VIEWER-ONLY ACCESS:")
            for endpoint in viewer_only:
                print(f"  - {endpoint}")
        
        if not demo_only and not viewer_only:
            print(f"\nBOTH USERS HAVE IDENTICAL ACCESS PATTERNS")

if __name__ == "__main__":
    main()