"""
CLO System Configuration Management
Handles environment variables and application settings
"""

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import validator
import QuantLib as ql


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment Configuration
    environment: str = "development"
    debug: bool = True
    
    # Database Configuration
    database_url: str = "postgresql://postgres:adamchaz@127.0.0.1:5433/clo_dev"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433
    postgres_user: str = "postgres"
    postgres_password: str = "adamchaz"
    postgres_db: str = "clo_dev"
    postgres_ssl_mode: str = "disable"
    
    # Database Connection Pool
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Redis Configuration  
    redis_url: str = "redis://127.0.0.1:6379"
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    
    # Application Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    max_workers: int = 1
    worker_timeout: int = 60
    keep_alive: int = 2
    max_requests: int = 1000
    max_requests_jitter: int = 100
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002", "http://127.0.0.1:3003", "http://127.0.0.1:3004"]
    cors_allow_credentials: bool = True
    cors_max_age: int = 3600
    
    # Security Configuration
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    jwt_algorithm: str = "HS256"
    jwt_private_key_path: Optional[str] = None
    jwt_public_key_path: Optional[str] = None
    force_https: bool = False
    
    # SSL/TLS Configuration
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_ca_path: Optional[str] = None
    
    # Rate Limiting Configuration
    rate_limit_strict: str = "10/minute"
    rate_limit_moderate: str = "100/minute"
    rate_limit_lenient: str = "1000/minute"
    rate_limit_auth: str = "5/minute"
    
    # QuantLib Configuration
    quantlib_date_today_auto: bool = True
    quantlib_thread_safety: bool = True
    
    # CLO System Specific
    max_assets: int = 10000
    max_correlations: int = 1000000
    default_day_count: str = "Actual360"
    default_business_calendar: str = "UnitedStates.NYSE"
    
    # File Storage Configuration
    upload_max_size: str = "10MB"
    allowed_file_types: List[str] = ["pdf", "xlsx", "csv", "docx", "txt"]
    storage_backend: str = "local"
    local_storage_path: str = "uploads"
    
    # Azure Configuration
    azure_storage_account: Optional[str] = None
    azure_storage_key: Optional[str] = None
    azure_blob_container: str = "clo-documents"
    azure_key_vault_url: Optional[str] = None
    
    # Cache Configuration
    cache_default_timeout: int = 3600
    cache_long_timeout: int = 86400
    correlation_cache_timeout: int = 21600
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file_path: Optional[str] = None
    log_max_size: str = "10MB"
    log_backup_count: int = 5
    
    # Monitoring Configuration
    health_check_timeout: int = 30
    metrics_export_interval: int = 60
    prometheus_metrics_enabled: bool = False
    prometheus_port: int = 9090
    performance_monitoring_enabled: bool = False
    slow_query_threshold: int = 1000
    request_timeout: int = 30
    
    # Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    from_email: str = "noreply@clo-system.com"
    
    # Backup Configuration
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"
    backup_retention_days: int = 30
    backup_storage_account: Optional[str] = None
    
    # Security Headers
    security_headers_enabled: bool = True
    hsts_max_age: int = 31536000
    csp_enabled: bool = True
    x_frame_options: str = "DENY"
    
    # Feature Flags
    feature_excel_integration: bool = True
    feature_real_time_updates: bool = True
    feature_advanced_analytics: bool = True
    feature_api_documentation: bool = True
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON string format from environment
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Handle comma-separated string format
                return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_file_types', pre=True)
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [ext.strip() for ext in v.split(',')]
        return v
    
    def get_database_url(self) -> str:
        """Construct database URL from components"""
        if hasattr(self, 'database_url') and self.database_url:
            return self.database_url
        
        # Construct from components
        ssl_suffix = f"?sslmode={self.postgres_ssl_mode}" if self.postgres_ssl_mode != "prefer" else ""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_suffix}"
    
    def get_redis_url(self) -> str:
        """Construct Redis URL from components"""
        if hasattr(self, 'redis_url') and self.redis_url and not self.redis_password:
            return self.redis_url
        
        # Construct from components with password if provided
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}//{auth}{self.redis_host}:{self.redis_port}"
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env.development"
        case_sensitive = False
        
        @property
        def env_file_path(self):
            """Dynamically select environment file based on ENVIRONMENT variable"""
            env = os.getenv("ENVIRONMENT", "development").lower()
            return f".env.{env}"


class QuantLibConfig:
    """QuantLib specific configuration and initialization"""
    
    @staticmethod
    def initialize():
        """Initialize QuantLib settings"""
        # Set evaluation date to today if auto-enabled
        if settings.quantlib_date_today_auto:
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()
    
    @staticmethod
    def get_day_count(day_count_name: str = None):
        """Get QuantLib day count convention"""
        day_count_name = day_count_name or settings.default_day_count
        
        day_count_map = {
            "Actual360": ql.Actual360(),
            "Actual365": ql.Actual365Fixed(),
            "ActualActual": ql.ActualActual(ql.ActualActual.ISDA),
            "Thirty360": ql.Thirty360(ql.Thirty360.USA)
        }
        
        return day_count_map.get(day_count_name, ql.Actual360())
    
    @staticmethod
    def get_calendar(calendar_name: str = None):
        """Get QuantLib business calendar"""
        calendar_name = calendar_name or settings.default_business_calendar
        
        if calendar_name == "UnitedStates.NYSE":
            return ql.UnitedStates(ql.UnitedStates.NYSE)
        elif calendar_name == "TARGET":
            return ql.TARGET()
        else:
            return ql.UnitedStates(ql.UnitedStates.NYSE)


# Global settings instance
settings = Settings()

# Initialize QuantLib on import
QuantLibConfig.initialize()