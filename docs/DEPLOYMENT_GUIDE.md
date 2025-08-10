# CLO Management System - Deployment Guide

## 🚀 **PRODUCTION DEPLOYMENT GUIDE**

**Version**: 1.0.0  
**Last Updated**: August 10, 2024  
**Status**: Production Ready  

This comprehensive guide covers deploying the CLO Management System in development, staging, and production environments with complete infrastructure setup, security configuration, and monitoring.

---

## 📋 **TABLE OF CONTENTS**

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Production Configuration](#production-configuration)
6. [Security Setup](#security-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Troubleshooting](#troubleshooting)

---

## 🔧 **PREREQUISITES**

### **System Requirements**

**Development Environment:**
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 18.04+
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **CPU**: 4 cores minimum

**Production Environment:**
- **OS**: Ubuntu 20.04 LTS or CentOS 8+
- **RAM**: 32GB minimum, 64GB recommended
- **Disk**: 500GB SSD with backup storage
- **CPU**: 8 cores minimum, 16 cores recommended
- **Network**: Static IP with firewall configuration

### **Required Software**

#### **Core Components**
```bash
# Docker & Docker Compose
Docker Engine 20.10+
Docker Compose 2.0+

# Python Environment
Python 3.11+
pip 23.0+

# Node.js (for frontend)
Node.js 18.0+
npm 8.0+

# Database Systems
PostgreSQL 15+
Redis 7.0+
```

#### **Optional Tools**
```bash
# Monitoring
Grafana 10.0+
Prometheus 2.45+

# Load Balancing
Nginx 1.20+

# SSL/TLS
Certbot (Let's Encrypt)
```

---

## 🌍 **ENVIRONMENT SETUP**

### **1. Repository Setup**

```bash
# Clone repository
git clone https://github.com/your-org/clo-management-system.git
cd clo-management-system

# Create environment files
cp .env.development.template .env.development
cp .env.production.template .env.production

# Set up development environment
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

### **2. Python Environment**

#### **Development Setup**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS  
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### **Production Setup**
```bash
# System-wide installation (using systemd service)
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Create application user
sudo useradd -m -s /bin/bash clo-app
sudo su - clo-app

# Set up application environment
cd /opt/clo-management-system
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### **3. Node.js Environment**

#### **Development Setup**
```bash
cd frontend
npm install
npm run build:dev
```

#### **Production Setup**
```bash
cd frontend
npm ci --production
npm run build:prod
```

---

## 🗄️ **DATABASE CONFIGURATION**

### **PostgreSQL Setup**

#### **Development (Local)**
```bash
# Install PostgreSQL (Ubuntu)
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE clo_management;
CREATE USER clo_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE clo_management TO clo_user;
\q
```

#### **Production Setup**
```bash
# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

# Configure PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf

# Key production settings:
listen_addresses = 'localhost'
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
wal_level = replica
max_wal_size = 2GB
min_wal_size = 80MB

# Configure authentication
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add application connection
local   clo_management  clo_user                md5
host    clo_management  clo_user  127.0.0.1/32  md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### **Database Initialization**
```bash
# Run database migrations
cd backend
alembic upgrade head

# Initialize with production data
python scripts/init_production_db.py
```

### **Redis Setup**

#### **Development (Local)**
```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### **Production Setup**
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Production settings:
bind 127.0.0.1
port 6379
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10  
save 60 10000

# Security
requirepass your_redis_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""

# Start Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### **Migration Databases Setup**

The system uses 5 specialized SQLite databases for migrated data:

```bash
# Verify migration databases
ls -la *.db
# Should show:
# clo_assets.db (384 assets)
# clo_correlations.db (238,144 correlations) 
# clo_mag_scenarios.db (19,795 parameters)
# clo_model_config.db (356 parameters)
# clo_reference_quick.db (694 records)

# Set proper permissions
chmod 644 *.db
chown clo-app:clo-app *.db
```

---

## 🐳 **DOCKER DEPLOYMENT**

### **Development Environment**

```bash
# Start development stack
cd infrastructure/docker
docker-compose -f docker-compose.development.yml up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f clo_backend
```

### **Production Deployment**

#### **1. Production Docker Compose**
```yaml
# infrastructure/docker/docker-compose.production.yml
version: '3.8'

services:
  postgresql:
    image: postgres:15-alpine
    container_name: clo_postgresql_prod
    environment:
      POSTGRES_DB: clo_management
      POSTGRES_USER: clo_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgresql_data_prod:/var/lib/postgresql/data
      - ./postgresql/init:/docker-entrypoint-initdb.d
      - /opt/clo-backups:/backups
    restart: unless-stopped
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB

  redis:
    image: redis:7-alpine
    container_name: clo_redis_prod
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data_prod:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf

  clo_backend:
    build:
      context: ../../backend
      dockerfile: Dockerfile.production
    container_name: clo_backend_prod
    environment:
      DATABASE_URL: postgresql://clo_user:${POSTGRES_PASSWORD}@postgresql:5432/clo_management
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: production
      LOG_LEVEL: info
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ../../:/app/data:ro
      - /var/log/clo-system:/app/logs
    depends_on:
      - postgresql
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: clo_nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /var/log/nginx:/var/log/nginx
    depends_on:
      - clo_backend
    restart: unless-stopped

volumes:
  postgresql_data_prod:
  redis_data_prod:
```

#### **2. Production Environment Variables**
```bash
# .env.production
# Database Configuration
POSTGRES_PASSWORD=your_secure_db_password_here
DATABASE_URL=postgresql://clo_user:your_secure_db_password@localhost:5432/clo_management

# Redis Configuration
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# Security Configuration  
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
ENCRYPTION_KEY=your_32_character_encryption_key_here

# API Configuration
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
API_BASE_URL=https://api.your-domain.com/api/v1

# Monitoring
GRAFANA_PASSWORD=your_grafana_password
LOG_LEVEL=info

# Feature Flags
ENABLE_CORRELATION_CACHE=true
ENABLE_SCENARIO_CACHE=true
ENABLE_PERFORMANCE_MONITORING=true

# Backup Configuration
BACKUP_RETENTION_DAYS=30
ENABLE_AUTOMATED_BACKUP=true
```

#### **3. Start Production Environment**
```bash
# Load environment variables
source .env.production

# Start production stack
docker-compose -f docker-compose.production.yml up -d

# Verify all services are healthy
docker-compose ps
docker-compose logs clo_backend
```

### **Container Health Monitoring**
```bash
# Check service health
curl http://localhost:8000/health

# Monitor container resources
docker stats

# View application logs
docker logs -f clo_backend_prod

# Access PostgreSQL
docker exec -it clo_postgresql_prod psql -U clo_user -d clo_management
```

---

## ⚙️ **PRODUCTION CONFIGURATION**

### **Backend Configuration**

#### **1. FastAPI Production Settings**
```python
# backend/app/core/config.py (Production overrides)
import os
from typing import List

class ProductionSettings:
    # Security
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 40
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL") 
    REDIS_MAX_CONNECTIONS = 50
    
    # API
    DEBUG = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    API_V1_STR = "/api/v1"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "/app/logs/clo-system.log"
    
    # Performance
    WORKERS = os.cpu_count() * 2 + 1
    MAX_REQUESTS = 1000
    MAX_REQUESTS_JITTER = 100
    
    # Monitoring
    ENABLE_METRICS = True
    METRICS_PORT = 9090
```

#### **2. Gunicorn Configuration**
```python
# backend/gunicorn.conf.py
import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
user = "clo-app"
group = "clo-app"

# Logging
errorlog = "/var/log/clo-system/gunicorn-error.log"
accesslog = "/var/log/clo-system/gunicorn-access.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "clo-management-system"

# Preload app for better performance
preload_app = True

# Worker management
worker_tmp_dir = "/dev/shm"
```

### **Nginx Configuration**

```nginx
# infrastructure/docker/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/x-web-app-manifest+json
        text/cache-manifest
        text/css
        text/plain
        text/xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none';";

    upstream clo_backend {
        server clo_backend:8000;
        keepalive 32;
    }

    # HTTPS redirect
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # Main application server
    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://clo_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/v1/auth/ {
            limit_req zone=auth burst=5 nodelay;
            
            proxy_pass http://clo_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend application
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Health check
        location /health {
            proxy_pass http://clo_backend/health;
            access_log off;
        }
    }
}
```

---

## 🔐 **SECURITY SETUP**

### **SSL/TLS Certificate Configuration**

#### **1. Let's Encrypt (Recommended)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### **2. Manual Certificate Setup**
```bash
# Create SSL directory
mkdir -p infrastructure/docker/nginx/ssl

# Copy certificates
cp /path/to/fullchain.pem infrastructure/docker/nginx/ssl/
cp /path/to/privkey.pem infrastructure/docker/nginx/ssl/

# Set proper permissions
chmod 600 infrastructure/docker/nginx/ssl/privkey.pem
chmod 644 infrastructure/docker/nginx/ssl/fullchain.pem
```

### **Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (local only)
sudo ufw allow from 127.0.0.1 to any port 5432

# Allow Redis (local only)
sudo ufw allow from 127.0.0.1 to any port 6379

# Check status
sudo ufw status
```

### **Database Security**

```bash
# PostgreSQL security hardening
sudo nano /etc/postgresql/15/main/postgresql.conf

# Security settings:
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h'

# Create read-only monitoring user
sudo -u postgres psql
CREATE USER clo_monitor WITH PASSWORD 'monitor_password';
GRANT CONNECT ON DATABASE clo_management TO clo_monitor;
GRANT USAGE ON SCHEMA public TO clo_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO clo_monitor;
```

### **Application Security**

#### **1. Environment Variables Security**
```bash
# Secure environment file permissions
chmod 600 .env.production

# Use Docker secrets for sensitive data
echo "your_secure_password" | docker secret create db_password -
echo "your_jwt_secret" | docker secret create jwt_secret -
```

#### **2. API Security Configuration**
```python
# backend/app/core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

class SecurityConfig:
    # Password hashing
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # JWT configuration
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 100
    AUTH_RATE_LIMIT_PER_MINUTE = 10
    
    # CORS configuration
    ALLOWED_ORIGINS = ["https://your-domain.com"]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]
    ALLOWED_HEADERS = ["Authorization", "Content-Type"]
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
```

---

## 📊 **MONITORING & LOGGING**

### **Application Logging**

#### **1. Structured Logging Configuration**
```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/clo-system/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "json"
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file", "console"]
    }
})
```

### **Prometheus Metrics**

#### **1. Metrics Configuration**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# API metrics
API_REQUESTS_TOTAL = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

API_REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Database metrics
DB_CONNECTIONS_ACTIVE = Gauge(
    'database_connections_active',
    'Active database connections'
)

DB_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Business metrics
WATERFALL_CALCULATIONS_TOTAL = Counter(
    'waterfall_calculations_total',
    'Total waterfall calculations performed'
)

RISK_ANALYSES_TOTAL = Counter(
    'risk_analyses_total',
    'Total risk analyses performed'
)

# System metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)
```

