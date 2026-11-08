"""
Test-suite database isolation.

Several tests run Base.metadata.create_all()/drop_all() against the application's
engine. On 2026-11-08 that wiped the development database (clo_dev). This conftest makes
that impossible by pointing the application at a separate test database *before* any
application module is imported:

  1. Pick the test database URL:
       - TEST_DATABASE_URL, if set; otherwise
       - the development DATABASE_URL (environment or backend/.env.development) with the
         database name replaced by "<name>_test" (clo_dev -> clo_dev_test).
  2. Refuse to run (pytest.exit) unless the test database name contains "test" and differs
     from the development database name.
  3. Export it as DATABASE_URL (process environment beats .env files in Settings).
  4. Create the test database if it does not exist.
  5. Import app.core.database and verify the engine really points at the test database.

pytest loads this file before collecting any test module in this directory tree, so the
override is in place before `app` is imported.
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _read_env_file(path: Path) -> dict:
    """Minimal KEY=VALUE parser for the dev env file (no app imports allowed yet)."""
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip().upper()] = value.strip().strip('"').strip("'")
    return values


def _dev_database_url() -> str:
    url = os.environ.get("DATABASE_URL") or _read_env_file(BACKEND_DIR / ".env.development").get("DATABASE_URL")
    if not url:
        pytest.exit("conftest: cannot determine DATABASE_URL to derive the test database from", returncode=4)
    return url


def _resolve_test_url():
    dev_url = make_url(_dev_database_url())
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        test_url = make_url(explicit)
    elif "test" in (dev_url.database or "").lower():
        test_url = dev_url  # DATABASE_URL already names a test database; use it as-is
    else:
        test_url = dev_url.set(database=f"{dev_url.database}_test")

    name = test_url.database or ""
    if "test" not in name.lower() or (name == dev_url.database and test_url is not dev_url):
        pytest.exit(
            f"conftest: refusing to run - test database '{name}' must contain 'test' and differ "
            f"from the development database '{dev_url.database}'",
            returncode=4,
        )
    return dev_url, test_url


def _ensure_database_exists(test_url) -> None:
    """CREATE DATABASE <test db> if missing. Failures are reported, not fatal:
    tests that don't need PostgreSQL can still run."""
    admin = create_engine(test_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": test_url.database}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"\n[conftest] WARNING: could not verify/create test database "
              f"'{test_url.database}': {exc}\n")
    finally:
        admin.dispose()


_DEV_URL, _TEST_URL = _resolve_test_url()
os.environ["DATABASE_URL"] = _TEST_URL.render_as_string(hide_password=False)
os.environ.setdefault("ENVIRONMENT", "testing")
_ensure_database_exists(_TEST_URL)

# Last line of defence: the real application engine must point at the test database.
from app.core.database import engine as _app_engine  # noqa: E402

if _app_engine.url.database != _TEST_URL.database:
    pytest.exit(
        f"conftest: application engine points at '{_app_engine.url.database}', expected test "
        f"database '{_TEST_URL.database}'. Was app.core.database imported before conftest?",
        returncode=4,
    )


def pytest_report_header(config):
    return (f"database isolation: tests use '{_TEST_URL.database}' on "
            f"{_TEST_URL.host}:{_TEST_URL.port} (development database '{_DEV_URL.database}' is not touched)")
