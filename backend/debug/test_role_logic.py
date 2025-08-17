#!/usr/bin/env python3
"""
Test the exact role logic used in unified_auth.py
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService
from app.schemas.auth import UserRole

def test_role_logic():
    """Test the exact logic from unified_auth.py"""
    print("=== TESTING ROLE LOGIC ===")
    
    auth_service = AuthService()
    
    # Get user and create token like in simple test
    user = auth_service.get_user_by_email("demo@clo-system.com")
    token_data = {
        "sub": user["email"],
        "user_id": user["id"], 
        "role": user["role"].value,  # "admin"
    }
    
    token = auth_service.create_access_token(token_data)
    current_user = auth_service.get_current_user(token)
    
    print(f"current_user from token: {current_user}")
    if current_user:
        print(f"Role in current_user: {current_user.get('role')}")
        print(f"Role type: {type(current_user.get('role'))}")
    
    # Now simulate the exact logic from require_admin_role
    print("\\n--- Simulating require_admin_role logic ---")
    
    user_role = current_user.get('role')
    print(f"1. user_role from current_user: {user_role} (type: {type(user_role)})")
    
    # If it's already a UserRole enum, use it directly
    if isinstance(user_role, UserRole):
        print("2. user_role is already UserRole enum, using directly")
    # Convert string role to UserRole if needed
    elif isinstance(user_role, str):
        print("2. user_role is string, attempting conversion...")
        try:
            # Handle both "ADMIN" and "UserRole.ADMIN" string formats
            if user_role.startswith('UserRole.'):
                role_name = user_role.split('.')[1]
                print(f"   Detected UserRole.X format, extracted: {role_name}")
            else:
                role_name = user_role
                print(f"   Using role_name as-is: {role_name}")
            user_role = UserRole(role_name.upper())
            print(f"   Converted to: {user_role}")
        except (ValueError, IndexError) as e:
            print(f"   Conversion failed: {e}")
            user_role = UserRole.VIEWER
            print(f"   Falling back to: {user_role}")
    else:
        print("2. user_role is unknown type, falling back to VIEWER")
        user_role = UserRole.VIEWER
    
    # Allow admin and manager roles for admin endpoints (for flexibility)
    result = user_role in [UserRole.ADMIN, UserRole.MANAGER]
    print(f"4. Final check: {user_role} in [UserRole.ADMIN, UserRole.MANAGER] = {result}")
    
    if result:
        print("\\nRESULT: Should have admin access")
    else:
        print("\\nRESULT: Should be denied admin access")

if __name__ == "__main__":
    test_role_logic()