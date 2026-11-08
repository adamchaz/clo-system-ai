"""
CLO System Database Configuration

The single place that owns database and cache connections:
  - one SQLAlchemy engine / connection pool, configured from app.core.config
  - one declarative Base for every model
  - get_db()         FastAPI dependency
  - session_scope()  context manager for services and scripts
  - get_redis()      shared Redis client (or None when Redis is unavailable)

Sessions from get_db() and session_scope() commit when the block finishes
without an exception and roll back otherwise, so callers don't need to commit
explicitly (explicit commits are still fine).
"""

import logging
from contextlib import contextmanager
from typing import Dict, Iterator, Optional

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy engine: the only connection pool in the application
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    echo=settings.db_echo,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy models
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yields a session, commits on success, rolls back on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for non-request code; same commit/rollback semantics as get_db()."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Redis: one shared client. Values are returned as bytes (callers decode / json.loads).
_redis_client: Optional[redis.Redis] = None
_redis_checked = False


def get_redis() -> Optional[redis.Redis]:
    """Return the shared Redis client, or None if Redis was unreachable on first use."""
    global _redis_client, _redis_checked
    if not _redis_checked:
        _redis_checked = True
        try:
            client = redis.Redis.from_url(settings.get_redis_url())
            client.ping()
            _redis_client = client
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            _redis_client = None
    return _redis_client


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
    def test_connection() -> bool:
        """Test database connection"""
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False

    @staticmethod
    def test_redis() -> bool:
        """Test Redis connection"""
        client = get_redis()
        if client is None:
            return False
        try:
            client.ping()
            return True
        except Exception:
            return False

    @staticmethod
    def health_check() -> Dict[str, bool]:
        """Health of PostgreSQL and Redis, as {'postgresql': bool, 'redis': bool}"""
        return {
            "postgresql": DatabaseManager.test_connection(),
            "redis": DatabaseManager.test_redis(),
        }
