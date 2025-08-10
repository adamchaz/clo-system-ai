"""
Monitoring Schemas
Pydantic models for system monitoring-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum

class SystemStatus(str, Enum):
    """System status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

class AlertSeverity(str, Enum):
    """Alert severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ServiceHealth(BaseModel):
    """Individual service health status"""
    service_name: str
    status: SystemStatus
    response_time_ms: Optional[float] = None
    last_checked: datetime
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SystemHealthResponse(BaseModel):
    """Schema for system health response"""
    overall_status: SystemStatus
    uptime_seconds: int
    uptime_human: str
    last_restart: Optional[datetime] = None
    
    # Service health
    services: List[ServiceHealth]
    
    # Critical metrics
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    
    # Database connectivity
    postgresql_status: SystemStatus
    redis_status: SystemStatus
    migration_databases_status: Dict[str, bool]
    
    # Summary
    healthy_services: int
    total_services: int
    active_alerts: int
    
    # Timestamps
    check_time: datetime = Field(default_factory=datetime.now)

class PerformanceMetrics(BaseModel):
    """Performance metrics data point"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_received: int
    active_connections: int
    request_rate: float
    response_time_avg: float

class PerformanceMetricsResponse(BaseModel):
    """Schema for performance metrics response"""
    time_range: str
    metrics: List[PerformanceMetrics]
    
    # Aggregated statistics
    avg_cpu_percent: float
    max_cpu_percent: float
    avg_memory_percent: float
    max_memory_percent: float
    avg_response_time: float
    total_requests: int
    
    # Trends
    cpu_trend: str  # "increasing", "decreasing", "stable"
    memory_trend: str
    response_time_trend: str

class DatabaseStats(BaseModel):
    """Database performance statistics"""
    database_name: str
    size_mb: float
    connections_active: int
    connections_max: int
    queries_per_second: float
    slow_queries_count: int
    cache_hit_ratio: float
    index_usage_ratio: float
    
    # Table statistics
    largest_tables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance metrics
    avg_query_time_ms: float
    lock_waits_count: int
    deadlocks_count: int

class DatabaseStatsResponse(BaseModel):
    """Schema for database statistics response"""
    postgresql_stats: DatabaseStats
    migration_db_stats: Dict[str, Dict[str, Any]]
    
    # Overall metrics
    total_databases: int
    total_size_mb: float
    total_connections: int
    
    # Performance summary
    overall_performance_score: float  # 0-100
    recommendations: List[str] = Field(default_factory=list)
    
    last_analyzed: datetime

class AlertBase(BaseModel):
    """Base alert model"""
    title: str
    message: str
    severity: AlertSeverity
    component: str  # "database", "api", "cache", "system"
    alert_type: str = "system"

class AlertCreate(AlertBase):
    """Schema for creating alerts"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    severity: AlertSeverity
    component: str
    
    # Optional metadata
    metadata: Optional[Dict[str, Any]] = None
    auto_resolve: bool = Field(default=False)

class AlertResponse(AlertBase):
    """Schema for alert responses"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    # Status tracking
    is_active: bool = True
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Metadata
    occurrence_count: int = 1
    last_occurrence: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ApplicationLog(BaseModel):
    """Application log entry"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[str] = None
    process_id: Optional[int] = None
    
    # Additional context
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class AuditLog(BaseModel):
    """Audit log entry"""
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    
    # Result
    success: bool
    error_message: Optional[str] = None
    response_code: Optional[int] = None
    
    # Additional details
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemResources(BaseModel):
    """System resource usage"""
    timestamp: datetime
    
    # CPU metrics
    cpu_percent: float
    cpu_count: int
    load_average: List[float]
    
    # Memory metrics
    memory_total_gb: float
    memory_used_gb: float
    memory_available_gb: float
    memory_percent: float
    
    # Disk metrics
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float
    
    # Network metrics
    network_bytes_sent: int
    network_bytes_received: int
    network_packets_sent: int
    network_packets_received: int
    
    # Process metrics
    process_count: int
    thread_count: int
    file_descriptors: int

class CacheStats(BaseModel):
    """Cache performance statistics"""
    redis_version: str
    uptime_seconds: int
    connected_clients: int
    used_memory: int
    used_memory_human: str
    memory_usage_percent: float
    
    # Key statistics
    total_keys: int
    expired_keys: int
    evicted_keys: int
    
    # Performance metrics
    total_commands_processed: int
    instantaneous_ops_per_sec: float
    cache_hit_ratio: float
    cache_miss_ratio: float
    
    # Network
    total_connections_received: int
    rejected_connections: int
    
    # Keyspace
    keyspace_stats: Dict[str, Dict[str, int]] = Field(default_factory=dict)

class APIMetrics(BaseModel):
    """API endpoint metrics"""
    total_requests: int
    requests_per_minute: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    
    # Status code distribution
    status_2xx: int = 0
    status_4xx: int = 0
    status_5xx: int = 0
    error_rate_percent: float
    
    # Endpoint breakdown
    top_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    slowest_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Time window
    time_window: str
    last_updated: datetime

class StatusSummary(BaseModel):
    """Overall system status summary"""
    overall_status: SystemStatus
    uptime: str
    version: str
    environment: str
    
    # Service status
    api_status: SystemStatus
    database_status: SystemStatus
    cache_status: SystemStatus
    
    # Key metrics
    active_users: int
    total_requests_today: int
    error_rate_percent: float
    avg_response_time_ms: float
    
    # Alerts
    critical_alerts: int
    total_alerts: int
    
    last_updated: datetime

class MaintenanceWindow(BaseModel):
    """Maintenance window information"""
    id: str
    title: str
    description: str
    scheduled_start: datetime
    scheduled_end: datetime
    status: str  # "scheduled", "active", "completed", "cancelled"
    
    # Impact
    affected_services: List[str]
    expected_downtime_minutes: int
    
    # Communication
    created_by: str
    notification_sent: bool = False
    
    class Config:
        from_attributes = True

class MonitoringConfiguration(BaseModel):
    """Monitoring system configuration"""
    # Alert thresholds
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 85.0
    disk_threshold_percent: float = 90.0
    response_time_threshold_ms: float = 2000.0
    error_rate_threshold_percent: float = 5.0
    
    # Retention periods
    metrics_retention_days: int = 30
    logs_retention_days: int = 90
    alerts_retention_days: int = 365
    
    # Notification settings
    enable_email_alerts: bool = True
    enable_slack_alerts: bool = False
    alert_email_recipients: List[str] = Field(default_factory=list)
    
    # Monitoring intervals
    health_check_interval_seconds: int = 30
    metrics_collection_interval_seconds: int = 60
    log_cleanup_interval_hours: int = 24