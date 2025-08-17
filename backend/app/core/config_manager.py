"""
Enhanced Configuration Management System
Centralized environment-aware configuration with validation and security
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from functools import lru_cache
import QuantLib as ql

logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    """Database-specific configuration"""
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="127.0.0.1", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5433, env="POSTGRES_PORT") 
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="adamchaz", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="clo_dev", env="POSTGRES_DB")
    postgres_ssl_mode: str = Field(default="disable", env="POSTGRES_SSL_MODE")
    
    # Connection Pool Settings
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class RedisSettings(BaseSettings):
    """Redis-specific configuration"""
    
    redis_host: str = Field(default="127.0.0.1", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components"""
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class SecuritySettings(BaseSettings):
    """Security-specific configuration"""
    
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class CORSSettings(BaseSettings):
    """CORS-specific configuration"""
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], env="CORS_METHODS")
    cors_headers: Union[str, List[str]] = Field(default="*", env="CORS_HEADERS")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @validator('cors_methods', pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',') if method.strip()]
        return v
    
    @validator('cors_headers', pre=True)  
    def parse_cors_headers(cls, v):
        if isinstance(v, str) and v != "*":
            return [header.strip() for header in v.split(',') if header.strip()]
        return v
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class BusinessLogicSettings(BaseSettings):
    """Business logic configuration"""
    
    default_analysis_date: str = Field(default="2016-03-23", env="DEFAULT_ANALYSIS_DATE")
    max_portfolio_size: int = Field(default=10000, env="MAX_PORTFOLIO_SIZE")
    max_asset_count: int = Field(default=5000, env="MAX_ASSET_COUNT")
    calculation_precision: int = Field(default=8, env="CALCULATION_PRECISION")
    enable_performance_features: bool = Field(default=True, env="ENABLE_PERFORMANCE_FEATURES")
    enable_waterfall_caching: bool = Field(default=True, env="ENABLE_WATERFALL_CACHING")
    
    # QuantLib Configuration
    quantlib_calendar: str = Field(default="UnitedStates", env="QUANTLIB_CALENDAR")
    quantlib_daycount: str = Field(default="Actual/360", env="QUANTLIB_DAYCOUNT")
    quantlib_date_format: str = Field(default="%Y-%m-%d", env="QUANTLIB_DATE_FORMAT")
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration"""
    
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="plain", env="LOG_FORMAT")
    log_file_path: str = Field(default="logs/clo_system.log", env="LOG_FILE_PATH")
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class AppSettings(BaseSettings):
    """Main application settings that combines all configuration sections"""
    
    # Environment Configuration
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    max_workers: int = Field(default=1, env="MAX_WORKERS")
    worker_timeout: int = Field(default=60, env="WORKER_TIMEOUT")
    keep_alive: int = Field(default=2, env="KEEP_ALIVE")
    max_requests: int = Field(default=1000, env="MAX_REQUESTS")
    max_requests_jitter: int = Field(default=100, env="MAX_REQUESTS_JITTER")
    
    # Frontend Configuration
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    api_base_url: str = Field(default="http://localhost:8000", env="API_BASE_URL")
    
    # Configuration sections
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    cors: CORSSettings = CORSSettings()
    business: BusinessLogicSettings = BusinessLogicSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['development', 'testing', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize subsection configurations
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.security = SecuritySettings()
        self.cors = CORSSettings()
        self.business = BusinessLogicSettings()
        self.monitoring = MonitoringSettings()

class ConfigManager:
    """Configuration manager with environment-specific loading"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.env_file = env_file or self._determine_env_file()
        self._settings: Optional[AppSettings] = None
    
    def _determine_env_file(self) -> str:
        """Determine which environment file to load"""
        environment = os.getenv("ENVIRONMENT", "development")
        
        # Check for environment-specific files
        env_files = {
            "development": ".env.development",
            "testing": ".env.testing", 
            "staging": ".env.staging",
            "production": ".env.production"
        }
        
        env_file = env_files.get(environment, ".env")
        env_path = self.project_root / env_file
        
        # Fall back to .env if specific file doesn't exist
        if not env_path.exists():
            fallback_path = self.project_root / ".env"
            if fallback_path.exists():
                logger.warning(f"Environment file {env_file} not found, using .env")
                return ".env"
        
        return env_file
    
    def load_environment_file(self):
        """Load environment variables from file"""
        env_path = self.project_root / self.env_file
        
        if env_path.exists():
            logger.info(f"Loading environment from: {env_path}")
            # Load environment file
            from dotenv import load_dotenv
            load_dotenv(env_path)
        else:
            logger.warning(f"Environment file {env_path} not found, using system environment variables")
    
    @property
    def settings(self) -> AppSettings:
        """Get application settings (cached)"""
        if self._settings is None:
            self.load_environment_file()
            self._settings = AppSettings()
            logger.info(f"Configuration loaded for environment: {self._settings.environment}")
        return self._settings
    
    def reload_settings(self):
        """Force reload of settings"""
        self._settings = None
        return self.settings
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return validation report"""
        validation_report = {
            "environment": self.settings.environment,
            "config_file": self.env_file,
            "warnings": [],
            "errors": [],
            "security_issues": []
        }
        
        # Security validations
        if self.settings.is_production:
            if "dev-secret-key" in self.settings.security.secret_key:
                validation_report["security_issues"].append("Using default development secret key in production")
            
            if "dev-jwt-secret" in self.settings.security.jwt_secret_key:
                validation_report["security_issues"].append("Using default development JWT secret in production")
            
            if self.settings.debug:
                validation_report["security_issues"].append("Debug mode enabled in production")
        
        # Database validations
        try:
            # Test database URL construction
            _ = self.settings.database.database_url
        except Exception as e:
            validation_report["errors"].append(f"Invalid database configuration: {e}")
        
        # Redis validations
        try:
            # Test Redis URL construction
            _ = self.settings.redis.redis_url
        except Exception as e:
            validation_report["errors"].append(f"Invalid Redis configuration: {e}")
        
        return validation_report

# Global configuration manager instance
@lru_cache()
def get_config_manager() -> ConfigManager:
    """Get singleton configuration manager instance"""
    return ConfigManager()

@lru_cache()
def get_settings() -> AppSettings:
    """Get application settings (cached singleton)"""
    return get_config_manager().settings

# For backward compatibility
settings = get_settings()