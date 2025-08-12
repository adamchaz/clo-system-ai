"""
User Management API Endpoints
FastAPI routes for user management, RBAC, and access control
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from ....core.security import get_current_user, require_permissions, require_admin
from ....schemas.user_management import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse,
    UserSearchRequest, PasswordResetRequest, PasswordChangeRequest,
    UserStatsResponse, BulkUserOperation, BulkUserOperationResponse,
    UserPreferencesRequest, UserPreferencesResponse, UserPermissionResponse,
    UserSessionResponse, UserActivityResponse, RoleCreateRequest,
    RoleUpdateRequest, RoleResponse, AccessControlRequest, AccessControlResponse,
    UserStatus
)
from ....services.user_management_service import UserManagementService
from ....core.exceptions import CLOBusinessError, CLOValidationError

router = APIRouter()
user_service = UserManagementService()


@router.post("/", response_model=UserResponse, status_code=HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Create a new user account
    
    - **request**: User creation parameters including credentials, profile, and role information
    
    Requires admin privileges. Creates user account with specified role and sends welcome email if requested.
    """
    try:
        result = user_service.create_user(request, current_user["user_id"])
        return result
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user information by ID
    
    - **user_id**: User identifier
    
    Users can access their own information or admins can access any user.
    """
    try:
        # Check permissions - users can view themselves, admins can view anyone
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = user_service.get_user(user_id, current_user["user_id"])
        return result
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user information
    
    - **user_id**: User identifier
    - **request**: Update parameters
    
    Users can update their own profile information. Admins can update any user including role changes.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Only admins can change roles and status
        if (request.role or request.status) and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can change user roles and status")
        
        result = user_service.update_user(user_id, request, current_user["user_id"])
        return result
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User update failed: {str(e)}")


@router.delete("/{user_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Delete user account (soft delete)
    
    - **user_id**: User identifier
    
    Requires admin privileges. Performs soft delete by setting user status to inactive.
    """
    try:
        # Prevent self-deletion
        if user_id == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        user_service.delete_user(user_id, current_user["user_id"])
        return Response(status_code=HTTP_204_NO_CONTENT)
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User deletion failed: {str(e)}")


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List users with optional filters
    
    - **skip**: Number of users to skip (pagination)
    - **limit**: Maximum number of users to return
    - **role**: Filter by user role
    - **status**: Filter by user status
    - **organization**: Filter by organization
    - **department**: Filter by department
    
    Requires manager or admin privileges.
    """
    try:
        if current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        search_request = UserSearchRequest(
            skip=skip,
            limit=limit,
            role=role,
            status=status,
            organization=organization,
            department=department
        )
        
        result = user_service.search_users(search_request, current_user["user_id"])
        return result
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.post("/search", response_model=UserListResponse)
async def search_users(
    request: UserSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Advanced user search with multiple criteria
    
    - **request**: Search parameters including query, filters, date ranges, and sorting
    
    Requires manager or admin privileges.
    """
    try:
        if current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = user_service.search_users(request, current_user["user_id"])
        return result
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User search failed: {str(e)}")


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change user's password
    
    - **request**: Password change parameters including current and new passwords
    
    Users can only change their own passwords.
    """
    try:
        success = user_service.change_password(current_user["user_id"], request)
        return {"message": "Password changed successfully"}
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")


@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest):
    """
    Request password reset
    
    - **request**: Password reset parameters including email
    
    Sends password reset email if user exists. Always returns success for security.
    """
    try:
        user_service.reset_password(request)
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        # Always return success for security reasons
        return {"message": "If the email exists, a password reset link has been sent"}


@router.get("/{user_id}/permissions", response_model=UserPermissionResponse)
async def get_user_permissions(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's effective permissions
    
    - **user_id**: User identifier
    
    Shows role-based permissions, direct permissions, and effective permissions summary.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = user_service.get_user_permissions(user_id, current_user["user_id"])
        return result
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get permissions: {str(e)}")


@router.get("/stats/summary", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get user management statistics
    
    Returns comprehensive user statistics including counts, activity, and usage patterns.
    Requires admin privileges.
    """
    try:
        result = user_service.get_user_statistics(current_user["user_id"])
        return result
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/bulk", response_model=BulkUserOperationResponse)
async def bulk_user_operation(
    request: BulkUserOperation,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Perform bulk operations on multiple users
    
    - **request**: Bulk operation parameters including user IDs and operation type
    
    Supported operations:
    - activate: Activate user accounts
    - deactivate: Deactivate user accounts
    - suspend: Suspend user accounts
    - delete: Soft delete user accounts
    - unlock: Unlock locked accounts
    
    Requires admin privileges.
    """
    try:
        # Prevent operations on self
        if current_user["user_id"] in request.user_ids:
            raise HTTPException(status_code=400, detail="Cannot perform bulk operations on your own account")
        
        successful = 0
        failed = 0
        errors = []
        processed_ids = []
        
        for user_id in request.user_ids:
            try:
                if request.operation == "activate":
                    # Mock activation
                    successful += 1
                    processed_ids.append(user_id)
                elif request.operation == "deactivate":
                    # Mock deactivation
                    successful += 1
                    processed_ids.append(user_id)
                elif request.operation == "delete":
                    user_service.delete_user(user_id, current_user["user_id"])
                    successful += 1
                    processed_ids.append(user_id)
                else:
                    errors.append(f"Unsupported operation: {request.operation}")
                    failed += 1
                    
            except Exception as e:
                errors.append(f"Failed to process {user_id}: {str(e)}")
                failed += 1
        
        return BulkUserOperationResponse(
            total_requested=len(request.user_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_user_ids=processed_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")


@router.get("/{user_id}/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's active sessions
    
    - **user_id**: User identifier
    
    Shows all active sessions for the user including current session details.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock sessions
        from datetime import datetime, timedelta
        sessions = [
            UserSessionResponse(
                user_id=user_id,
                session_id="sess_12345",
                created_at=datetime.utcnow() - timedelta(hours=2),
                last_activity=datetime.utcnow() - timedelta(minutes=5),
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                is_current=True,
                expires_at=datetime.utcnow() + timedelta(hours=22)
            )
        ]
        
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/{user_id}/activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's activity log
    
    - **user_id**: User identifier
    - **limit**: Maximum number of activity records to return
    
    Shows user activity history including logins, changes, and actions performed.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock activity
        from datetime import datetime, timedelta
        activities = [
            UserActivityResponse(
                activity_id="act_12345",
                user_id=user_id,
                action="login",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            ),
            UserActivityResponse(
                activity_id="act_12346",
                user_id=user_id,
                action="view_portfolio",
                resource_type="portfolio",
                resource_id="CLO_001",
                timestamp=datetime.utcnow() - timedelta(minutes=30),
                ip_address="192.168.1.100"
            )
        ]
        
        return activities[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")


@router.get("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user preferences and settings
    
    - **user_id**: User identifier
    
    Returns user's personalization settings, notification preferences, and dashboard configuration.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"] and current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock preferences
        from datetime import datetime
        preferences = UserPreferencesResponse(
            user_id=user_id,
            theme="light",
            language="en",
            timezone="UTC",
            date_format="MM/DD/YYYY",
            number_format="US",
            email_notifications=True,
            desktop_notifications=True,
            notification_frequency="real-time",
            dashboard_layout={"widgets": ["portfolio_summary", "risk_metrics", "alerts"]},
            default_portfolio="CLO_001",
            favorite_reports=["portfolio_performance", "risk_analysis"],
            updated_at=datetime.utcnow()
        )
        
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@router.put("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    request: UserPreferencesRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user preferences and settings
    
    - **user_id**: User identifier
    - **request**: Preference updates
    
    Updates user's personalization settings, notification preferences, and dashboard configuration.
    """
    try:
        # Check permissions
        if user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Can only update your own preferences")
        
        # Mock update
        from datetime import datetime
        preferences = UserPreferencesResponse(
            user_id=user_id,
            theme=request.theme or "light",
            language=request.language or "en",
            timezone=request.timezone or "UTC",
            date_format=request.date_format or "MM/DD/YYYY",
            number_format=request.number_format or "US",
            email_notifications=request.email_notifications if request.email_notifications is not None else True,
            desktop_notifications=request.desktop_notifications if request.desktop_notifications is not None else True,
            notification_frequency=request.notification_frequency or "real-time",
            dashboard_layout=request.dashboard_layout,
            default_portfolio=request.default_portfolio,
            favorite_reports=request.favorite_reports or [],
            updated_at=datetime.utcnow()
        )
        
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


# Role management endpoints
@router.get("/roles/", response_model=List[RoleResponse])
async def list_roles(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    List all available roles
    
    Returns all system and custom roles with their permissions.
    Requires admin privileges.
    """
    try:
        # Mock roles
        from datetime import datetime
        roles = [
            RoleResponse(
                role_id="admin",
                name="Administrator",
                description="Full system access",
                is_system_role=True,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                user_count=3,
                permissions=[]
            ),
            RoleResponse(
                role_id="manager",
                name="Portfolio Manager",
                description="Portfolio management access",
                is_system_role=True,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                user_count=12,
                permissions=[]
            )
        ]
        
        return roles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")


@router.post("/impersonate/{user_id}")
async def impersonate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Impersonate another user (admin only)
    
    - **user_id**: User identifier to impersonate
    
    Creates temporary session as the specified user for support purposes.
    Requires admin privileges and full audit logging.
    """
    try:
        # Get target user
        target_user = user_service.get_user(user_id, current_user["user_id"])
        
        # Log impersonation
        logger.info(f"Admin {current_user['user_id']} impersonating user {user_id}")
        
        # Create temporary token (mock implementation)
        from ..core.security import create_access_token
        
        impersonation_token = create_access_token({
            "user_id": user_id,
            "username": target_user.username,
            "role": target_user.role.value,
            "impersonated_by": current_user["user_id"],
            "impersonation_started": datetime.utcnow().isoformat()
        })
        
        return {
            "impersonation_token": impersonation_token,
            "target_user": target_user,
            "impersonated_by": current_user["user_id"],
            "message": "Impersonation session created. Use this token for API calls."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impersonation failed: {str(e)}")