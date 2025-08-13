"""
Production Monitoring API Endpoints  
Handles system health, performance metrics, readiness/liveness checks, and operational monitoring
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....core.monitoring import health_checker, StructuredLogger
from ....core.security import rate_limit_moderate, rate_limit_lenient
from ....services.monitoring_service import MonitoringService
from ....schemas.monitoring import (
    SystemHealthResponse,
    PerformanceMetricsResponse,
    DatabaseStatsResponse,
    AlertResponse,
    AlertCreate
)
from ..endpoints.auth import get_current_active_user
from ....schemas.auth import User

# Initialize structured logger
logger = StructuredLogger("monitoring_api")

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_monitoring_service():
    """Monitoring service dependency"""
    return MonitoringService()

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get comprehensive system health status"""
    try:
        health_status = monitoring_service.get_system_health()
        
        return SystemHealthResponse(**health_status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/health/database")
async def get_database_health():
    """Get database connection health status"""
    try:
        health_status = db_config.health_check()
        
        overall_status = "healthy"
        if not health_status.get('postgresql', False):
            overall_status = "unhealthy"
        elif not health_status.get('redis', False):
            overall_status = "degraded"  # Redis is optional
        
        return {
            "status": overall_status,
            "postgresql": {
                "status": "connected" if health_status.get('postgresql', False) else "disconnected",
                "response_time_ms": health_status.get('postgresql_response_time', 0)
            },
            "redis": {
                "status": "connected" if health_status.get('redis', False) else "disconnected",
                "response_time_ms": health_status.get('redis_response_time', 0)
            },
            "migration_databases": health_status.get('migration_databases', {}),
            "last_checked": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}")


# ==== PRODUCTION HEALTH ENDPOINTS ====

@router.get("/health/live")
@rate_limit_lenient()
async def liveness_check(request: Request):
    """
    Liveness probe - checks if application is alive
    Used by Kubernetes/container orchestrators
    """
    try:
        result = health_checker.check_liveness()
        logger.info("Liveness check performed", client_ip=request.client.host, **result)
        return result
    except Exception as e:
        logger.error("Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/ready") 
@rate_limit_lenient()
async def readiness_check(request: Request):
    """
    Readiness probe - checks if application is ready to serve requests
    Used by Kubernetes/container orchestrators and load balancers
    """
    try:
        result = health_checker.check_readiness()
        
        if result["ready"]:
            logger.info("Readiness check passed", client_ip=request.client.host, **result)
            return result
        else:
            logger.warning("Readiness check failed", client_ip=request.client.host, **result)
            raise HTTPException(status_code=503, detail="Service not ready")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check error", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/detailed")
