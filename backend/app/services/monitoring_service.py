"""
Monitoring Service
Handles system monitoring, health checks, and performance metrics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import psutil
import platform
import json

from sqlalchemy.orm import Session
from ..core.database_config import db_config

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for system monitoring and health checks"""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status
        
        Returns:
            System health information
        """
        logger.debug("Collecting system health information")
        
        try:
            # Get uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            uptime_human = self._format_uptime(uptime_seconds)
            
            # Check individual services
            services = self._check_all_services()
            
            # Get system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Count service status
            healthy_services = sum(1 for service in services if service['status'] == 'healthy')
            total_services = len(services)
            
            # Determine overall status
            if healthy_services == total_services:
                overall_status = 'healthy'
            elif healthy_services >= total_services * 0.8:
                overall_status = 'degraded'
            else:
                overall_status = 'unhealthy'
            
            # Get active alerts count
            active_alerts = len(self._get_active_alerts())
            
            return {
                'overall_status': overall_status,
                'uptime_seconds': int(uptime_seconds),
                'uptime_human': uptime_human,
                'last_restart': self.start_time,
                'services': services,
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': disk.percent,
                'postgresql_status': self._get_postgresql_status(),
                'redis_status': self._get_redis_status(),
                'migration_databases_status': self._get_migration_db_status(),
                'healthy_services': healthy_services,
                'total_services': total_services,
                'active_alerts': active_alerts
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            raise
    
    def get_performance_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get system performance metrics
        
        Args:
            time_range: Time range for metrics (5m, 15m, 1h, 6h, 24h, 7d)
            
        Returns:
            Performance metrics data
        """
        logger.debug(f"Collecting performance metrics for {time_range}")
        
        try:
            # Generate mock performance data points
            metrics = self._generate_performance_metrics(time_range)
            
            # Calculate aggregated statistics
            cpu_values = [m['cpu_percent'] for m in metrics]
            memory_values = [m['memory_percent'] for m in metrics]
            response_times = [m['response_time_avg'] for m in metrics]
            
            aggregated_stats = {
                'avg_cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max_cpu_percent': max(cpu_values) if cpu_values else 0,
                'avg_memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max_memory_percent': max(memory_values) if memory_values else 0,
                'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                'total_requests': sum(m['active_connections'] for m in metrics)
            }
            
            # Determine trends
            trends = self._calculate_trends(cpu_values, memory_values, response_times)
            
            return {
                'time_range': time_range,
                'metrics': metrics,
                **aggregated_stats,
                **trends
            }
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {e}")
            raise
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get database performance statistics
        
        Returns:
            Database statistics
        """
        logger.debug("Collecting database statistics")
        
        try:
            # PostgreSQL statistics
            postgresql_stats = self._get_postgresql_statistics()
            
            # Migration database statistics
            migration_stats = self._get_migration_database_statistics()
            
            # Calculate overall metrics
            total_databases = 1 + len(migration_stats)  # PostgreSQL + migration DBs
            total_size_mb = postgresql_stats['size_mb'] + sum(
                stats.get('size_mb', 0) for stats in migration_stats.values()
            )
            total_connections = postgresql_stats['connections_active']
            
            # Performance score (0-100)
            performance_score = self._calculate_database_performance_score(
                postgresql_stats, migration_stats
            )
            
            # Generate recommendations
            recommendations = self._generate_database_recommendations(
                postgresql_stats, migration_stats, performance_score
            )
            
            return {
                'postgresql_stats': postgresql_stats,
                'migration_db_stats': migration_stats,
                'total_databases': total_databases,
                'total_size_mb': total_size_mb,
                'total_connections': total_connections,
                'overall_performance_score': performance_score,
                'recommendations': recommendations,
                'last_analyzed': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Database statistics collection failed: {e}")
            raise
    
    def get_alerts(
        self, 
        severity: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get system alerts
        
        Args:
            severity: Filter by severity level
            active_only: Return only active alerts
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        logger.debug(f"Fetching alerts - severity: {severity}, active: {active_only}")
        
        try:
            # Get alerts from storage (mock implementation)
            all_alerts = self._get_stored_alerts()
            
            # Apply filters
            filtered_alerts = all_alerts
            
            if severity:
                filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
            
            if active_only:
                filtered_alerts = [a for a in filtered_alerts if a['is_active']]
            
            # Apply limit
            filtered_alerts = filtered_alerts[:limit]
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Alert retrieval failed: {e}")
            raise
    
    def create_alert(
        self, 
        alert_data: Dict[str, Any], 
        created_by: str
    ) -> Dict[str, Any]:
        """
        Create a new system alert
        
        Args:
            alert_data: Alert information
            created_by: User who created the alert
            
        Returns:
            Created alert data
        """
        logger.info(f"Creating alert: {alert_data.get('title', 'Untitled')}")
        
        try:
            # Generate alert ID
            alert_id = self._generate_alert_id()
            
            # Create alert record
            alert = {
                'id': alert_id,
                'created_at': datetime.now(),
                'created_by': created_by,
                'is_active': True,
                'is_acknowledged': False,
                'occurrence_count': 1,
                'last_occurrence': datetime.now(),
                **alert_data
            }
            
            # Store alert
            self._store_alert(alert)
            
            # Send notifications if needed
            self._send_alert_notifications(alert)
            
            logger.info(f"Successfully created alert {alert_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Alert creation failed: {e}")
            raise
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge a system alert
        
        Args:
            alert_id: Alert identifier
            acknowledged_by: User who acknowledged the alert
            
        Returns:
            True if acknowledged successfully
        """
        logger.info(f"Acknowledging alert: {alert_id}")
        
        try:
            # Get alert
            alert = self._get_alert_by_id(alert_id)
            
            if not alert:
                return False
            
            # Update alert
            alert['is_acknowledged'] = True
            alert['acknowledged_by'] = acknowledged_by
            alert['acknowledged_at'] = datetime.now()
            
            # Store updated alert
            self._store_alert(alert)
            
            logger.info(f"Successfully acknowledged alert {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Alert acknowledgment failed for {alert_id}: {e}")
            return False
    
    def get_application_logs(
        self,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get application logs
        
        Args:
            level: Log level filter
            start_time: Start time for log retrieval
            end_time: End time for log retrieval
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        logger.debug(f"Fetching application logs - level: {level}, limit: {limit}")
        
        try:
            # Mock log entries
            logs = self._generate_mock_logs(level, start_time, end_time, limit)
            
            return logs
            
        except Exception as e:
            logger.error(f"Application log retrieval failed: {e}")
            raise
    
    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs
        
        Args:
            user_id: Filter by user ID
            action: Filter by action type
            start_time: Start time for log retrieval
            end_time: End time for log retrieval
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log entries
        """
        logger.debug(f"Fetching audit logs - user: {user_id}, action: {action}")
        
        try:
            # Mock audit logs
            audit_logs = self._generate_mock_audit_logs(
                user_id, action, start_time, end_time, limit
            )
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Audit log retrieval failed: {e}")
            raise
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        Get current system resource usage
        
        Returns:
            System resource information
        """
        logger.debug("Collecting system resource information")
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_used_gb = disk.used / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            return {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_average': list(load_avg),
                'memory_total_gb': round(memory_total_gb, 2),
                'memory_used_gb': round(memory_used_gb, 2),
                'memory_available_gb': round(memory_available_gb, 2),
                'memory_percent': memory.percent,
                'disk_total_gb': round(disk_total_gb, 2),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_free_gb': round(disk_free_gb, 2),
                'disk_percent': (disk_used_gb / disk_total_gb) * 100,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_received': network.bytes_recv,
                'network_packets_sent': network.packets_sent,
                'network_packets_received': network.packets_recv,
                'process_count': process_count,
                'thread_count': 0,  # Would need additional calculation
                'file_descriptors': 0  # Platform-specific
            }
            
        except Exception as e:
            logger.error(f"System resource collection failed: {e}")
            raise
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics
        
        Returns:
            Cache statistics
        """
        logger.debug("Collecting cache statistics")
        
        try:
            redis_client = db_config.get_redis_client()
            
            if not redis_client:
                return {'status': 'unavailable', 'error': 'Redis not configured'}
            
            # Get Redis info
            info = redis_client.info()
            
            # Extract key statistics
            stats = {
                'redis_version': info.get('redis_version', 'unknown'),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'memory_usage_percent': 0,  # Would calculate based on maxmemory
                'total_keys': 0,
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'cache_hit_ratio': 0.95,  # Mock value
                'cache_miss_ratio': 0.05,  # Mock value
                'total_connections_received': info.get('total_connections_received', 0),
                'rejected_connections': info.get('rejected_connections', 0),
                'keyspace_stats': {}
            }
            
            # Get keyspace information
            for key, value in info.items():
                if key.startswith('db'):
                    stats['keyspace_stats'][key] = value
            
            return stats
            
        except Exception as e:
            logger.error(f"Cache statistics collection failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache keys
        
        Args:
            pattern: Key pattern to clear (None for all keys)
            
        Returns:
            Number of keys cleared
        """
        logger.info(f"Clearing cache - pattern: {pattern or 'all'}")
        
        try:
            redis_client = db_config.get_redis_client()
            
            if not redis_client:
                raise ValueError("Redis not available")
            
            if pattern:
                # Clear keys matching pattern
                keys = redis_client.keys(pattern)
                if keys:
                    cleared = redis_client.delete(*keys)
                else:
                    cleared = 0
            else:
                # Clear all keys
                cleared = redis_client.flushdb()
            
            logger.info(f"Cleared {cleared} cache keys")
            return cleared
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            raise
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """
        Get API endpoint usage metrics
        
        Returns:
            API metrics
        """
        logger.debug("Collecting API metrics")
        
        try:
            # Mock API metrics
            return {
                'total_requests': 125842,
                'requests_per_minute': 23.5,
                'avg_response_time': 145.2,
                'error_rate': 0.8,
                'endpoint_stats': {
                    '/api/v1/assets': {'requests': 45123, 'avg_response_time': 120.5},
                    '/api/v1/portfolios': {'requests': 32456, 'avg_response_time': 180.3},
                    '/api/v1/waterfall': {'requests': 18234, 'avg_response_time': 250.1}
                },
                'status_code_distribution': {
                    '200': 118934,
                    '400': 3245,
                    '404': 2156,
                    '500': 1507
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"API metrics collection failed: {e}")
            raise
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get overall system status summary
        
        Returns:
            Status summary
        """
        logger.debug("Generating status summary")
        
        try:
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            # Check critical services
            db_status = 'healthy' if db_config.health_check().get('postgresql', False) else 'unhealthy'
            cache_status = 'healthy' if db_config.health_check().get('redis', False) else 'degraded'
            
            # Overall status logic
            if db_status == 'healthy' and cache_status in ['healthy', 'degraded']:
                overall_status = 'healthy'
            else:
                overall_status = 'unhealthy'
            
            return {
                'status': overall_status,
                'uptime': self._format_uptime(uptime_seconds),
                'api_status': 'healthy',
                'database_status': db_status,
                'cache_status': cache_status
            }
            
        except Exception as e:
            logger.error(f"Status summary generation failed: {e}")
            raise
    
    # Helper methods
    
    def _check_all_services(self) -> List[Dict[str, Any]]:
        """Check status of all services"""
        services = []
        
        # Database service
        db_health = db_config.health_check()
        services.append({
            'service_name': 'PostgreSQL',
            'status': 'healthy' if db_health.get('postgresql', False) else 'unhealthy',
            'response_time_ms': db_health.get('postgresql_response_time', 0),
            'last_checked': datetime.now(),
            'error_message': None if db_health.get('postgresql', False) else 'Connection failed'
        })
        
        # Redis service
        services.append({
            'service_name': 'Redis',
            'status': 'healthy' if db_health.get('redis', False) else 'degraded',
            'response_time_ms': db_health.get('redis_response_time', 0),
            'last_checked': datetime.now(),
            'error_message': None if db_health.get('redis', False) else 'Connection failed'
        })
        
        # Migration databases
        migration_dbs = db_health.get('migration_databases', {})
        for db_name, is_healthy in migration_dbs.items():
            services.append({
                'service_name': f'Migration DB ({db_name})',
                'status': 'healthy' if is_healthy else 'unhealthy',
                'response_time_ms': 0,
                'last_checked': datetime.now(),
                'error_message': None if is_healthy else 'Connection failed'
            })
        
        return services
    
    def _get_postgresql_status(self) -> str:
        """Get PostgreSQL status"""
        health = db_config.health_check()
        return 'healthy' if health.get('postgresql', False) else 'unhealthy'
    
    def _get_redis_status(self) -> str:
        """Get Redis status"""
        health = db_config.health_check()
        return 'healthy' if health.get('redis', False) else 'degraded'
    
    def _get_migration_db_status(self) -> Dict[str, bool]:
        """Get migration database status"""
        health = db_config.health_check()
        return health.get('migration_databases', {})
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _generate_performance_metrics(self, time_range: str) -> List[Dict[str, Any]]:
        """Generate mock performance metrics"""
        # Mock performance data generation
        import random
        from datetime import datetime, timedelta
        
        intervals = {
            '5m': (5, 60),    # 5 data points, 1 minute intervals
            '15m': (15, 60),  # 15 data points, 1 minute intervals
            '1h': (60, 60),   # 60 data points, 1 minute intervals
            '6h': (72, 300),  # 72 data points, 5 minute intervals
            '24h': (288, 300), # 288 data points, 5 minute intervals
            '7d': (168, 3600)  # 168 data points, 1 hour intervals
        }
        
        count, interval_seconds = intervals.get(time_range, (60, 60))
        
        metrics = []
        now = datetime.now()
        
        for i in range(count):
            timestamp = now - timedelta(seconds=i * interval_seconds)
            metrics.append({
                'timestamp': timestamp,
                'cpu_percent': random.uniform(10, 80),
                'memory_percent': random.uniform(40, 90),
                'disk_io_read': random.randint(1000, 10000),
                'disk_io_write': random.randint(500, 5000),
                'network_io_sent': random.randint(1000, 50000),
                'network_io_received': random.randint(2000, 80000),
                'active_connections': random.randint(5, 50),
                'request_rate': random.uniform(1, 25),
                'response_time_avg': random.uniform(80, 300)
            })
        
        return sorted(metrics, key=lambda x: x['timestamp'])
    
    def _calculate_trends(self, cpu_values, memory_values, response_times):
        """Calculate performance trends"""
        def get_trend(values):
            if len(values) < 2:
                return 'stable'
            
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            
            change_percent = ((avg_second - avg_first) / avg_first) * 100
            
            if change_percent > 10:
                return 'increasing'
            elif change_percent < -10:
                return 'decreasing'
            else:
                return 'stable'
        
        return {
            'cpu_trend': get_trend(cpu_values),
            'memory_trend': get_trend(memory_values),
            'response_time_trend': get_trend(response_times)
        }
    
    def _get_postgresql_statistics(self) -> Dict[str, Any]:
        """Get PostgreSQL statistics"""
        # Mock PostgreSQL statistics
        return {
            'database_name': 'clo_management',
            'size_mb': 2048.5,
            'connections_active': 12,
            'connections_max': 100,
            'queries_per_second': 45.2,
            'slow_queries_count': 3,
            'cache_hit_ratio': 0.95,
            'index_usage_ratio': 0.87,
            'largest_tables': [
                {'table_name': 'assets', 'size_mb': 512.3},
                {'table_name': 'asset_correlations', 'size_mb': 384.7}
            ],
            'avg_query_time_ms': 125.5,
            'lock_waits_count': 2,
            'deadlocks_count': 0
        }
    
    def _get_migration_database_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get migration database statistics"""
        # Mock migration database statistics
        return {
            'assets': {'size_mb': 125.3, 'record_count': 384},
            'correlations': {'size_mb': 892.1, 'record_count': 238144},
            'scenarios': {'size_mb': 45.8, 'record_count': 19795},
            'config': {'size_mb': 12.4, 'record_count': 356},
            'reference': {'size_mb': 23.7, 'record_count': 694}
        }
    
    def _calculate_database_performance_score(self, pg_stats, migration_stats) -> float:
        """Calculate database performance score (0-100)"""
        score = 100
        
        # Deduct for high query times
        if pg_stats['avg_query_time_ms'] > 200:
            score -= 20
        
        # Deduct for low cache hit ratio
        if pg_stats['cache_hit_ratio'] < 0.9:
            score -= 15
        
        # Deduct for high connection usage
        connection_usage = pg_stats['connections_active'] / pg_stats['connections_max']
        if connection_usage > 0.8:
            score -= 10
        
        return max(0, score)
    
    def _generate_database_recommendations(self, pg_stats, migration_stats, score) -> List[str]:
        """Generate database optimization recommendations"""
        recommendations = []
        
        if pg_stats['avg_query_time_ms'] > 200:
            recommendations.append("Consider optimizing slow queries")
        
        if pg_stats['cache_hit_ratio'] < 0.9:
            recommendations.append("Increase shared_buffers for better cache performance")
        
        if score < 80:
            recommendations.append("Review database configuration and indexing strategy")
        
        return recommendations
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        # Mock active alerts
        return [
            {
                'id': 'alert_001',
                'title': 'High CPU Usage',
                'severity': 'medium',
                'is_active': True,
                'created_at': datetime.now() - timedelta(minutes=15)
            }
        ]
    
    def _get_stored_alerts(self) -> List[Dict[str, Any]]:
        """Get all stored alerts"""
        # Mock alert storage
        return [
            {
                'id': 'alert_001',
                'title': 'High CPU Usage',
                'message': 'CPU usage exceeded 80% for 10 minutes',
                'severity': 'medium',
                'component': 'system',
                'alert_type': 'system',
                'is_active': True,
                'is_acknowledged': False,
                'created_at': datetime.now() - timedelta(minutes=15),
                'occurrence_count': 1,
                'last_occurrence': datetime.now() - timedelta(minutes=15)
            },
            {
                'id': 'alert_002',
                'title': 'Database Connection Pool Warning',
                'message': 'Database connection pool usage above 75%',
                'severity': 'low',
                'component': 'database',
                'alert_type': 'performance',
                'is_active': True,
                'is_acknowledged': True,
                'created_at': datetime.now() - timedelta(hours=2),
                'acknowledged_at': datetime.now() - timedelta(hours=1),
                'acknowledged_by': 'admin',
                'occurrence_count': 3,
                'last_occurrence': datetime.now() - timedelta(minutes=30)
            }
        ]
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid
        return f"alert_{uuid.uuid4().hex[:8]}"
    
    def _store_alert(self, alert: Dict[str, Any]) -> None:
        """Store alert in database"""
        # Implementation would store in PostgreSQL alerts table
        logger.debug(f"Stored alert {alert['id']} in database")
    
    def _get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert by ID"""
        # Implementation would query PostgreSQL
        alerts = self._get_stored_alerts()
        return next((a for a in alerts if a['id'] == alert_id), None)
    
    def _send_alert_notifications(self, alert: Dict[str, Any]) -> None:
        """Send alert notifications"""
        # Implementation would send email/Slack notifications
        logger.info(f"Alert notifications sent for {alert['id']}")
    
    def _generate_mock_logs(self, level, start_time, end_time, limit) -> List[Dict[str, Any]]:
        """Generate mock application logs"""
        import random
        
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level:
            levels = [level]
        
        logs = []
        for i in range(min(limit, 50)):  # Generate up to 50 mock logs
            timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))
            logs.append({
                'timestamp': timestamp,
                'level': random.choice(levels),
                'logger_name': random.choice(['clo.waterfall', 'clo.risk', 'clo.auth']),
                'message': f'Mock log message {i}',
                'module': 'service.py',
                'function': 'calculate_metrics',
                'line_number': random.randint(100, 500),
                'thread_id': f'thread-{random.randint(1, 10)}',
                'process_id': 12345
            })
        
        return sorted(logs, key=lambda x: x['timestamp'], reverse=True)
    
    def _generate_mock_audit_logs(self, user_id, action, start_time, end_time, limit) -> List[Dict[str, Any]]:
        """Generate mock audit logs"""
        import random
        
        actions = ['login', 'logout', 'calculate_waterfall', 'view_portfolio', 'update_asset']
        if action:
            actions = [action]
        
        logs = []
        for i in range(min(limit, 30)):  # Generate up to 30 mock audit logs
            timestamp = datetime.now() - timedelta(hours=random.randint(1, 72))
            logs.append({
                'timestamp': timestamp,
                'user_id': user_id or f'user_{random.randint(1, 10)}',
                'user_email': 'user@example.com',
                'action': random.choice(actions),
                'resource_type': 'portfolio',
                'resource_id': f'deal_{random.randint(1, 5)}',
                'ip_address': f'192.168.1.{random.randint(100, 200)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'endpoint': '/api/v1/portfolios',
                'http_method': 'GET',
                'success': random.choice([True, True, True, False]),  # 75% success rate
                'response_code': random.choice([200, 200, 200, 400, 404, 500]),
                'changes': {'field': 'value'} if random.choice([True, False]) else None
            })
        
        return sorted(logs, key=lambda x: x['timestamp'], reverse=True)