#### **2. Grafana Dashboard Configuration**
```json
# monitoring/grafana/dashboards/clo-system-dashboard.json
{
  "dashboard": {
    "title": "CLO Management System",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, api_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "database_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "Business Metrics",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(waterfall_calculations_total[24h])",
            "legendFormat": "Daily Calculations"
          }
        ]
      }
    ]
  }
}
```

### **Log Management**

#### **1. Log Rotation**
```bash
# /etc/logrotate.d/clo-system
/var/log/clo-system/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 clo-app clo-app
    postrotate
        systemctl reload clo-system
    endscript
}
```

#### **2. Centralized Logging (ELK Stack)**
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## 💾 **BACKUP & RECOVERY**

### **Database Backup Strategy**

#### **1. PostgreSQL Automated Backup**
```bash
#!/bin/bash
# /opt/clo-system/scripts/backup-database.sh

# Configuration
DB_NAME="clo_management"
DB_USER="clo_user"
BACKUP_DIR="/opt/clo-backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full database backup
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --no-owner --no-privileges \
    --format=custom > "$BACKUP_DIR/clo_db_$DATE.dump"

# Compress backup
gzip "$BACKUP_DIR/clo_db_$DATE.dump"

# Remove old backups
find "$BACKUP_DIR" -name "clo_db_*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "$(date): Database backup completed: clo_db_$DATE.dump.gz" >> /var/log/clo-system/backup.log
```