@rate_limit_moderate()
async def detailed_health_check(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Comprehensive health check with system metrics
    Requires authentication - for operational monitoring
    """
    try:
        result = health_checker.check_health(detailed=True)
        
        logger.info("Detailed health check performed", 
                   user_id=current_user.get("user_id"),
                   client_ip=request.client.host,
                   status=result.get("status"))
        
        return result
        
    except Exception as e:
        logger.error("Detailed health check failed", 
                    user_id=current_user.get("user_id"), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/metrics/system")
@rate_limit_moderate()
async def get_system_metrics(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed system performance metrics
    Requires authentication - for system administrators
    """
    try:
        from ....core.monitoring import SystemMonitor
        
        metrics = {
            "system": SystemMonitor.get_system_stats(),
            "databases": SystemMonitor.get_database_health(), 
            "application": SystemMonitor.get_application_metrics()
        }
        
        logger.info("System metrics requested",
                   user_id=current_user.get("user_id"),
                   client_ip=request.client.host)
        
        return metrics
        
    except Exception as e:
        logger.error("System metrics failed",
                    user_id=current_user.get("user_id"),
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to collect system metrics")

@router.get("/metrics/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    time_range: str = Query("1h", regex="^(5m|15m|1h|6h|24h|7d)$"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get system performance metrics"""
    try:
        metrics = monitoring_service.get_performance_metrics(time_range)
        
        return PerformanceMetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}")

@router.get("/metrics/database", response_model=DatabaseStatsResponse)
async def get_database_statistics(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get database performance statistics"""
    try:
        stats = monitoring_service.get_database_statistics()
        
        return DatabaseStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch database stats: {str(e)}")

@router.get("/metrics/api")
async def get_api_metrics(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get API endpoint usage metrics"""
    try:
        metrics = monitoring_service.get_api_metrics()
        
        return {
            "total_requests": metrics.get("total_requests", 0),
            "requests_per_minute": metrics.get("requests_per_minute", 0),
            "average_response_time": metrics.get("avg_response_time", 0),
            "error_rate": metrics.get("error_rate", 0),
            "endpoints": metrics.get("endpoint_stats", {}),
            "status_codes": metrics.get("status_code_distribution", {}),
            "last_updated": metrics.get("last_updated", datetime.now().isoformat())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch API metrics: {str(e)}")

@router.get("/alerts", response_model=List[AlertResponse])
async def get_system_alerts(
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get system alerts and notifications"""
    try:
        alerts = monitoring_service.get_alerts(
            severity=severity,
            active_only=active_only,
            limit=limit
        )
        
        return [AlertResponse(**alert) for alert in alerts]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new system alert"""
    try:
        new_alert = monitoring_service.create_alert(
            alert_data=alert.dict(),
            created_by=current_user.id
        )
        
        return AlertResponse(**new_alert)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Acknowledge a system alert"""
    try:
        success = monitoring_service.acknowledge_alert(alert_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": f"Alert {alert_id} acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/logs/application")
async def get_application_logs(
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get application logs"""
    try:
        logs = monitoring_service.get_application_logs(
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "filters": {
                "level": level,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch application logs: {str(e)}")

@router.get("/logs/audit")
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit logs"""
    try:
        # Check if user has permission to view audit logs
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        logs = monitoring_service.get_audit_logs(
            user_id=user_id,
            action=action,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "audit_logs": logs,
            "total_count": len(logs),
            "filters": {
                "user_id": user_id,
                "action": action,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")

@router.get("/system/resources")
async def get_system_resources(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get system resource usage"""
    try:
        resources = monitoring_service.get_system_resources()
        
        return {
            "cpu": {
                "usage_percent": resources.get("cpu_percent", 0),
                "load_average": resources.get("load_average", [])
            },
            "memory": {
                "usage_percent": resources.get("memory_percent", 0),
                "available_gb": resources.get("memory_available_gb", 0),
                "used_gb": resources.get("memory_used_gb", 0)
            },
            "disk": {
                "usage_percent": resources.get("disk_percent", 0),
                "free_gb": resources.get("disk_free_gb", 0),
                "used_gb": resources.get("disk_used_gb", 0)
            },
            "network": {
                "bytes_sent": resources.get("network_sent", 0),
                "bytes_received": resources.get("network_received", 0)
            },
            "timestamp": resources.get("timestamp", datetime.now().isoformat())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system resources: {str(e)}")

@router.get("/cache/stats")
async def get_cache_statistics(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get Redis cache statistics"""
    try:
        redis_client = db_config.get_redis_client()
        
        if not redis_client:
            return {"status": "unavailable", "message": "Redis not configured"}
        
        stats = monitoring_service.get_cache_statistics()
        
        return {
            "status": "connected",
            "memory_usage": stats.get("used_memory", 0),
            "memory_usage_human": stats.get("used_memory_human", "0B"),
            "connected_clients": stats.get("connected_clients", 0),
            "total_commands": stats.get("total_commands_processed", 0),
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
            "keys_count": stats.get("db0_keys", 0),
            "expires_count": stats.get("db0_expires", 0),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cache stats: {str(e)}")

@router.post("/maintenance/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear"),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user)
):
    """Clear cache (admin only)"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cleared_count = monitoring_service.clear_cache(pattern)
        
        return {
            "message": "Cache cleared successfully",
            "keys_cleared": cleared_count,
            "pattern": pattern or "all",
            "cleared_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/status/summary")
async def get_status_summary(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get overall system status summary (public endpoint)"""
    try:
        summary = monitoring_service.get_status_summary()
        
        return {
            "overall_status": summary.get("status", "unknown"),
            "uptime": summary.get("uptime", "unknown"),
            "version": "1.0.0",
            "environment": "production",
            "services": {
                "api": summary.get("api_status", "unknown"),
                "database": summary.get("database_status", "unknown"),
                "cache": summary.get("cache_status", "unknown")
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status summary: {str(e)}")