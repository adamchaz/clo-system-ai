# 🔧 CLO System Configuration Guide

## 📋 **Configuration Management Overview**

The CLO System uses a sophisticated environment-aware configuration management system that supports multiple deployment environments with secure credential handling.

**Date**: August 17, 2025  
**Status**: Production-Ready Configuration System  

---

## 🎯 **Configuration Architecture**

### **Multi-Environment Support**
```
Environment Files:
├── .env.template        # Template with all configuration options
├── .env.development     # Development environment (committed)
├── .env.production      # Production template (secure values needed)
├── .env.testing         # Testing environment (not committed)
└── .env.staging         # Staging environment (not committed)
```

### **Configuration Sections**
1. **Environment Settings** - Basic environment configuration
2. **Database Configuration** - PostgreSQL connection and pooling
3. **Redis Configuration** - Cache and session storage
4. **Security Configuration** - JWT, secrets, and access control
5. **CORS Configuration** - Cross-origin resource sharing
6. **Business Logic Configuration** - CLO-specific settings
7. **Monitoring Configuration** - Logging, metrics, and alerting

---

## 🚀 **Quick Setup**

### **1. Development Environment**
```bash
# Copy development configuration
cp .env.development .env

# Or start with template
cp .env.template .env
# Edit .env with your values
```

### **2. Production Environment**
```bash
# Copy production template
cp .env.production .env

# Fill in secure production values
nano .env
```

### **3. Environment Variables**
```bash
# Set environment type
export ENVIRONMENT=development  # or production, testing, staging
```

---

## ⚙️ **Configuration Sections**

### **Environment Settings**
```bash
ENVIRONMENT=development          # development, testing, staging, production
DEBUG=true                      # Enable debug mode
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

### **Database Configuration**
```bash
# PostgreSQL Database
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=clo_dev
POSTGRES_SSL_MODE=disable       # disable, prefer, require

# Connection Pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### **Redis Configuration**
```bash
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=                 # Optional
REDIS_SSL=false
```

### **Security Configuration**
```bash
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### **CORS Configuration**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3004
CORS_CREDENTIALS=true
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=*
```

### **Business Logic Configuration**
```bash
DEFAULT_ANALYSIS_DATE=2016-03-23
MAX_PORTFOLIO_SIZE=10000
MAX_ASSET_COUNT=5000
CALCULATION_PRECISION=8
ENABLE_PERFORMANCE_FEATURES=true
ENABLE_WATERFALL_CACHING=true
```

---

## 🔒 **Security Best Practices**

### **Development Environment**
- ✅ Use default development credentials
- ✅ Enable debug mode for troubleshooting
- ✅ Extended token expiration for convenience
- ✅ Permissive CORS for local development

### **Production Environment**
- ⚠️ **NEVER use default credentials**
- ⚠️ **Generate secure random secrets (64+ characters)**
- ⚠️ **Disable debug mode**
- ⚠️ **Use SSL/TLS for database connections**
- ⚠️ **Restrict CORS origins to your domain**
- ⚠️ **Use environment variables, not hardcoded values**

### **Secret Generation**
```python
# Generate secure secrets
import secrets
secret_key = secrets.token_urlsafe(64)
jwt_secret = secrets.token_urlsafe(64)
```

---

## 🏗️ **Configuration Loading**

### **Environment File Priority**
1. Environment-specific file (`.env.production`)
2. Generic `.env` file
3. System environment variables
4. Default values in code

### **Configuration Validation**
```python
from backend.app.core.config_manager import get_config_manager

# Validate configuration
config_manager = get_config_manager()
validation_report = config_manager.validate_configuration()

if validation_report['errors']:
    print("Configuration errors:", validation_report['errors'])
if validation_report['security_issues']:
    print("Security issues:", validation_report['security_issues'])
```

---

## 📊 **Usage in Code**

### **Basic Usage**
```python
from backend.app.core.config_manager import get_settings

settings = get_settings()

# Access configuration sections
db_url = settings.database.database_url
redis_url = settings.redis.redis_url
secret = settings.security.secret_key
```

### **Environment-Specific Logic**
```python
if settings.is_development:
    # Development-specific code
    enable_debug_endpoints()

if settings.is_production:
    # Production-specific code
    setup_error_reporting()
```

