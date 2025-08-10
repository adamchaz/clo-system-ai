"""
Authentication Schemas
Pydantic models for authentication-related API requests and responses
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    """Schema for user creation"""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    role: UserRole = UserRole.VIEWER
    
class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user API responses"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        from_attributes = True

class User(UserBase):
    """Internal user model with sensitive fields"""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: Optional[dict] = None

class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[UserRole] = None
    expires_at: Optional[datetime] = None

class PasswordResetRequest(BaseModel):
    """Schema for password reset requests"""
    email: EmailStr = Field(..., description="Email address for password reset")

class PasswordReset(BaseModel):
    """Schema for password reset with token"""
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class UserPermissions(BaseModel):
    """Schema for user permissions"""
    user_id: str
    role: UserRole
    permissions: List[str]
    
    # Specific capabilities
    can_create_deals: bool = False
    can_modify_deals: bool = False
    can_delete_deals: bool = False
    can_run_calculations: bool = False
    can_view_risk_reports: bool = False
    can_manage_users: bool = False
    can_configure_system: bool = False

class UserSession(BaseModel):
    """Schema for user session information"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True

class LoginAttempt(BaseModel):
    """Schema for login attempt tracking"""
    email: str
    ip_address: Optional[str] = None
    success: bool
    attempted_at: datetime
    failure_reason: Optional[str] = None

class AuthAuditLog(BaseModel):
    """Schema for authentication audit logs"""
    user_id: Optional[str] = None
    action: str  # login, logout, password_change, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    details: Optional[dict] = None
    timestamp: datetime

class RolePermissionMap(BaseModel):
    """Schema for role-permission mapping"""
    role: UserRole
    permissions: List[str]
    description: str
    
    # Default role permissions
    @classmethod
    def get_default_permissions(cls, role: UserRole) -> List[str]:
        """Get default permissions for a role"""
        role_permissions = {
            UserRole.ADMIN: [
                "deal_management", "user_management", "system_configuration",
                "risk_analytics", "waterfall_calculations", "scenario_analysis",
                "audit_logs", "data_export"
            ],
            UserRole.MANAGER: [
                "deal_management", "risk_analytics", "waterfall_calculations",
                "scenario_analysis", "data_export"
            ],
            UserRole.ANALYST: [
                "risk_analytics", "waterfall_calculations", "scenario_analysis",
                "deal_viewing"
            ],
            UserRole.VIEWER: [
                "deal_viewing", "basic_analytics"
            ]
        }
        return role_permissions.get(role, [])

class TokenValidationResponse(BaseModel):
    """Schema for token validation response"""
    is_valid: bool
    token_type: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    permissions: Optional[List[str]] = None

class AuthStats(BaseModel):
    """Schema for authentication statistics"""
    total_users: int
    active_users: int
    users_by_role: dict
    recent_logins: int
    failed_login_attempts: int
    password_resets_today: int
    
    # Session statistics
    active_sessions: int
    average_session_duration: Optional[float] = None  # minutes

class SecuritySettings(BaseModel):
    """Schema for security configuration"""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = False
    password_expiry_days: Optional[int] = None
    
    # Session settings
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    
    # Security features
    enable_two_factor: bool = False
    enable_login_rate_limiting: bool = True
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15