#### **2. Migration Databases Backup**
```bash
#!/bin/bash
# /opt/clo-system/scripts/backup-migration-dbs.sh

MIGRATION_DB_DIR="/opt/clo-management-system"
BACKUP_DIR="/opt/clo-backups/migration"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup each SQLite database
for db in clo_assets.db clo_correlations.db clo_mag_scenarios.db clo_model_config.db clo_reference_quick.db; do
    if [ -f "$MIGRATION_DB_DIR/$db" ]; then
        cp "$MIGRATION_DB_DIR/$db" "$BACKUP_DIR/${db%.db}_$DATE.db"
        gzip "$BACKUP_DIR/${db%.db}_$DATE.db"
        echo "$(date): Backed up $db" >> /var/log/clo-system/migration-backup.log
    fi
done

# Remove old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.db.gz" -mtime +30 -delete
```

#### **3. Automated Backup Scheduling**
```bash
# Add to crontab (sudo crontab -e)
# Daily database backup at 2 AM
0 2 * * * /opt/clo-system/scripts/backup-database.sh

# Weekly migration database backup (Sundays at 3 AM)
0 3 * * 0 /opt/clo-system/scripts/backup-migration-dbs.sh

# Monthly full system backup
0 4 1 * * /opt/clo-system/scripts/backup-full-system.sh
```