### **Subsection Access**
```python
# Database settings
db_config = settings.database
connection_url = db_config.database_url
pool_size = db_config.db_pool_size

# Security settings
security_config = settings.security
jwt_secret = security_config.jwt_secret_key
token_expiry = security_config.jwt_access_token_expire_minutes

# Business logic settings
business_config = settings.business
default_date = business_config.default_analysis_date
max_portfolio = business_config.max_portfolio_size
```

---

## 🔧 **Advanced Configuration**

### **Custom Configuration Loading**
```python
from backend.app.core.config_manager import ConfigManager

# Load specific environment file
config_manager = ConfigManager(env_file=".env.custom")
settings = config_manager.settings
```

### **Runtime Configuration Changes**
```python
# Reload configuration (useful for testing)
config_manager.reload_settings()
```

### **Configuration Validation in CI/CD**
```python
#!/usr/bin/env python3
"""Configuration validation script for CI/CD"""

from backend.app.core.config_manager import get_config_manager

def validate_config():
    config_manager = get_config_manager()
    report = config_manager.validate_configuration()
    
    if report['errors']:
        print(f"❌ Configuration errors: {report['errors']}")
        exit(1)
    
    if report['security_issues']:
        print(f"⚠️  Security issues: {report['security_issues']}")
        exit(1)
    
    print("✅ Configuration validation passed")

if __name__ == "__main__":
    validate_config()
```

---

## 🚀 **Deployment Configurations**

### **Docker Environment**
```dockerfile
# Dockerfile
ENV ENVIRONMENT=production
ENV POSTGRES_HOST=db
ENV REDIS_HOST=redis
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    environment:
      - ENVIRONMENT=production
      - POSTGRES_HOST=db
      - REDIS_HOST=redis
    env_file:
      - .env.production
```

### **Kubernetes ConfigMap**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: clo-system-config
data:
  ENVIRONMENT: "production"
  POSTGRES_HOST: "postgresql-service"
  REDIS_HOST: "redis-service"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Configuration Not Loading**
```bash
# Check environment file exists
ls -la .env*

# Validate environment variables
python -c "import os; print(os.environ.get('ENVIRONMENT', 'not set'))"

# Test configuration loading
python -c "from backend.app.core.config_manager import get_settings; print(get_settings().environment)"
```

#### **Database Connection Issues**
```python
# Test database configuration
from backend.app.core.config_manager import get_settings

settings = get_settings()
print(f"Database URL: {settings.database.database_url}")
print(f"Pool size: {settings.database.db_pool_size}")
```

#### **Security Warnings**
```python
# Validate production security
from backend.app.core.config_manager import get_config_manager

config_manager = get_config_manager()
report = config_manager.validate_configuration()

for issue in report['security_issues']:
    print(f"Security Issue: {issue}")
```

### **Configuration Debug Mode**
```python
# Enable detailed configuration logging
import logging
logging.getLogger('backend.app.core.config_manager').setLevel(logging.DEBUG)
```

---

## 📚 **Configuration Files Reference**

| **File** | **Purpose** | **Committed** | **Usage** |
|----------|-------------|---------------|-----------|
| `.env.template` | Configuration template with all options | ✅ Yes | Reference and setup guide |
| `.env.development` | Development environment defaults | ✅ Yes | Local development |
| `.env.production` | Production configuration template | ✅ Yes | Production deployment template |
| `.env.testing` | Testing environment | ❌ No | CI/CD testing |
| `.env.staging` | Staging environment | ❌ No | Pre-production staging |
| `.env` | Active environment file | ❌ No | Runtime configuration |

---

## 🎯 **Best Practices**

### **Development**
1. Use `.env.development` as starting point
2. Override specific values in local `.env`
3. Never commit `.env` with personal credentials
4. Use permissive settings for easier debugging

### **Production**
1. Start with `.env.production` template
2. Generate secure random secrets
3. Use environment variables in container orchestration
4. Validate configuration in deployment pipeline
5. Monitor configuration drift

### **Security**
1. Rotate secrets regularly
2. Use least-privilege database accounts
3. Restrict CORS origins in production
4. Enable SSL/TLS for all connections
5. Monitor for configuration exposure

---

**Status**: 🔧 **CONFIGURATION SYSTEM COMPLETE - PRODUCTION READY**  
**Features**: Multi-environment support, security validation, structured configuration management