"""
User Management Service
Business logic for user management, RBAC, and access control
"""

import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..core.database_config import get_db_session
from ..core.exceptions import CLOBusinessError, CLOValidationError
from ..core.security import hash_password, verify_password, create_access_token
from ..models.auth import User, UserRole  # Assuming these exist
from ..schemas.user_management import (
    UserCreateRequest, UserUpdateRequest, UserResponse,
    UserSearchRequest, UserListResponse, PasswordResetRequest,
    PasswordChangeRequest, UserStatsResponse, BulkUserOperation,
    BulkUserOperationResponse, UserPreferencesRequest, UserPreferencesResponse,
    UserStatus, Permission, RoleCreateRequest, RoleUpdateRequest, RoleResponse,
    UserPermissionResponse, UserSessionResponse, UserActivityResponse
)

logger = logging.getLogger(__name__)


class UserManagementService:
    """Service for user management operations"""
    
    def __init__(self):
        pass
    
    def create_user(self, request: UserCreateRequest, created_by: str) -> UserResponse:
        """Create a new user account"""
        try:
            with get_db_session() as session:
                # Check if username or email already exists
                existing_user = session.query(User).filter(
                    or_(User.username == request.username, User.email == request.email)
                ).first()
                
                if existing_user:
                    if existing_user.username == request.username:
                        raise CLOValidationError(f"Username '{request.username}' already exists")
                    else:
                        raise CLOValidationError(f"Email '{request.email}' already exists")
                
                # Generate user ID
                user_id = f"USER_{uuid.uuid4().hex[:12].upper()}"
                
                # Hash password
                password_hash = hash_password(request.password)
                
                # Create user record (mock structure - adjust based on actual User model)
                user_data = {
                    "user_id": user_id,
                    "username": request.username,
                    "email": request.email,
                    "password_hash": password_hash,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "role": request.role,
                    "organization": request.organization,
                    "department": request.department,
                    "phone": request.phone,
                    "title": request.title,
                    "manager_id": request.manager_id,
                    "cost_center": request.cost_center,
                    "location": request.location,
                    "timezone": request.timezone,
                    "language": request.language,
                    "status": UserStatus.ACTIVE if request.role != UserRole.VIEWER else UserStatus.PENDING_ACTIVATION,
                    "created_by": created_by,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Mock user creation (replace with actual User model instantiation)
                user = self._create_user_record(session, user_data)
                
                # Send welcome email if requested
                if request.send_welcome_email:
                    self._send_welcome_email(user)
                
                # Log user creation
                self._log_user_activity(session, user_id, "user_created", created_by)
                
                return self._build_user_response(user)
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to create user: {str(e)}")
            raise CLOBusinessError(f"User creation failed: {str(e)}") from e
    
    def get_user(self, user_id: str, requesting_user: str) -> UserResponse:
        """Get user by ID"""
        try:
            with get_db_session() as session:
                user = self._get_user_by_id(session, user_id)
                return self._build_user_response(user)
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to retrieve user: {str(e)}") from e
    
    def update_user(self, user_id: str, request: UserUpdateRequest, updated_by: str) -> UserResponse:
        """Update user information"""
        try:
            with get_db_session() as session:
                user = self._get_user_by_id(session, user_id)
                
                # Update fields
                update_fields = {}
                if request.email and request.email != user.get("email"):
                    # Check for email conflicts
                    existing = session.query(User).filter(
                        User.email == request.email,
                        User.user_id != user_id
                    ).first()
                    if existing:
                        raise CLOValidationError(f"Email '{request.email}' already exists")
                    update_fields["email"] = request.email
                
                # Update other fields
                field_mapping = {
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "role": request.role,
                    "organization": request.organization,
                    "department": request.department,
                    "phone": request.phone,
                    "title": request.title,
                    "manager_id": request.manager_id,
                    "cost_center": request.cost_center,
                    "location": request.location,
                    "timezone": request.timezone,
                    "language": request.language,
                    "status": request.status,
                    "email_notifications": request.email_notifications,
                    "two_factor_enabled": request.two_factor_enabled
                }
                
                for field, value in field_mapping.items():
                    if value is not None:
                        update_fields[field] = value
                
                if update_fields:
                    update_fields["updated_at"] = datetime.utcnow()
                    update_fields["updated_by"] = updated_by
                    
                    # Mock update (replace with actual User model update)
                    updated_user = self._update_user_record(session, user_id, update_fields)
                    
                    # Log user update
                    self._log_user_activity(session, user_id, "user_updated", updated_by, 
                                          details={"updated_fields": list(update_fields.keys())})
                    
                    return self._build_user_response(updated_user)
                
                return self._build_user_response(user)
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise CLOBusinessError(f"User update failed: {str(e)}") from e
    
    def delete_user(self, user_id: str, deleted_by: str) -> bool:
        """Delete user (soft delete)"""
        try:
            with get_db_session() as session:
                user = self._get_user_by_id(session, user_id)
                
                # Soft delete
                update_fields = {
                    "status": UserStatus.INACTIVE,
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": deleted_by,
                    "updated_at": datetime.utcnow()
                }
                
                self._update_user_record(session, user_id, update_fields)
                
                # Log user deletion
                self._log_user_activity(session, user_id, "user_deleted", deleted_by)
                
                return True
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise CLOBusinessError(f"User deletion failed: {str(e)}") from e
    
    def search_users(self, request: UserSearchRequest, requesting_user: str) -> UserListResponse:
        """Search users with filters"""
        try:
            with get_db_session() as session:
                # Mock search implementation
                users = self._perform_user_search(session, request)
                
                # Convert to response objects
                user_responses = [self._build_user_response(user) for user in users]
                
                # Mock total count
                total_count = len(user_responses) + request.skip
                
                return UserListResponse(
                    users=user_responses,
                    total_count=total_count,
                    skip=request.skip,
                    limit=request.limit,
                    has_more=(request.skip + len(user_responses)) < total_count
                )
                
        except Exception as e:
            logger.error(f"User search failed: {str(e)}")
            raise CLOBusinessError(f"User search failed: {str(e)}") from e
    
    def change_password(self, user_id: str, request: PasswordChangeRequest) -> bool:
        """Change user password"""
        try:
            if request.new_password != request.confirm_password:
                raise CLOValidationError("New password and confirmation do not match")
            
            with get_db_session() as session:
                user = self._get_user_by_id(session, user_id)
                
                # Verify current password
                if not verify_password(request.current_password, user.get("password_hash")):
                    raise CLOValidationError("Current password is incorrect")
                
                # Update password
                new_password_hash = hash_password(request.new_password)
                update_fields = {
                    "password_hash": new_password_hash,
                    "password_changed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                self._update_user_record(session, user_id, update_fields)
                
                # Log password change
                self._log_user_activity(session, user_id, "password_changed", user_id)
                
                return True
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Password change failed for user {user_id}: {str(e)}")
            raise CLOBusinessError(f"Password change failed: {str(e)}") from e
    
    def reset_password(self, request: PasswordResetRequest) -> bool:
        """Reset user password"""
        try:
            with get_db_session() as session:
                # Find user by email
                user = self._get_user_by_email(session, request.email)
                
                if not user:
                    # Don't reveal if email exists or not for security
                    logger.warning(f"Password reset requested for non-existent email: {request.email}")
                    return True
                
                # Generate reset token
                reset_token = self._generate_password_reset_token(user["user_id"])
                
                # Store reset token
                self._store_password_reset_token(session, user["user_id"], reset_token)
                
                # Send reset email
                self._send_password_reset_email(user, reset_token)
                
                # Log password reset request
                self._log_user_activity(session, user["user_id"], "password_reset_requested", "system")
                
                return True
                
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            # Don't expose internal errors for security
            return True
    
    def get_user_permissions(self, user_id: str, requesting_user: str) -> UserPermissionResponse:
        """Get user's effective permissions"""
        try:
            with get_db_session() as session:
                user = self._get_user_by_id(session, user_id)
                
                # Get role permissions
                role_permissions = self._get_role_permissions(session, user["role"])
                
                # Get direct permissions (if any)
                direct_permissions = self._get_user_direct_permissions(session, user_id)
                
                # Calculate effective permissions
                effective_permissions = self._calculate_effective_permissions(
                    role_permissions, direct_permissions
                )
                
                # Build permission summary
                permission_summary = self._build_permission_summary(effective_permissions)
                
                return UserPermissionResponse(
                    user_id=user_id,
                    effective_permissions=effective_permissions,
                    role_permissions=role_permissions,
                    direct_permissions=direct_permissions,
                    can_read=permission_summary["can_read"],
                    can_write=permission_summary["can_write"],
                    can_delete=permission_summary["can_delete"],
                    can_admin=permission_summary["can_admin"]
                )
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to get permissions for user {user_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to get user permissions: {str(e)}") from e
    
    def get_user_statistics(self, requesting_user: str) -> UserStatsResponse:
        """Get user management statistics"""
        try:
            with get_db_session() as session:
                # Mock statistics implementation
                stats = {
                    "total_users": 156,
                    "active_users": 142,
                    "by_role": {
                        "admin": 3,
                        "manager": 12,
                        "analyst": 89,
                        "viewer": 52
                    },
                    "by_status": {
                        "active": 142,
                        "inactive": 8,
                        "suspended": 4,
                        "pending_activation": 2
                    },
                    "by_organization": {
                        "Corporate": 89,
                        "Asset Management": 45,
                        "Risk Management": 22
                    },
                    "daily_active_users": 78,
                    "weekly_active_users": 134,
                    "monthly_active_users": 149
                }
                
                # Recent registrations and most active users would be queried from database
                recent_registrations = []
                most_active_users = []
                
                return UserStatsResponse(
                    total_users=stats["total_users"],
                    active_users=stats["active_users"],
                    by_role=stats["by_role"],
                    by_status=stats["by_status"],
                    by_organization=stats["by_organization"],
                    recent_registrations=recent_registrations,
                    most_active_users=most_active_users,
                    daily_active_users=stats["daily_active_users"],
                    weekly_active_users=stats["weekly_active_users"],
                    monthly_active_users=stats["monthly_active_users"]
                )
                
        except Exception as e:
            logger.error(f"Failed to get user statistics: {str(e)}")
            raise CLOBusinessError(f"Failed to get user statistics: {str(e)}") from e
    
    # Helper methods (mock implementations)
    def _get_user_by_id(self, session: Session, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        # Mock implementation
        if user_id.startswith("USER_"):
            return {
                "user_id": user_id,
                "username": f"user_{user_id[-4:].lower()}",
                "email": f"user_{user_id[-4:].lower()}@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": UserRole.ANALYST,
                "status": UserStatus.ACTIVE,
                "created_at": datetime.utcnow() - timedelta(days=30),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow() - timedelta(hours=2),
                "login_count": 45,
                "organization": "Corporate",
                "password_hash": "mock_hash"
            }
        else:
            raise CLOValidationError(f"User not found: {user_id}")
    
    def _get_user_by_email(self, session: Session, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        # Mock implementation
        if "@example.com" in email:
            return {
                "user_id": "USER_MOCK123",
                "email": email,
                "first_name": "John",
                "last_name": "Doe"
            }
        return None
    
    def _create_user_record(self, session: Session, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user record in database"""
        # Mock implementation
        return user_data
    
    def _update_user_record(self, session: Session, user_id: str, update_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update user record in database"""
        # Mock implementation
        user = self._get_user_by_id(session, user_id)
        user.update(update_fields)
        return user
    
    def _build_user_response(self, user: Dict[str, Any]) -> UserResponse:
        """Build user response object"""
        return UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            full_name=f"{user['first_name']} {user['last_name']}",
            role=user["role"],
            status=user.get("status", UserStatus.ACTIVE),
            organization=user.get("organization"),
            department=user.get("department"),
            title=user.get("title"),
            manager_id=user.get("manager_id"),
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            last_login=user.get("last_login"),
            login_count=user.get("login_count", 0),
            timezone=user.get("timezone", "UTC"),
            language=user.get("language", "en"),
            email_notifications=user.get("email_notifications", True),
            two_factor_enabled=user.get("two_factor_enabled", False),
            is_active=user.get("status") == UserStatus.ACTIVE,
            days_since_last_login=self._calculate_days_since_login(user.get("last_login"))
        )
    
    def _calculate_days_since_login(self, last_login: Optional[datetime]) -> Optional[int]:
        """Calculate days since last login"""
        if last_login:
            return (datetime.utcnow() - last_login).days
        return None
    
    def _perform_user_search(self, session: Session, request: UserSearchRequest) -> List[Dict[str, Any]]:
        """Perform user search"""
        # Mock implementation - return sample users
        users = []
        for i in range(min(request.limit, 10)):
            users.append({
                "user_id": f"USER_{i:03d}",
                "username": f"user{i:03d}",
                "email": f"user{i:03d}@example.com",
                "first_name": f"User",
                "last_name": f"{i:03d}",
                "role": UserRole.ANALYST,
                "status": UserStatus.ACTIVE,
                "created_at": datetime.utcnow() - timedelta(days=i),
                "updated_at": datetime.utcnow(),
                "organization": "Corporate"
            })
        return users
    
    def _log_user_activity(self, session: Session, user_id: str, action: str, performed_by: str, details: Optional[Dict[str, Any]] = None):
        """Log user activity"""
        # Mock implementation
        logger.info(f"User activity: {action} for {user_id} by {performed_by}")
    
    def _send_welcome_email(self, user: Dict[str, Any]):
        """Send welcome email to new user"""
        logger.info(f"Sending welcome email to {user['email']}")
    
    def _generate_password_reset_token(self, user_id: str) -> str:
        """Generate password reset token"""
        return f"RESET_{uuid.uuid4().hex}"
    
    def _store_password_reset_token(self, session: Session, user_id: str, token: str):
        """Store password reset token"""
        # Mock implementation
        logger.info(f"Storing reset token for user {user_id}")
    
    def _send_password_reset_email(self, user: Dict[str, Any], token: str):
        """Send password reset email"""
        logger.info(f"Sending password reset email to {user['email']}")
    
    def _get_role_permissions(self, session: Session, role: UserRole) -> List[Permission]:
        """Get permissions for role"""
        # Mock implementation
        return []
    
    def _get_user_direct_permissions(self, session: Session, user_id: str) -> List[Permission]:
        """Get direct permissions for user"""
        # Mock implementation
        return []
    
    def _calculate_effective_permissions(self, role_perms: List[Permission], direct_perms: List[Permission]) -> List[Permission]:
        """Calculate effective permissions"""
        # Mock implementation
        return role_perms + direct_perms
    
    def _build_permission_summary(self, permissions: List[Permission]) -> Dict[str, List[str]]:
        """Build permission summary"""
        # Mock implementation
        return {
            "can_read": ["portfolio", "asset", "report"],
            "can_write": ["portfolio", "asset"],
            "can_delete": [],
            "can_admin": []
        }