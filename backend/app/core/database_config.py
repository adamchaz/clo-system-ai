"""
DEPRECATED compatibility shim - use app.core.database instead.

Application code no longer imports this module. It remains only so the
standalone migration/utility scripts that still do
`from app.core.database_config import db_config` keep working. It owns no
engine, Base, or configuration of its own; everything delegates to
app.core.database, so there is a single connection pool.
"""

from contextlib import contextmanager

from .database import Base, DatabaseManager, engine, get_redis, session_scope  # noqa: F401


class DatabaseConfig:
    """Thin adapter preserving the old db_config API on top of app.core.database."""

    @contextmanager
    def get_db_session(self, database: str = "postgresql"):
        # Legacy names ('correlations', 'scenarios', 'assets', ...) all live in PostgreSQL.
        with session_scope() as session:
            yield session

    def get_engine(self, database: str = "postgresql"):
        return engine

    def get_redis_client(self):
        return get_redis()

    def health_check(self) -> dict:
        return DatabaseManager.health_check()


db_config = DatabaseConfig()


def get_db_session(database: str = "postgresql"):
    return db_config.get_db_session(database)


def get_engine(database: str = "postgresql"):
    return engine
