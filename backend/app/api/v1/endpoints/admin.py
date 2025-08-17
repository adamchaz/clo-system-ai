"""
Admin API Endpoints
Handles administrative functions including system statistics, user management, and alerts
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query  
from datetime import datetime, timedelta
from decimal import Decimal

# Import unified authentication dependencies
from app.core.unified_auth import require_admin_role, get_current_user

router = APIRouter()

@router.get("/test")
async def admin_test_endpoint():
    """Test endpoint without authentication to verify routing"""
    return {"message": "Admin routes are working", "timestamp": datetime.utcnow().isoformat()}

@router.get("/statistics")
async def get_system_statistics(
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Get comprehensive system statistics for admin dashboard
    
    Returns system metrics, user statistics, portfolio statistics, and performance data.
    Requires admin privileges.
    """
    try:
        # Mock system statistics - in production this would aggregate real data
        stats = {
            "system": {
                "uptime_hours": 72.5,
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "disk_usage": 34.1,
                "active_sessions": 12,
                "api_requests_today": 1547,
                "error_rate": 0.02,
                "response_time_avg": 245
            },
            "users": {
                "total_users": 25,
                "active_users": 23,
                "new_users_today": 2,
                "users_online": 8,
                "users_by_role": {
                    "admin": 3,
                    "manager": 8,
                    "analyst": 12,
                    "viewer": 2
                },
                "login_attempts_today": 89,
                "failed_logins_today": 3
            },
            "portfolios": {
                "total_portfolios": 3,
                "active_portfolios": 3,
                "total_assets": 195,
                "total_aum": float(Decimal("431160000.00")),
                "portfolios_by_status": {
                    "effective": 1,
                    "revolving": 1, 
                    "amortizing": 1
                },
                "average_deal_size": float(Decimal("143720000.00")),
                "total_market_value": float(Decimal("431160000.00"))
            },
            "alerts": {
                "total_alerts": 5,
                "critical_alerts": 1,
                "warning_alerts": 3,
                "info_alerts": 1,
                "acknowledged_alerts": 2,
                "unacknowledged_alerts": 3
            },
            "performance": {
                "database_queries_today": 2847,
                "cache_hit_rate": 94.2,
                "average_page_load": 1.8,
                "background_jobs_pending": 3,
                "background_jobs_completed": 127
            },
            "security": {
                "suspicious_activities": 0,
                "blocked_ips": 2,
                "password_resets_today": 1,
                "security_alerts": 0
            }
        }
        
        return {
            "data": stats,
            "message": "System statistics retrieved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system statistics: {str(e)}")

@router.get("/users")
async def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Get users for admin dashboard
    
    Returns paginated list of users with admin-specific information.
    """
    try:
        # Mock user data for admin dashboard
        users = [
            {
                "id": "admin_001",
                "email": "admin@clo-system.com",
                "full_name": "System Administrator",
                "role": "admin",
                "status": "active",
                "last_login": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat(),
                "login_count": 156,
                "is_online": True
            },
            {
                "id": "demo_001", 
                "email": "demo@clo-system.com",
                "full_name": "Demo User",
                "role": "viewer",
                "status": "active",
                "last_login": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                "login_count": 89,
                "is_online": True
            },
            {
                "id": "manager_001",
                "email": "manager@clo-system.com",
                "full_name": "Portfolio Manager",
                "role": "manager",
                "status": "active",
                "last_login": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=45)).isoformat(),
                "login_count": 134,
                "is_online": False
            },
            {
                "id": "analyst_001",
                "email": "analyst@clo-system.com", 
                "full_name": "Risk Analyst",
                "role": "analyst",
                "status": "active",
                "last_login": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "login_count": 67,
                "is_online": False
            },
            {
                "id": "viewer_001",
                "email": "viewer@clo-system.com",
                "full_name": "Report Viewer", 
                "role": "viewer",
                "status": "active",
                "last_login": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "login_count": 23,
                "is_online": False
            }
        ]
        
        # Apply filters
        filtered_users = users
        if role:
            filtered_users = [u for u in filtered_users if u["role"] == role]
        if status:
            filtered_users = [u for u in filtered_users if u["status"] == status]
        
        # Apply pagination
        total_count = len(filtered_users)
        paginated_users = filtered_users[skip:skip + limit]
        
        return {
            "data": paginated_users,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "message": f"Retrieved {len(paginated_users)} users successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

@router.get("/alerts")
async def get_admin_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    acknowledged: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Get system alerts for admin dashboard
    
    Returns system alerts, warnings, and notifications.
    """
    try:
        # Mock alert data
        alerts = [
            {
                "id": "alert_001",
                "title": "High Memory Usage",
                "message": "System memory usage has exceeded 90% threshold",
                "severity": "critical",
                "category": "system",
                "acknowledged": False,
                "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "acknowledged_at": None,
                "acknowledged_by": None
            },
            {
                "id": "alert_002", 
                "title": "Failed Login Attempts",
                "message": "Multiple failed login attempts detected from IP 192.168.1.50",
                "severity": "warning",
                "category": "security",
                "acknowledged": True,
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "acknowledged_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "acknowledged_by": "admin@clo-system.com"
            },
            {
                "id": "alert_003",
                "title": "Portfolio Compliance Warning", 
                "message": "CLO2014-001 approaching OC test limits",
                "severity": "warning",
                "category": "portfolio",
                "acknowledged": False,
                "created_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                "acknowledged_at": None,
                "acknowledged_by": None
            },
            {
                "id": "alert_004",
                "title": "Data Backup Completed",
                "message": "Scheduled database backup completed successfully",
                "severity": "info",
                "category": "system",
                "acknowledged": True,
                "created_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                "acknowledged_at": (datetime.utcnow() - timedelta(hours=7)).isoformat(),
                "acknowledged_by": "admin@clo-system.com"
            },
            {
                "id": "alert_005",
                "title": "New User Registration",
                "message": "New user analyst@clo-system.com requires approval",
                "severity": "warning",
                "category": "user_management",
                "acknowledged": False,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "acknowledged_at": None,
                "acknowledged_by": None
            }
        ]
        
        # Apply filters
        filtered_alerts = alerts
        if acknowledged is not None:
            filtered_alerts = [a for a in filtered_alerts if a["acknowledged"] == acknowledged]
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity]
        
        # Apply pagination
        total_count = len(filtered_alerts)
        paginated_alerts = filtered_alerts[skip:skip + limit]
        
        return {
            "data": paginated_alerts,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "message": f"Retrieved {len(paginated_alerts)} alerts successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Acknowledge a system alert
    """
    try:
        # Mock acknowledgment - in production would update database
        return {
            "message": f"Alert {alert_id} acknowledged successfully",
            "acknowledged_by": current_user.get("email", "admin"),
            "acknowledged_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/health")
async def get_system_health(
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Get detailed system health information
    """
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": {
                    "status": "healthy",
                    "response_time": 12,
                    "connections": 8,
                    "max_connections": 100
                },
                "redis": {
                    "status": "healthy", 
                    "response_time": 2,
                    "memory_usage": "45MB",
                    "connected_clients": 3
                },
                "background_jobs": {
                    "status": "healthy",
                    "pending_jobs": 3,
                    "processed_today": 127,
                    "failed_today": 2
                }
            },
            "metrics": {
                "uptime_seconds": 261000,
                "memory_usage_mb": 512,
                "cpu_usage_percent": 45.2,
                "disk_usage_percent": 34.1,
                "network_io_mb": 156.7
            }
        }
        
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system health: {str(e)}")