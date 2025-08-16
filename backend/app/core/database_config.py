"""
Production Database Configuration
Handles both SQLite (migrated data) and PostgreSQL (operational) databases
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from typing import Optional
from contextlib import contextmanager

# Base class for SQLAlchemy models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration manager for CLO system"""
    
    def __init__(self):
        # Production PostgreSQL Database  
        self.postgresql_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:adamchaz@127.0.0.1:5433/clo_dev'
        )
        
        # Migrated Data SQLite Databases (read-only)
        # Get absolute paths to database files (they're in backend/data/databases)
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up from app/core to backend
        db_dir = os.path.join(backend_dir, "data", "databases")
        self.migration_databases = {
            'assets': f'sqlite:///{os.path.join(db_dir, "clo_assets_production.db")}',
            'correlations': f'sqlite:///{os.path.join(db_dir, "clo_correlations.db")}',
            'scenarios': f'sqlite:///{os.path.join(db_dir, "clo_mag_scenarios.db")}',
            'config': f'sqlite:///{os.path.join(db_dir, "clo_model_config.db")}',
            'reference': f'sqlite:///{os.path.join(db_dir, "clo_reference_quick.db")}'
        }
        
        # Redis for caching
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Initialize database engines
        self.engines = {}
        self.sessions = {}
        self._setup_engines()
        
        # Redis client
        self.redis_client = None
        self._setup_redis()
    
    def _setup_engines(self):
        """Initialize database engines"""
        
        # Production PostgreSQL engine
        self.engines['postgresql'] = create_engine(
            self.postgresql_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )
        
        # Session factory for PostgreSQL
        self.sessions['postgresql'] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engines['postgresql']
        )
        
        # Migration database engines (read-only)
        for db_name, db_url in self.migration_databases.items():
            self.engines[db_name] = create_engine(
                db_url,
                poolclass=StaticPool,
                pool_pre_ping=True,
                connect_args={"check_same_thread": False}
            )
            
            # Session factory for each migration database
            self.sessions[db_name] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engines[db_name]
            )
    
    def _setup_redis(self):
        """Initialize Redis client"""
        try:
            self.redis_client = redis.Redis.from_url(self.redis_url)
            # Test connection
            self.redis_client.ping()
            print("[OK] Redis connection established")
        except Exception as e:
            print(f"[WARNING] Redis connection failed: {e}")
            self.redis_client = None
    
    @contextmanager
    def get_db_session(self, database: str = 'postgresql'):
        """
        Get database session with automatic cleanup
        
        Args:
            database: Database name ('postgresql', 'assets', 'correlations', etc.)
        """
        if database not in self.sessions:
            raise ValueError(f"Unknown database: {database}")
        
        session = self.sessions[database]()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_engine(self, database: str = 'postgresql'):
        """Get database engine"""
        if database not in self.engines:
            raise ValueError(f"Unknown database: {database}")
        return self.engines[database]
    
    def create_all_tables(self):
        """Create all tables in production database"""
        try:
            Base.metadata.create_all(bind=self.engines['postgresql'])
            print("✅ All operational database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False
    
    def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client for caching"""
        return self.redis_client
    
    def health_check(self) -> dict:
        """Perform health check on all database connections"""
        status = {
            'postgresql': False,
            'redis': False,
            'migration_databases': {}
        }
        
        # Check PostgreSQL
        try:
            with self.get_db_session('postgresql') as session:
                session.execute('SELECT 1')
                status['postgresql'] = True
        except Exception:
            status['postgresql'] = False
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                status['redis'] = True
            except Exception:
                status['redis'] = False
        
        # Check migration databases
        for db_name in self.migration_databases.keys():
            try:
                with self.get_db_session(db_name) as session:
                    session.execute('SELECT 1')
                    status['migration_databases'][db_name] = True
            except Exception:
                status['migration_databases'][db_name] = False
        
        return status

# Global database configuration instance
db_config = DatabaseConfig()

# Convenience functions
def get_db_session(database: str = 'postgresql'):
    """Get database session - convenience function"""
    return db_config.get_db_session(database)

def get_engine(database: str = 'postgresql'):
    """Get database engine - convenience function"""
    return db_config.get_engine(database)

def get_redis():
    """Get Redis client - convenience function"""
    return db_config.get_redis_client()