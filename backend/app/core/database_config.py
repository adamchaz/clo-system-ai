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
        
        # All data now unified in PostgreSQL - no more separate SQLite databases
        # Migration completed: 258,989 rows successfully migrated to PostgreSQL
        # Tables: asset_correlations, scenario_inputs, model_parameters, reference_data
        self.migration_databases = {}
        
        # Note: SQLite databases fully migrated to PostgreSQL on 2025-08-17
        
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
        
        # All migrated data is now available through the main PostgreSQL engine
        # No separate engines needed - unified database architecture
    
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
            database: Database name ('postgresql' or legacy names like 'correlations', 'scenarios', etc.)
                     All legacy database names now map to PostgreSQL after migration
        """
        # Map all legacy database names to PostgreSQL (backward compatibility)
        legacy_database_mapping = {
            'correlations': 'postgresql',
            'scenarios': 'postgresql',
            'config': 'postgresql',
            'reference': 'postgresql',
            'assets': 'postgresql'  # In case any old code still references this
        }
        
        # Use mapping if it's a legacy name, otherwise use the provided name
        actual_database = legacy_database_mapping.get(database, database)
        
        if actual_database not in self.sessions:
            raise ValueError(f"Unknown database: {database} (mapped to {actual_database})")
        
        session = self.sessions[actual_database]()
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
        # Map legacy database names to PostgreSQL
        legacy_database_mapping = {
            'correlations': 'postgresql',
            'scenarios': 'postgresql',
            'config': 'postgresql',
            'reference': 'postgresql',
            'assets': 'postgresql'
        }
        
        actual_database = legacy_database_mapping.get(database, database)
        
        if actual_database not in self.engines:
            raise ValueError(f"Unknown database: {database} (mapped to {actual_database})")
        return self.engines[actual_database]
    
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