# 🔧 CLO System Configuration Guide

**Last updated**: November 8, 2026
**Source of truth**: `backend/app/core/config.py` (`Settings`, a pydantic `BaseSettings` class)

All backend configuration lives in one class, `Settings`, exposed as the module-level
`settings` object. There is no other configuration module (`config_manager.py` was removed
on 2026-11-08 because nothing used it).

---

## 🎯 How configuration is loaded

`Settings` reads values in this order (first match wins):

1. **Process environment variables** (e.g. `export SECRET_KEY=...`, Docker `environment:`)
2. **`.env.development` in the current working directory** - always this file name,
   whatever `ENVIRONMENT` is set to. When the backend is started from `backend/`, this is
   `backend/.env.development`.
3. **Defaults in `config.py`** - development-only values (local database, dev secret).

Variable names are case-insensitive and match the field names in `config.py`
(`secret_key` ↔ `SECRET_KEY`). Variables that don't match a field are silently ignored.

> ⚠️ Because step 2 always reads `.env.development`, a production host must provide its real
> values as environment variables (step 1). The production safety check below stops the app
> from starting if development values leak through.

### Production safety check

On import, `config.py` calls `settings.validate_production_safety()`. When
`ENVIRONMENT=production` the app **refuses to start** if any of these hold:

| Check | Fails when |
|---|---|
| `SECRET_KEY` | missing, shorter than 32 characters, or a placeholder/dev value (`dev-…`, `CHANGE_THIS…`, `your_secret…`, unresolved `${…}`) |
| `DEBUG` | true |
| Database credentials | `DATABASE_URL` or `POSTGRES_PASSWORD` still contains the development password |

All failures are reported together in one `RuntimeError`. Outside production the check is a no-op.

---

## ⚙️ Settings reference (most used)

### Environment
```bash
ENVIRONMENT=development   # development | production (only "production" changes behaviour)
DEBUG=false               # default false; .env.development sets true
LOG_LEVEL=INFO
```

### Database
```bash
# The engine connects with DATABASE_URL. The POSTGRES_* fields exist but are NOT used to
# build the connection while DATABASE_URL is set (it always is - it has a default).
DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5433/clo_dev

# Connection pool (one pool for the whole app - see "Database access in code")
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false             # true logs every SQL statement (very noisy)
```

### Redis
```bash
REDIS_URL=redis://127.0.0.1:6379
# REDIS_HOST / REDIS_PORT / REDIS_SSL are only used when REDIS_PASSWORD is set,
# in which case the URL is built from them.
REDIS_PASSWORD=
```
If Redis is unreachable the app still runs; caching is simply disabled.

### Security
```bash
SECRET_KEY=<random, 32+ chars>   # signs JWT access tokens - the ONLY signing key
ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_ALGORITHM=HS256
```
> `JWT_SECRET_KEY` appears in some older env files and docs but **is not read by the code**.
> Set `SECRET_KEY`.

Generate a key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### CORS
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3002   # JSON list or comma-separated
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=3600
```

### Rate limiting, logging, monitoring, storage, email, backups, feature flags
See the corresponding sections of `config.py` (`RATE_LIMIT_*`, `LOG_*`, `PROMETHEUS_*`,
`STORAGE_BACKEND`, `SMTP_*`, `BACKUP_*`, `FEATURE_*`). Every field there can be set by an
environment variable of the same name.

### Analysis date
```bash
DEFAULT_ANALYSIS_DATE=2016-03-23   # as-of date used when a request doesn't pass analysis_date
```
The single source for the default. Requests may pass any date from 2010-01-01 to 2035-12-31
(`?analysis_date=YYYY-MM-DD`, or an `analysis_date` field in request bodies); invalid or
out-of-range dates return 422. QuantLib's global evaluation date is initialised to this value
(it used to be the real current date). Implementation: `backend/app/core/analysis_date.py`.

Note: the portfolio data is a snapshot as of 2016-03-23 (the workbook's analysis date).
Changing the analysis date moves time-based measures such as years-to-maturity, but does not
roll holdings forward.

### Not configurable
Older versions of this guide listed `MAX_PORTFOLIO_SIZE`, `MAX_ASSET_COUNT`,
`CALCULATION_PRECISION`, `ENABLE_PERFORMANCE_FEATURES`, `ENABLE_WATERFALL_CACHING`,
`JWT_REFRESH_TOKEN_EXPIRE_DAYS`, `ALLOWED_HOSTS`, `CORS_CREDENTIALS`, `CORS_METHODS` and
`CORS_HEADERS`. None of these are read by the code. `QUANTLIB_DATE_TODAY_AUTO` was removed on
2026-11-08 (QuantLib now follows the analysis date).

---

## 📊 Usage in code

```python
from app.core.config import settings

