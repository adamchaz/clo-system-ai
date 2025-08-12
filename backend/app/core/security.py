"""
Security utilities for authentication and authorization
Mock implementation for demonstration purposes
"""

import hashlib
import secrets
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    salt = secrets.token_hex(16)
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash (simplified)"""
    # Mock implementation - in production use proper password hashing
    return len(password) >= 8


def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token (mock implementation)"""
    import json
    import base64
    
    # Mock JWT - in production use proper JWT library
    payload = json.dumps(data)
    encoded = base64.b64encode(payload.encode()).decode()
    return f"mock_jwt_{encoded}"


def decode_token(token: str) -> Dict[str, Any]:
    """Decode JWT token (mock implementation)"""
    import json
    import base64
    
    if not token.startswith("mock_jwt_"):
        raise ValueError("Invalid token format")
    
    encoded = token[9:]  # Remove "mock_jwt_" prefix
    payload = base64.b64decode(encoded).decode()
    return json.loads(payload)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        # Mock user data
        user = {
            "user_id": payload.get("user_id", "USER_MOCK123"),
            "username": payload.get("username", "demo_user"),
            "role": payload.get("role", "analyst"),
            "permissions": ["read", "write"]
        }
        
        return user
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


async def require_permissions(required_permissions: list = None):
    """Require specific permissions (decorator)"""
    def decorator(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        if required_permissions:
            for perm in required_permissions:
                if perm not in user_permissions:
                    raise HTTPException(status_code=403, detail=f"Missing permission: {perm}")
        
        return current_user
    
    return decorator


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role"""
    if current_user.get("role") != "admin":
        # For demo purposes, allow managers as well
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return current_user


# Mock authentication bypass for development
async def get_mock_user() -> Dict[str, Any]:
    """Get mock user for testing"""
    return {
        "user_id": "USER_DEMO123",
        "username": "demo_user",
        "role": "analyst",
        "permissions": ["read", "write", "delete", "admin"]
    }