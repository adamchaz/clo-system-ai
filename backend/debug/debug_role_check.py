#!/usr/bin/env python3
"""
Debug role checking logic
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService
from app.schemas.auth import UserRole

def debug_role_check():
    """Debug role checking"""
    print("=== DEBUGGING ROLE CHECK ===")
    
    auth_service = AuthService()
    
    # Get user from database
    user = auth_service.get_user_by_email("demo@clo-system.com")
    if not user:
        print("ERROR: User not found")
        return
    
    print(f"1. User from database:")
    print(f"   Email: {user['email']}")
    print(f"   Role: {user['role']}")
    print(f"   Role type: {type(user['role'])}")
    print(f"   Role repr: {repr(user['role'])}")
    
    # Test role comparisons
    print(f"\\n2. Role comparisons:")
    print(f"   user['role'] == UserRole.ADMIN: {user['role'] == UserRole.ADMIN}")
    print(f"   user['role'] in [UserRole.ADMIN]: {user['role'] in [UserRole.ADMIN]}")
    print(f"   user['role'] in [UserRole.ADMIN, UserRole.MANAGER]: {user['role'] in [UserRole.ADMIN, UserRole.MANAGER]}")
    
    # Test string conversion
    print(f"\\n3. String conversions:")
    role_str = str(user['role'])
    print(f"   str(role): {role_str}")
    print(f"   str(role) type: {type(role_str)}")
    
    if isinstance(role_str, str):
        try:
            converted_role = UserRole(role_str.upper())
            print(f"   UserRole(str.upper()): {converted_role}")
            print(f"   Converted == UserRole.ADMIN: {converted_role == UserRole.ADMIN}")
        except ValueError as e:
            print(f"   UserRole conversion failed: {e}")
    
    # Test the exact logic from unified_auth.py
    print(f"\\n4. Unified auth logic simulation:")
    user_role = user.get('role')
    print(f"   Original user_role: {user_role} (type: {type(user_role)})")
    
    # Convert string role to UserRole if needed
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role.upper())
            print(f"   After string conversion: {user_role}")
        except ValueError:
            user_role = UserRole.VIEWER
            print(f"   Fallback to VIEWER: {user_role}")
    
    # Check admin privileges
    result = user_role in [UserRole.ADMIN, UserRole.MANAGER]
    print(f"   Final check - user_role in [ADMIN, MANAGER]: {result}")
    
    if result:
        print("   ✅ Should have admin access")
    else:
        print("   ❌ Should be denied admin access")

if __name__ == "__main__":
    debug_role_check()