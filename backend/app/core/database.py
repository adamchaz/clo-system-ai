"""
CLO System Database Configuration
Handles SQLAlchemy database connections and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from .config import settings

# SQLAlchemy Database Engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug  # Echo SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Redis connection
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Dependency to get Redis client"""
    return redis_client


class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def create_tables():
        """Create all database tables"""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_tables():
        """Drop all database tables"""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    @staticmethod
    def test_redis():
        """Test Redis connection"""
        try:
            redis_client.ping()
            return True
        except Exception:
            return False