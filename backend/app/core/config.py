"""
CLO System Configuration Management
Handles environment variables and application settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
import QuantLib as ql


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    database_url: str = "postgresql://postgres:adamchaz@127.0.0.1:5433/clo_dev"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433
    postgres_user: str = "postgres"
    postgres_password: str = "adamchaz"
    postgres_db: str = "clo_dev"
    
    # Redis Configuration  
    redis_url: str = "redis://127.0.0.1:6379"
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    
    # Application Configuration
    environment: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Security Configuration
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # QuantLib Configuration
    quantlib_date_today_auto: bool = True
    
    # CLO System Specific
    max_assets: int = 10000
    max_correlations: int = 1000000
    default_day_count: str = "Actual360"
    default_business_calendar: str = "UnitedStates.NYSE"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env.development"
        case_sensitive = False


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