### **Disaster Recovery Procedures**

#### **1. Database Recovery**
```bash
# PostgreSQL recovery from backup
pg_restore -h localhost -U clo_user -d clo_management \
    --verbose --clean --no-owner --no-privileges \
    /opt/clo-backups/clo_db_20240810_020000.dump

# Migration databases recovery
cd /opt/clo-management-system
gunzip -c /opt/clo-backups/migration/clo_assets_20240810_030000.db.gz > clo_assets.db
# Repeat for all migration databases
```

#### **2. Full System Recovery**
```bash
# 1. Restore application code
git clone https://github.com/your-org/clo-management-system.git /opt/clo-management-system

# 2. Restore configuration
cp /opt/clo-backups/config/.env.production /opt/clo-management-system/

# 3. Restore databases (see above)

# 4. Restore Docker volumes
docker run --rm -v clo_postgresql_data_prod:/volume -v /opt/clo-backups:/backup alpine \
    sh -c "cd /volume && tar -xzf /backup/postgresql-data-20240810.tar.gz --strip-components=1"

# 5. Restart services
cd /opt/clo-management-system/infrastructure/docker
docker-compose -f docker-compose.production.yml up -d
```

---

## 🔧 **MAINTENANCE PROCEDURES**

### **Regular Maintenance Tasks**

#### **1. Daily Tasks (Automated)**
```bash
#!/bin/bash
# /opt/clo-system/scripts/daily-maintenance.sh

# Check system health
curl -f http://localhost:8000/health || echo "$(date): Health check failed" >> /var/log/clo-system/maintenance.log

# Clean temporary files
find /tmp -name "clo-*" -mtime +1 -delete

# Rotate logs
logrotate -f /etc/logrotate.d/clo-system

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is $DISK_USAGE%" >> /var/log/clo-system/maintenance.log
fi

# Database statistics
psql -h localhost -U clo_user -d clo_management -c "\
    SELECT 'connections' as metric, count(*) as value FROM pg_stat_activity \
    UNION ALL \
    SELECT 'database_size', pg_size_pretty(pg_database_size('clo_management'))::text \
    UNION ALL \
    SELECT 'cache_hit_ratio', round(sum(blks_hit)*100/sum(blks_hit+blks_read),2)::text \
    FROM pg_stat_database WHERE datname='clo_management';" > /var/log/clo-system/db-stats.log
```

#### **2. Weekly Tasks**
```bash
#!/bin/bash
# /opt/clo-system/scripts/weekly-maintenance.sh

# Update system packages (with approval)
sudo apt update
sudo apt list --upgradable

# PostgreSQL maintenance
psql -h localhost -U clo_user -d clo_management -c "VACUUM ANALYZE;"
psql -h localhost -U clo_user -d clo_management -c "REINDEX DATABASE clo_management;"

# Check for security updates
sudo unattended-upgrades --dry-run

# SSL certificate check
openssl x509 -in /etc/nginx/ssl/fullchain.pem -text -noout | grep "Not After"

# Performance analysis
docker stats --no-stream > /var/log/clo-system/docker-stats-$(date +%Y%m%d).log
```

#### **3. Monthly Tasks**
```bash
#!/bin/bash
# /opt/clo-system/scripts/monthly-maintenance.sh

# Full system backup
/opt/clo-system/scripts/backup-full-system.sh

# Security audit
sudo lynis audit system --quick > /var/log/clo-system/security-audit-$(date +%Y%m%d).log

# Performance tuning review
pg_stat_statements_reset();

# Update dependencies (development environment)
cd /opt/clo-management-system/backend
pip list --outdated > /var/log/clo-system/outdated-packages-$(date +%Y%m%d).log
```

### **System Updates**

#### **1. Application Updates**
```bash
#!/bin/bash
# /opt/clo-system/scripts/update-application.sh

# Create backup before update
/opt/clo-system/scripts/backup-full-system.sh

# Pull latest code
cd /opt/clo-management-system
git fetch origin
git checkout main
git pull origin main

# Update Python dependencies
source venv/bin/activate
pip install -r backend/requirements.txt

# Run database migrations
cd backend
alembic upgrade head

# Rebuild Docker images
cd ../infrastructure/docker
docker-compose -f docker-compose.production.yml build --no-cache

# Rolling update (zero downtime)
docker-compose -f docker-compose.production.yml up -d --no-deps clo_backend

# Verify update
curl -f http://localhost:8000/health
```

