"""
Production Monitoring and Health Check Configuration
Implements structured logging, health endpoints, and system monitoring
"""

import logging
import logging.config
import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .config import settings
from .database import DatabaseManager


class StructuredLogger:
    """Structured JSON logging for production monitoring"""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self._configure_structured_logging()
    
    def _configure_structured_logging(self):
        """Configure structured JSON logging"""
        
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                },
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": settings.log_level,
                    "formatter": "json" if settings.environment == "production" else "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": settings.log_level,
                    "formatter": "json",
                    "filename": "logs/app.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["console"] + (["file"] if settings.environment == "production" else [])
            }
        }
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Only use JSON logging in production if pythonjsonlogger is available
        try:
            import pythonjsonlogger.jsonlogger
            logging.config.dictConfig(logging_config)
        except ImportError:
            # Fallback to basic logging if pythonjsonlogger not available
            logging.basicConfig(
                level=getattr(logging, settings.log_level),
                format=settings.log_format
            )
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        if kwargs:
            self.logger.info(message, extra=kwargs)
        else:
            self.logger.info(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        if kwargs:
            self.logger.error(message, extra=kwargs)
        else:
            self.logger.error(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        if kwargs:
            self.logger.warning(message, extra=kwargs)
        else:
            self.logger.warning(message)


class SystemMonitor:
    """System health and performance monitoring"""
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_stats = {
                "total": memory.total,
                "available": memory.available, 
                "percent": memory.percent,
                "used": memory.used
            }
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_stats = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": memory_stats,
                "disk": disk_stats,
                "processes": len(psutil.pids())
            }
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": f"Failed to collect system stats: {str(e)}"
            }
    
    @staticmethod
    def get_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        results = {}
        
        # Test PostgreSQL
        try:
            start_time = time.time()
            postgres_healthy = DatabaseManager.test_connection()
            postgres_time = time.time() - start_time
            
            results["postgresql"] = {
                "healthy": postgres_healthy,
                "response_time_ms": round(postgres_time * 1000, 2),
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "database": settings.postgres_db
            }
        except Exception as e:
            results["postgresql"] = {
                "healthy": False,
                "error": str(e)
            }
        
        # Test Redis  
        try:
            start_time = time.time()
            redis_healthy = DatabaseManager.test_redis_connection()
            redis_time = time.time() - start_time
            
            results["redis"] = {
                "healthy": redis_healthy,
                "response_time_ms": round(redis_time * 1000, 2),
                "host": settings.redis_host,
                "port": settings.redis_port
            }
        except Exception as e:
            results["redis"] = {
                "healthy": False,
                "error": str(e)
            }
        
        return results
    
    @staticmethod
    def get_application_metrics() -> Dict[str, Any]:
        """Get application-specific metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "debug_mode": settings.debug,
            "version": "1.0.0",
            "quantlib_initialized": True,  # Would check actual QuantLib status
            "max_assets": settings.max_assets,
            "max_correlations": settings.max_correlations
        }


class HealthChecker:
    """Comprehensive health check implementation"""
    
    def __init__(self):
        self.logger = StructuredLogger("health_checker")
        self.monitor = SystemMonitor()
    
    def check_health(self, detailed: bool = False) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()
        
        # Basic health status
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment
        }
        
        if detailed:
            try:
                # System statistics
                health_status["system"] = self.monitor.get_system_stats()
                
                # Database health
                db_health = self.monitor.get_database_health()
                health_status["databases"] = db_health
                
                # Application metrics
                health_status["application"] = self.monitor.get_application_metrics()
                
                # Overall health determination
                postgres_healthy = db_health.get("postgresql", {}).get("healthy", False)
                redis_healthy = db_health.get("redis", {}).get("healthy", False)
                
                if not postgres_healthy or not redis_healthy:
                    health_status["status"] = "degraded"
                    
                # Response time
                health_status["check_duration_ms"] = round((time.time() - start_time) * 1000, 2)
                
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        
        return health_status
    
    def check_readiness(self) -> Dict[str, Any]:
        """Check if application is ready to serve requests"""
        readiness = {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check database connectivity
        try:
            postgres_ready = DatabaseManager.test_connection()
            readiness["checks"]["postgresql"] = {
                "status": "pass" if postgres_ready else "fail",
                "ready": postgres_ready
            }
            
            redis_ready = DatabaseManager.test_redis_connection()  
            readiness["checks"]["redis"] = {
                "status": "pass" if redis_ready else "fail",
                "ready": redis_ready
            }
            
            # Overall readiness
            readiness["ready"] = postgres_ready and redis_ready
            
        except Exception as e:
            readiness["ready"] = False
            readiness["error"] = str(e)
        
        return readiness
    
    def check_liveness(self) -> Dict[str, Any]:
        """Check if application is alive"""
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
        }


# Global health checker instance
health_checker = HealthChecker()


def configure_monitoring():
    """Configure monitoring and logging for the application"""
    
    # Initialize structured logging
    logger = StructuredLogger("monitoring")
    logger.info("Monitoring configuration initialized", 
                environment=settings.environment,
                log_level=settings.log_level)
    
    # Record application start time for uptime tracking
    health_checker._start_time = time.time()
    
    return logger


# Export main components
__all__ = [
    "StructuredLogger",
    "SystemMonitor", 
    "HealthChecker",
    "health_checker",
    "configure_monitoring"
]