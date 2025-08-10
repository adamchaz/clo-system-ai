"""
Authentication API Endpoints
Handles user authentication, authorization, and session management
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....core.config import settings
from ....services.auth_service import AuthService
from ....schemas.auth import (
    Token,
    TokenData,
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordReset,
    PasswordResetRequest
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_auth_service():
    """Authentication service dependency"""
    return AuthService()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        user = auth_service.get_current_user(token)
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create new user
        new_user = auth_service.create_user(user)
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            role=new_user.role,
            created_at=new_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User registration failed: {str(e)}")

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token"""
    try:
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        updated_user = auth_service.update_user(
            user_id=current_user.id,
            updates=user_update.dict(exclude_unset=True)
        )
        
        return UserResponse(**updated_user.dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        # Verify current password
        if not auth_service.verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        
        # Update password
        auth_service.update_password(current_user.id, new_password)
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")

@router.post("/forgot-password")
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    try:
        # Generate password reset token
        reset_token = auth_service.create_password_reset_token(request.email)
        
        if reset_token:
            # In production, this would send an email
            # For now, return the token (NOT recommended for production)
            return {
                "message": "Password reset instructions sent to email",
                "reset_token": reset_token  # Remove this in production
            }
        else:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, password reset instructions have been sent"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset request failed: {str(e)}")

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password using reset token"""
    try:
        success = auth_service.reset_password_with_token(
            reset_data.reset_token,
            reset_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token"""
    try:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        new_token = auth_service.create_access_token(
            data={"sub": current_user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user (invalidate token)"""
    try:
        # In a more sophisticated system, we would blacklist the token
        # For now, just return success
        auth_service.record_logout(current_user.id)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user permissions and role-based access"""
    try:
        permissions = auth_service.get_user_permissions(current_user.id)
        
        return {
            "user_id": current_user.id,
            "role": current_user.role,
            "permissions": permissions,
            "can_manage_deals": "deal_management" in permissions,
            "can_view_risk_reports": "risk_analytics" in permissions,
            "can_run_calculations": "waterfall_calculations" in permissions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch permissions: {str(e)}")

@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user's active sessions"""
    try:
        sessions = auth_service.get_user_sessions(current_user.id)
        
        return {
            "user_id": current_user.id,
            "active_sessions": sessions,
            "session_count": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@router.post("/validate-token")
async def validate_token(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate access token without requiring authentication"""
    try:
        is_valid = auth_service.validate_token(token)
        
        return {
            "is_valid": is_valid,
            "token_type": "bearer" if is_valid else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token validation failed: {str(e)}")