#### **2. Security Updates**
```bash
#!/bin/bash
# /opt/clo-system/scripts/security-updates.sh

# System security updates
sudo apt update
sudo apt upgrade -y

# Docker security updates
docker system prune -f
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# SSL certificate renewal
sudo certbot renew --nginx

# Update security scanning
sudo freshclam
sudo clamscan -r /opt/clo-management-system --log=/var/log/clo-system/security-scan.log
```

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues & Solutions**

#### **1. Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check configuration
sudo -u postgres psql -c "SHOW config_file;"

# Reset connection pool
docker-compose restart clo_backend

# Check logs
docker logs clo_backend_prod | grep -i error
tail -f /var/log/postgresql/postgresql-15-main.log
```

#### **2. Performance Issues**
```bash
# Check system resources
htop
iotop
docker stats

# Database performance
sudo -u postgres psql -d clo_management -c "\
    SELECT query, calls, total_time, mean_time \
    FROM pg_stat_statements \
    ORDER BY total_time DESC LIMIT 10;"

# Check slow queries
tail -f /var/log/postgresql/postgresql-15-main.log | grep "slow query"

# Redis performance
redis-cli info stats
redis-cli info memory
```

#### **3. API Issues**
```bash
# Check API health
curl -v http://localhost:8000/health

# Check authentication
curl -X POST http://localhost:8000/api/v1/auth/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=password"

# Check logs
docker logs -f clo_backend_prod | grep -i error
tail -f /var/log/clo-system/app.log | jq '.message'

# Test specific endpoint
curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/assets/ | jq '.total_count'
```

#### **4. Memory Issues**
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Check Docker memory usage
docker stats --no-stream

# Check for memory leaks
ps aux --sort=-%mem | head -10

# Restart services if needed
docker-compose -f docker-compose.production.yml restart clo_backend
```

### **Emergency Procedures**

#### **1. System Down - Recovery Steps**
```bash
# 1. Check all services
systemctl status postgresql redis-server nginx
docker-compose ps

# 2. Check disk space
df -h

# 3. Check system resources
htop

# 4. Restart services in order
sudo systemctl restart postgresql
sudo systemctl restart redis-server
docker-compose -f docker-compose.production.yml restart

# 5. Verify recovery
curl http://localhost:8000/health
```

#### **2. Data Corruption - Recovery**
```bash
# 1. Stop all services
docker-compose -f docker-compose.production.yml stop

# 2. Check database integrity
sudo -u postgres postgres --single -D /var/lib/postgresql/15/main clo_management

# 3. Restore from backup if needed
pg_restore -d clo_management /opt/clo-backups/latest-backup.dump

# 4. Restart services
docker-compose -f docker-compose.production.yml up -d
```

### **Monitoring & Alerting**

#### **1. Health Check Script**
```bash
#!/bin/bash
# /opt/clo-system/scripts/health-check.sh

# Check API health
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "API health check failed" | mail -s "CLO System Alert" admin@yourcompany.com
fi

# Check database
if ! pg_isready -h localhost -p 5432 -U clo_user >/dev/null 2>&1; then
    echo "Database health check failed" | mail -s "CLO System Alert" admin@yourcompany.com
fi

# Check Redis
if ! redis-cli ping >/dev/null 2>&1; then
    echo "Redis health check failed" | mail -s "CLO System Alert" admin@yourcompany.com
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Disk usage is $DISK_USAGE%" | mail -s "CLO System Alert" admin@yourcompany.com
fi
```

#### **2. Automated Alerting**
```bash
# Add to crontab for monitoring (every 5 minutes)
*/5 * * * * /opt/clo-system/scripts/health-check.sh

# Weekly system report
0 9 * * 1 /opt/clo-system/scripts/weekly-report.sh | mail -s "CLO System Weekly Report" admin@yourcompany.com
```

---

## 📞 **SUPPORT & CONTACTS**

### **Emergency Contacts**
- **System Administrator**: admin@yourcompany.com
- **Database Administrator**: dba@yourcompany.com  
- **Security Team**: security@yourcompany.com
- **On-Call Support**: +1-555-0199 (24/7)

### **Escalation Procedures**
1. **Level 1**: Application issues → Development Team
2. **Level 2**: Infrastructure issues → DevOps Team
3. **Level 3**: Security incidents → Security Team
4. **Level 4**: Business critical → Management Team

### **Documentation & Resources**
- **System Documentation**: `/opt/clo-management-system/docs/`
- **Runbook**: `/opt/clo-management-system/docs/RUNBOOK.md`
- **API Documentation**: `https://your-domain.com/docs`
- **Monitoring Dashboard**: `https://monitoring.your-domain.com`

---

**Last Updated**: August 10, 2024  
**Version**: 1.0.0  
**Next Review**: September 10, 2024