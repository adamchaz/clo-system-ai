"""
User Management Schemas
Pydantic models for user management and RBAC API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

from ..models.auth import UserRole  # Assuming this exists


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"
    LOCKED = "locked"


class PermissionScope(str, Enum):
    """Permission scope levels"""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PORTFOLIO = "portfolio"
    ASSET = "asset"


class ActionType(str, Enum):
    """Action types for permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    ADMIN = "admin"


class UserCreateRequest(BaseModel):
    """Schema for creating new users"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    
    # Profile information
    title: Optional[str] = None
    manager_id: Optional[str] = None
    cost_center: Optional[str] = None
    location: Optional[str] = None
    
    # Initial settings
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")
    send_welcome_email: bool = Field(default=True)


class UserUpdateRequest(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    manager_id: Optional[str] = None
    cost_center: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    status: Optional[UserStatus] = None
    
    # Settings
    email_notifications: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user API responses"""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    status: UserStatus
    
    # Organization information
    organization: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    manager_id: Optional[str] = None
    
    # Account information
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    # Settings
    timezone: str = "UTC"
    language: str = "en"
    email_notifications: bool = True
    two_factor_enabled: bool = False
    
    # Computed fields
    is_active: bool
    days_since_last_login: Optional[int] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list responses"""
    users: List[UserResponse]
    total_count: int
    skip: int
    limit: int
    has_more: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self.has_more = (self.skip + len(self.users)) < self.total_count


class UserSearchRequest(BaseModel):
    """Schema for user search requests"""
    query: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests"""
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class Permission(BaseModel):
    """Individual permission definition"""
    permission_id: str
    name: str
    description: str
    scope: PermissionScope
    action: ActionType
    resource_type: str  # portfolio, asset, report, etc.
    resource_id: Optional[str] = None  # Specific resource ID if applicable


class RoleBase(BaseModel):
    """Base role model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_system_role: bool = False
    is_active: bool = True


class RoleCreateRequest(RoleBase):
    """Schema for creating roles"""
    permissions: List[str] = Field(default_factory=list, description="List of permission IDs")


class RoleUpdateRequest(BaseModel):
    """Schema for updating roles"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Schema for role API responses"""
    role_id: str
    created_at: datetime
    updated_at: datetime
    user_count: int = 0  # Number of users with this role
    permissions: List[Permission] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class UserPermissionResponse(BaseModel):
    """Schema for user permission responses"""
    user_id: str
    effective_permissions: List[Permission]
    role_permissions: List[Permission]
    direct_permissions: List[Permission]  # Permissions assigned directly to user
    
    # Permission summary
    can_read: List[str] = Field(default_factory=list)  # Resource types user can read
    can_write: List[str] = Field(default_factory=list)  # Resource types user can write
    can_delete: List[str] = Field(default_factory=list)  # Resource types user can delete
    can_admin: List[str] = Field(default_factory=list)  # Resource types user can admin


class UserSessionResponse(BaseModel):
    """Schema for user session information"""
    user_id: str
    session_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_current: bool
    expires_at: datetime


class UserActivityResponse(BaseModel):
    """Schema for user activity responses"""
    activity_id: str
    user_id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class UserStatsResponse(BaseModel):
    """Schema for user statistics"""
    total_users: int
    active_users: int
    by_role: Dict[str, int]
    by_status: Dict[str, int]
    by_organization: Dict[str, int]
    
    # Activity statistics
    recent_registrations: List[UserResponse] = Field(default_factory=list)
    most_active_users: List[UserResponse] = Field(default_factory=list)
    
    # Login statistics
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int


class BulkUserOperation(BaseModel):
    """Schema for bulk user operations"""
    user_ids: List[str] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern="^(activate|deactivate|suspend|delete|unlock)$")
    parameters: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class BulkUserOperationResponse(BaseModel):
    """Schema for bulk user operation responses"""
    total_requested: int
    successful: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    processed_user_ids: List[str] = Field(default_factory=list)


class UserPreferencesRequest(BaseModel):
    """Schema for user preferences updates"""
    theme: Optional[str] = Field(default="light", pattern="^(light|dark|auto)$")
    language: Optional[str] = Field(default="en")
    timezone: Optional[str] = Field(default="UTC")
    date_format: Optional[str] = Field(default="MM/DD/YYYY")
    number_format: Optional[str] = Field(default="US")
    
    # Notification preferences
    email_notifications: Optional[bool] = True
    desktop_notifications: Optional[bool] = True
    notification_frequency: Optional[str] = Field(default="real-time", pattern="^(real-time|daily|weekly|never)$")
    
    # Dashboard preferences
    dashboard_layout: Optional[Dict[str, Any]] = None
    default_portfolio: Optional[str] = None
    favorite_reports: Optional[List[str]] = Field(default_factory=list)


class UserPreferencesResponse(UserPreferencesRequest):
    """Schema for user preferences responses"""
    user_id: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    """Schema for organization information"""
    organization_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    user_count: int = 0
    active_user_count: int = 0
    
    # Settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class AccessControlRequest(BaseModel):
    """Schema for access control rule requests"""
    user_id: str
    resource_type: str
    resource_id: str
    permissions: List[ActionType]
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


class AccessControlResponse(BaseModel):
    """Schema for access control responses"""
    rule_id: str
    user_id: str
    resource_type: str
    resource_id: str
    permissions: List[ActionType]
    granted_at: datetime
    granted_by: str
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True