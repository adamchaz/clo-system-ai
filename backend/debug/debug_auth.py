#!/usr/bin/env python3
"""
Debug authentication system
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.auth_service import AuthService
from app.core.unified_auth import get_auth_service
from app.schemas.auth import UserRole

def test_token_generation_and_validation():
    """Test token generation and validation"""
    print("=== DEBUGGING AUTHENTICATION ===")
    
    # Test AuthService directly
    auth_service = AuthService()
    
    print("1. Testing AuthService token generation...")
    token_data = {
        "sub": "admin@clo-system.com",
        "user_id": "admin_001",
        "role": UserRole.ADMIN.value,
        "permissions": ["read", "write", "admin"]
    }
    
    token = auth_service.create_access_token(token_data)
    print(f"   Generated token: {token[:50]}...")
    
    print("2. Testing token validation...")
    try:
        is_valid = auth_service.validate_token(token)
        print(f"   Token valid: {is_valid}")
    except Exception as e:
        print(f"   Token validation error: {e}")
    
    print("3. Testing get_current_user...")
    try:
        user = auth_service.get_current_user(token)
        print(f"   User from token: {user}")
    except Exception as e:
        print(f"   get_current_user error: {e}")
    
    print("4. Testing unified auth service...")
    try:
        unified_auth_service = get_auth_service()
        print(f"   Unified auth service: {unified_auth_service}")
        print(f"   Same instance: {unified_auth_service is auth_service}")
    except Exception as e:
        print(f"   Unified auth service error: {e}")
    
    # Test with actual user from database
    print("5. Testing with database user...")
    try:
        db_user = auth_service.get_user_by_email("admin@clo-system.com")
        print(f"   Database user: {db_user}")
        
        if db_user:
            # Create token for actual database user
            db_token_data = {
                "sub": db_user["email"],
                "user_id": db_user["id"],
                "role": db_user["role"].value if hasattr(db_user["role"], 'value') else str(db_user["role"]),
                "permissions": ["read", "write", "admin"]
            }
            
            db_token = auth_service.create_access_token(db_token_data)
            print(f"   DB token: {db_token[:50]}...")
            
            # Validate DB token
            db_user_from_token = auth_service.get_current_user(db_token)
            print(f"   DB user from token: {db_user_from_token}")
            
    except Exception as e:
        print(f"   Database user test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_token_generation_and_validation()