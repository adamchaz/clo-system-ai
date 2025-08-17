#!/usr/bin/env python3
"""
Create a viewer user for testing different role access
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, UserRole

def create_viewer_user():
    """Create a viewer user for testing"""
    print("=== CREATING VIEWER USER ===")
    
    auth_service = AuthService()
    
    # Check if viewer user already exists
    existing_user = auth_service.get_user_by_email("viewer@clo-system.com")
    if existing_user:
        print(f"Viewer user already exists: {existing_user['email']} (Role: {existing_user['role']})")
        return existing_user
    
    # Create viewer user
    print("Creating new viewer user...")
    try:
        viewer_user = UserCreate(
            email="viewer@clo-system.com",
            password="viewer123",
            full_name="Demo Viewer",
            role=UserRole.VIEWER
        )
        
        user = auth_service.create_user(viewer_user)
        print(f"Viewer user created successfully: {user}")
        return user
        
    except Exception as e:
        print(f"Failed to create viewer user: {e}")
        return None

def test_viewer_authentication():
    """Test viewer authentication and compare with admin access"""
    print("\n=== TESTING VIEWER AUTHENTICATION ===")
    
    # Create viewer user first
    viewer_user = create_viewer_user()
    if not viewer_user:
        return
    
    auth_service = AuthService()
    
    # Test password authentication
    print("\n1. Testing viewer password authentication...")
    try:
        authenticated_user = auth_service.authenticate_user("viewer@clo-system.com", "viewer123")
        if authenticated_user:
            print(f"   SUCCESS: Viewer authenticated as {authenticated_user['email']}")
            print(f"   Role: {authenticated_user['role']}")
        else:
            print(f"   FAILED: Viewer authentication failed")
            return
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Create token for viewer
    print("\n2. Creating token for viewer...")
    token_data = {
        "sub": authenticated_user["email"],
        "user_id": authenticated_user["id"],
        "role": authenticated_user["role"].value,
        "permissions": ["deal_viewing", "basic_analytics"]
    }
    
    viewer_token = auth_service.create_access_token(token_data)
    print(f"   Generated viewer token: {viewer_token[:50]}...")
    
    # Test token validation
    print("\n3. Validating viewer token...")
    user_from_token = auth_service.get_current_user(viewer_token)
    if user_from_token:
        print(f"   Token validation SUCCESS")
        print(f"   User: {user_from_token['email']}")
        print(f"   Role: {user_from_token['role']}")
    else:
        print(f"   Token validation FAILED")
        return
    
    # Quick endpoint test - just admin endpoints to see difference
    print(f"\n4. Testing admin endpoint access (should fail for viewer)...")
    import requests
    
    base_url = "http://localhost:8003/api/v1"
    headers = {"Authorization": f"Bearer {viewer_token}"}
    
    admin_endpoints = [
        ("/admin/statistics", "Admin statistics"),
        ("/admin/users", "Admin user management"),
        ("/portfolios/", "Portfolio access (should work)"),
        ("/assets/", "Asset access (should work)"),
    ]
    
    for endpoint, description in admin_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   SUCCESS (200): {description}")
            elif response.status_code == 403:
                print(f"   FORBIDDEN (403): {description} - Access denied (expected for admin endpoints)")
            elif response.status_code == 401:
                print(f"   UNAUTHORIZED (401): {description} - Auth issue")
            else:
                print(f"   OTHER ({response.status_code}): {description}")
                
        except Exception as e:
            print(f"   ERROR testing {endpoint}: {e}")

if __name__ == "__main__":
    test_viewer_authentication()