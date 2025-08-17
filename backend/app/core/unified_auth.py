"""
Unified Authentication System for CLO Management System
Provides standardized authentication dependencies using the existing AuthService
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from ..services.auth_service import AuthService
from ..schemas.auth import UserRole

logger = logging.getLogger(__name__)

# Initialize security scheme and auth service
security = HTTPBearer()
auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User data dictionary
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Ensure user is active
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current active user (alias for backward compatibility)
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User data dictionary
    """
    return current_user

async def require_role(required_role: UserRole):
    """
    Create a dependency that requires a specific user role
    
    Args:
        required_role: Required user role
        
    Returns:
        FastAPI dependency function
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get('role')
        
        # Convert string role to UserRole if needed
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role.upper())
            except ValueError:
                user_role = UserRole.VIEWER
        
        # Check if user has required role or higher
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2, 
            UserRole.MANAGER: 3,
            UserRole.ADMIN: 4
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 4)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. {required_role.value} role or higher required."
            )
        
        return current_user
    
    return role_checker

async def require_admin_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require admin role for access
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User data if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    user_role = current_user.get('role')
    
    # If it's already a UserRole enum, use it directly
    if isinstance(user_role, UserRole):
        pass  # Already correct type
    # Convert string role to UserRole if needed
    elif isinstance(user_role, str):
        try:
            # Handle both "ADMIN" and "UserRole.ADMIN" string formats
            if user_role.startswith('UserRole.'):
                role_name = user_role.split('.')[1]
            else:
                role_name = user_role
            user_role = UserRole(role_name.upper())
        except (ValueError, IndexError):
            user_role = UserRole.VIEWER
    else:
        # Unknown type, fallback to VIEWER
        user_role = UserRole.VIEWER
    
    # Allow admin and manager roles for admin endpoints (for flexibility)
    if user_role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def require_manager_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require manager role or higher for access
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User data if user is manager or admin
        
    Raises:
        HTTPException: If user is not manager or admin
    """
    user_role = current_user.get('role')
    
    # Convert string role to UserRole if needed
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role.upper())
        except ValueError:
            user_role = UserRole.VIEWER
    
    if user_role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager privileges required"
        )
    
    return current_user

async def require_analyst_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require analyst role or higher for access
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User data if user is analyst, manager, or admin
        
    Raises:
        HTTPException: If user is only viewer
    """
    user_role = current_user.get('role')
    
    # Convert string role to UserRole if needed
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role.upper())
        except ValueError:
            user_role = UserRole.VIEWER
    
    if user_role not in [UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst privileges required"
        )
    
    return current_user

def require_permissions(required_permissions: list):
    """
    Create a dependency that requires specific permissions
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        FastAPI dependency function
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_id = current_user.get('id')
        user_permissions = auth_service.get_user_permissions(user_id)
        
        # Check if user has all required permissions
        missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Get current user if token is provided, otherwise return None
    Useful for endpoints that work with or without authentication
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        User data if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        
        # Only return user if active
        if user and user.get('is_active', True):
            return user
        
        return None
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None

# Token validation utilities
async def validate_token(token: str) -> bool:
    """
    Validate a JWT token without returning user data
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is valid, False otherwise
    """
    return auth_service.validate_token(token)

def get_auth_service() -> AuthService:
    """
    Get the authentication service instance
    
    Returns:
        AuthService instance
    """
    return auth_service

# Export commonly used dependencies for easy import
__all__ = [
    'get_current_user',
    'get_current_active_user', 
    'require_admin_role',
    'require_manager_role',
    'require_analyst_role',
    'require_role',
    'require_permissions',
    'get_optional_user',
    'validate_token',
    'get_auth_service'
]