settings.database_url
settings.secret_key
settings.is_production()      # methods, not properties
settings.is_development()
settings.get_redis_url()
```

### Database access in code

`backend/app/core/database.py` is the single owner of database and cache connections:

```python
from app.core.database import get_db, session_scope, get_redis, Base, engine

# FastAPI endpoints
@router.get("/things")
async def list_things(db: Session = Depends(get_db)):
    ...

# Services, scripts, background code
with session_scope() as session:
    session.execute(text("SELECT 1"))

redis_client = get_redis()    # shared client, or None if Redis is down; returns bytes
```

- `get_db()` and `session_scope()` **commit when the block finishes without an exception and
  roll back otherwise**. Explicit `commit()` calls are harmless.
- There is one engine/connection pool. Do not create engines or `declarative_base()`
  elsewhere, and do not define per-module `get_db()` helpers.
- `app/core/database_config.py` (`db_config`) is a **deprecated shim** kept only for old
  standalone scripts. Application code must not import it.

### Authentication dependencies in code

All auth dependencies come from `backend/app/core/unified_auth.py`:

```python
from app.core.unified_auth import (
    get_current_user,         # user dict; 401 if token missing/invalid
    get_current_active_user,
    get_current_user_id,      # just the user's id (str)
    require_admin_role, require_manager_role, require_analyst_role,
    require_permissions, get_optional_user,
)
```

Do not import these from `app.core.security` or `app.api.v1.endpoints.auth` (those
re-exports/duplicates were removed). Most routers already get authentication at router level
in `app/api/v1/api.py`; add role/permission dependencies on individual endpoints as needed.

---

## 🚀 Deployment

```yaml
# docker-compose (example)
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - SECRET_KEY=${PRODUCTION_SECRET_KEY}
      - DATABASE_URL=postgresql://clo_app:${DB_PASSWORD}@db:5432/clo_prod
      - REDIS_URL=redis://redis:6379
```

Provide secrets through the orchestrator's secret store, not committed files.

---

## 🔍 Troubleshooting

```bash
cd backend && venv\Scripts\activate

# What did Settings resolve?
python -c "from app.core.config import settings as s; print(s.environment, s.debug, s.database_url)"

# Would production start with the current environment?
set ENVIRONMENT=production
python -c "import app.core.config"     # raises RuntimeError listing every problem

# Database / Redis reachable?
python -c "from app.core.database import DatabaseManager as d; print(d.health_check())"
```

---

## 📚 Environment files

| File | Purpose | Committed |
|---|---|---|
| `.env.template` | Reference of available variables | Yes |
| `.env.development`, `backend/.env.development` | Local development values (read automatically) | Yes (contain dev credentials - see note) |
| `.env.production`, `backend/.env.production` | Production template with placeholders | Yes |
| `frontend/.env.development` | `REACT_APP_API_URL` for the React app | Yes |

> **Note:** The development env files currently contain the local database password and are
> tracked in git. Treat that password as compromised: rotate it, untrack the files, and keep
> only `.env.template` in git.
