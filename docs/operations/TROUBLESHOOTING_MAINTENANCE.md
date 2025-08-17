# CLO Management System - Troubleshooting & Maintenance Guide

## Table of Contents

1. [System Monitoring](#system-monitoring)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Database Maintenance](#database-maintenance)
4. [Performance Optimization](#performance-optimization)
5. [Backup & Recovery](#backup--recovery)
6. [Security Maintenance](#security-maintenance)
7. [Scheduled Maintenance Tasks](#scheduled-maintenance-tasks)
8. [Emergency Procedures](#emergency-procedures)

---

## System Monitoring

### Health Check Endpoints

#### Application Health
```bash
# Basic health check
curl -X GET "https://api.clo-system.com/api/v1/monitoring/health"

# Expected Response:
{
  "overall_status": "healthy",
  "uptime_seconds": 3456789,
  "uptime_human": "40d 2h 33m",
  "services": [
    {"service_name": "PostgreSQL", "status": "healthy"},
    {"service_name": "Redis", "status": "healthy"},
    {"service_name": "Migration DB (assets)", "status": "healthy"}
  ],
  "cpu_usage_percent": 25.3,
  "memory_usage_percent": 67.8,
  "disk_usage_percent": 45.2
}
```

#### Database Health
```bash
# Database connectivity check
curl -X GET "https://api.clo-system.com/api/v1/monitoring/database-stats"

# PostgreSQL direct check
psql -h localhost -U clo_user -d clo_management -c "SELECT 1 as health_check;"
```

#### Cache Health
```bash
# Redis connectivity check
redis-cli ping
# Expected: PONG

# Cache statistics
curl -X GET "https://api.clo-system.com/api/v1/monitoring/cache-stats"
```

### Monitoring Dashboards

#### System Metrics Dashboard
```python
# Custom monitoring script
#!/usr/bin/env python3
import psutil
import requests
import time
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.api_base = "https://api.clo-system.com/api/v1"
        self.alert_threshold = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time_ms': 2000
        }
    
    def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application health
        try:
            response = requests.get(f"{self.api_base}/monitoring/health", timeout=10)
            api_healthy = response.status_code == 200
            response_time = response.elapsed.total_seconds() * 1000
        except Exception as e:
            api_healthy = False
            response_time = float('inf')
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': (disk.used / disk.total) * 100,
            'api_healthy': api_healthy,
            'response_time_ms': response_time
        }
        
        # Check thresholds and alert
        self.check_alerts(metrics)
        
        return metrics
    
    def check_alerts(self, metrics):
        """Check metrics against alert thresholds"""
        alerts = []
        
        for metric, threshold in self.alert_threshold.items():
            if metric in metrics and metrics[metric] > threshold:
                alerts.append(f"ALERT: {metric} = {metrics[metric]:.2f} (threshold: {threshold})")
        
        if alerts:
            self.send_alerts(alerts, metrics)
    
    def send_alerts(self, alerts, metrics):
        """Send alerts to administrators"""
        print(f"[{datetime.now()}] SYSTEM ALERTS:")
        for alert in alerts:
            print(f"  - {alert}")
        
        # In production: send email, Slack notification, etc.

if __name__ == "__main__":
    monitor = SystemMonitor()
    
    while True:
        try:
            metrics = monitor.collect_system_metrics()
            print(f"[{metrics['timestamp']}] System OK - "
                  f"CPU: {metrics['cpu_percent']:.1f}% "
                  f"Memory: {metrics['memory_percent']:.1f}% "
                  f"Disk: {metrics['disk_percent']:.1f}% "
                  f"API: {metrics['response_time_ms']:.0f}ms")
        except Exception as e:
            print(f"[{datetime.now()}] Monitoring error: {e}")
        
        time.sleep(60)  # Check every minute
```

---

## Common Issues & Solutions

### Application Issues

#### Issue: API Returns 500 Internal Server Error
**Symptoms:**
- API endpoints returning HTTP 500
- Error logs showing database connection failures
- Users unable to access application

**Diagnosis:**
```bash
# Check application logs
docker logs clo-app-container

# Check database connectivity
psql -h db-host -U clo_user -d clo_management -c "SELECT version();"

# Check application health endpoint
curl -X GET "http://localhost:8000/api/v1/monitoring/health"
```

**Solutions:**
```bash
# 1. Restart application container
docker restart clo-app-container

# 2. Check database connection pool
# Look for connection pool exhaustion in logs
grep "connection pool" /var/log/clo-app.log

# 3. Verify database configuration
docker exec -it clo-app-container env | grep DATABASE_URL

# 4. Clear connection pool if needed
docker exec -it clo-app-container python -c "
from backend.app.core.database_config import db_config
db_config.engine.dispose()
print('Connection pool cleared')
"
```

#### Issue: Authentication Failures
**Symptoms:**
- Users cannot log in
- "Invalid credentials" errors for valid users
- JWT token validation failures

**Diagnosis:**
```bash
# Check authentication service logs
grep "auth" /var/log/clo-app.log | tail -20

# Test direct authentication
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Check JWT configuration
docker exec -it clo-app-container env | grep JWT
```

**Solutions:**
```bash
# 1. Verify JWT secret key configuration
echo $JWT_SECRET_KEY | wc -c  # Should be > 32 characters

# 2. Check user database
psql -h db-host -U clo_user -d clo_management -c "
SELECT email, is_active, last_login FROM users WHERE email = 'user@example.com';
"

# 3. Clear Redis cache (may contain stale session data)
redis-cli FLUSHDB

# 4. Reset user password
docker exec -it clo-app-container python -c "
from backend.app.services.auth_service import AuthService
auth = AuthService()
new_hash = auth.get_password_hash('newpassword123')
print(f'New password hash: {new_hash}')
"
```

### Database Issues

#### Issue: Database Connection Pool Exhausted
**Symptoms:**
- "Connection pool limit reached" errors
- Slow API responses
- Timeouts on database queries

**Diagnosis:**
```sql
-- Check active connections
SELECT count(*) as active_connections, state 
FROM pg_stat_activity 
WHERE datname = 'clo_management' 
GROUP BY state;

-- Check long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state = 'active';
```

**Solutions:**
```bash
# 1. Increase connection pool size
# Edit docker-compose.yml or environment variables
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=20

# 2. Kill long-running queries
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
         WHERE (now() - pg_stat_activity.query_start) > interval '30 minutes';"

# 3. Restart application to reset pool
docker restart clo-app-container

# 4. Optimize queries causing connection buildup
# Check slow query log
tail -f /var/log/postgresql/postgresql-slow.log
```

#### Issue: SQLite Database Locked
**Symptoms:**
- "Database is locked" errors
- Failed data migration operations
- Timeouts accessing migrated data

**Diagnosis:**
```bash
# Check for processes accessing SQLite files
lsof | grep -E "\.(db|sqlite)$"

# Test database access
sqlite3 assets.db "SELECT COUNT(*) FROM assets;" 2>&1
```

**Solutions:**
```bash
# 1. Close all connections to SQLite files
# Find and kill processes holding database locks
fuser -k assets.db correlations.db scenarios.db config.db reference.db

# 2. Check database integrity
sqlite3 assets.db "PRAGMA integrity_check;"

# 3. Vacuum databases to optimize
sqlite3 assets.db "VACUUM;"
sqlite3 correlations.db "VACUUM;"

# 4. Convert to WAL mode for better concurrency
sqlite3 assets.db "PRAGMA journal_mode=WAL;"
```

### Cache Issues

#### Issue: Redis Memory Issues
**Symptoms:**
- Redis running out of memory
- Cache misses increasing
- OOM (Out of Memory) errors

**Diagnosis:**
```bash
# Check Redis memory usage
redis-cli INFO memory

# Check memory usage by key patterns
redis-cli --bigkeys

# Monitor memory in real-time
redis-cli monitor | grep -E "(SET|DEL)"
```

**Solutions:**
```bash
# 1. Clear cache entirely (temporary fix)
redis-cli FLUSHALL

# 2. Clear specific key patterns
redis-cli --scan --pattern "portfolio:*" | xargs redis-cli DEL

# 3. Configure memory limits and eviction
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 4. Restart Redis with new configuration
docker restart clo-redis-container
```

### Performance Issues

#### Issue: Slow API Response Times
**Symptoms:**
- API responses taking > 2 seconds
- Frontend timeouts
- High CPU usage on database server

**Diagnosis:**
```bash
# Check API response times
curl -w "@curl-format.txt" -s -o /dev/null "https://api.clo-system.com/api/v1/portfolios"

# curl-format.txt content:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer: %{time_pretransfer}\n
# time_redirect:    %{time_redirect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n

# Check database query performance
psql -c "SELECT query, calls, total_time, mean_time 
         FROM pg_stat_statements 
         ORDER BY mean_time DESC LIMIT 10;"
```

**Solutions:**
```python
# 1. Add database indexes for slow queries
CREATE INDEX CONCURRENTLY idx_assets_rating_industry ON assets(rating, industry);
CREATE INDEX CONCURRENTLY idx_portfolios_created_at ON portfolios(created_at);

# 2. Implement query result caching
@app.get("/api/v1/portfolios")
async def list_portfolios():
    cache_key = "portfolios:list:all"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    portfolios = await portfolio_service.list_all()
    await redis_client.setex(cache_key, 300, json.dumps(portfolios))
    return portfolios

# 3. Optimize database queries
# Use EXPLAIN ANALYZE to identify bottlenecks
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM assets WHERE rating LIKE 'Aa%';
```

---

## Database Maintenance

### PostgreSQL Maintenance

#### Daily Maintenance
```bash
#!/bin/bash
# daily_db_maintenance.sh

echo "[$(date)] Starting daily database maintenance..."

# Update table statistics
psql -d clo_management -c "ANALYZE;"

# Check for bloated tables
psql -d clo_management -c "
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
       round((n_dead_tup::float / GREATEST(n_live_tup,1)) * 100, 2) as dead_ratio
FROM pg_stat_user_tables 
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;
"

# Vacuum tables with high dead tuple ratio
psql -d clo_management -c "VACUUM (ANALYZE, VERBOSE) audit_logs;"

# Check database size growth
psql -d clo_management -c "
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database WHERE datname = 'clo_management';
"

echo "[$(date)] Daily database maintenance completed."
```

#### Weekly Maintenance
```bash
#!/bin/bash
# weekly_db_maintenance.sh

echo "[$(date)] Starting weekly database maintenance..."

# Full vacuum of high-churn tables
psql -d clo_management -c "VACUUM FULL audit_logs;"

# Reindex system catalogs
psql -d clo_management -c "REINDEX SYSTEM clo_management;"

# Update query statistics
psql -d clo_management -c "SELECT pg_stat_reset();"

# Check for unused indexes
psql -d clo_management -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename, indexname;
"

# Archive old audit logs (older than 1 year)
psql -d clo_management -c "
DELETE FROM audit_logs 
WHERE timestamp < NOW() - INTERVAL '1 year';
"

echo "[$(date)] Weekly database maintenance completed."
```

### SQLite Maintenance

#### SQLite Optimization Script
```python
#!/usr/bin/env python3
# optimize_sqlite_databases.py

import sqlite3
import os
from datetime import datetime

def optimize_sqlite_db(db_path):
    """Optimize SQLite database"""
    print(f"[{datetime.now()}] Optimizing {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check database integrity
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result != "ok":
            print(f"WARNING: Integrity check failed for {db_path}: {integrity_result}")
            return False
        
        # Get database size before optimization
        size_before = os.path.getsize(db_path)
        
        # Vacuum database
        cursor.execute("VACUUM;")
        
        # Analyze database for query optimization
        cursor.execute("ANALYZE;")
        
        # Update statistics
        cursor.execute("PRAGMA optimize;")
        
        conn.close()
        
        # Get size after optimization
        size_after = os.path.getsize(db_path)
        space_saved = size_before - size_after
        
        print(f"  - Size before: {size_before:,} bytes")
        print(f"  - Size after: {size_after:,} bytes")
        print(f"  - Space saved: {space_saved:,} bytes ({space_saved/size_before*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"ERROR optimizing {db_path}: {e}")
        return False

def main():
    """Optimize all SQLite databases"""
    databases = [
        "assets.db",
        "correlations.db", 
        "scenarios.db",
        "config.db",
        "reference.db"
    ]
    
    print(f"[{datetime.now()}] Starting SQLite database optimization...")
    
    success_count = 0
    for db_path in databases:
        if os.path.exists(db_path):
            if optimize_sqlite_db(db_path):
                success_count += 1
        else:
            print(f"WARNING: Database not found: {db_path}")
    
    print(f"[{datetime.now()}] Optimization completed: {success_count}/{len(databases)} databases optimized")

if __name__ == "__main__":
    main()
```

---

## Performance Optimization

### Query Optimization

#### Identify Slow Queries
```sql
-- Enable query statistics (run once)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_time DESC 
LIMIT 10;
```

#### Database Performance Tuning
```sql
-- Recommended PostgreSQL configuration for CLO system
-- Add to postgresql.conf

# Memory settings
shared_buffers = 256MB                  # 25% of RAM
effective_cache_size = 1GB              # 75% of RAM
work_mem = 8MB                          # Per connection
maintenance_work_mem = 128MB            # For maintenance operations

# Query planner settings
random_page_cost = 1.1                  # SSD optimized
effective_io_concurrency = 200          # SSD optimized

# WAL settings for performance
wal_level = replica
max_wal_size = 2GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9

# Connection settings
max_connections = 100
```

### Application Performance

#### Connection Pool Optimization
```python
# Optimized database configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Production database configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Base number of connections
    max_overflow=30,           # Additional connections under load
    pool_pre_ping=True,        # Validate connections before use
    pool_recycle=3600,         # Recycle connections every hour
    echo=False,                # Disable query logging in production
    connect_args={
        "options": "-c default_transaction_isolation=read committed"
    }
)
```

#### Cache Strategy Optimization
```python
# Multi-level caching implementation
class OptimizedCacheService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(REDIS_URL)
        self.local_cache = {}  # In-memory cache
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    async def get_cached_data(self, key: str, factory_func, ttl: int = 3600):
        """Multi-level cache with statistics"""
        # Level 1: In-memory cache (fastest)
        if key in self.local_cache:
            self.cache_stats['hits'] += 1
            return self.local_cache[key]['data']
        
        # Level 2: Redis cache
        cached_data = self.redis_client.get(key)
        if cached_data:
            data = json.loads(cached_data)
            # Store in local cache
            self.local_cache[key] = {
                'data': data,
                'expires': time.time() + 300  # 5 minutes local cache
            }
            self.cache_stats['hits'] += 1
            return data
        
        # Level 3: Generate data
        self.cache_stats['misses'] += 1
        data = await factory_func()
        
        # Store in both caches
        self.redis_client.setex(key, ttl, json.dumps(data))
        self.local_cache[key] = {
            'data': data,
            'expires': time.time() + 300
        }
        
        return data
    
    def clear_expired_local_cache(self):
        """Clean up expired local cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.local_cache.items()
            if value['expires'] < current_time
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
```

---

## Backup & Recovery

### Automated Backup System

#### Database Backup Script
```bash
#!/bin/bash
# backup_system.sh

# Configuration
BACKUP_DIR="/backup/clo-system"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

echo "[$(date)] Starting system backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR/postgresql/$TIMESTAMP"
mkdir -p "$BACKUP_DIR/sqlite/$TIMESTAMP"
mkdir -p "$BACKUP_DIR/application/$TIMESTAMP"

# PostgreSQL backup
echo "Backing up PostgreSQL database..."
pg_dump -h localhost -U clo_user -d clo_management \
    -f "$BACKUP_DIR/postgresql/$TIMESTAMP/clo_management.sql"

if [ $? -eq 0 ]; then
    echo "PostgreSQL backup completed successfully"
    gzip "$BACKUP_DIR/postgresql/$TIMESTAMP/clo_management.sql"
else
    echo "ERROR: PostgreSQL backup failed"
    exit 1
fi

# SQLite databases backup
echo "Backing up SQLite databases..."
SQLITE_DBS=("assets.db" "correlations.db" "scenarios.db" "config.db" "reference.db")

for db in "${SQLITE_DBS[@]}"; do
    if [ -f "$db" ]; then
        cp "$db" "$BACKUP_DIR/sqlite/$TIMESTAMP/"
        echo "Backed up $db"
    else
        echo "WARNING: $db not found"
    fi
done

# Application configuration backup
echo "Backing up application configuration..."
docker exec clo-app-container tar -czf - /app/config/ > "$BACKUP_DIR/application/$TIMESTAMP/app_config.tar.gz"

# Create backup manifest
cat > "$BACKUP_DIR/backup_manifest_$TIMESTAMP.json" << EOF
{
    "backup_date": "$(date -Iseconds)",
    "backup_type": "full",
    "postgresql_backup": "$BACKUP_DIR/postgresql/$TIMESTAMP/clo_management.sql.gz",
    "sqlite_backups": [
        $(printf '"%s",' "${SQLITE_DBS[@]}" | sed 's/,$//')
    ],
    "application_backup": "$BACKUP_DIR/application/$TIMESTAMP/app_config.tar.gz",
    "backup_size": "$(du -sh $BACKUP_DIR | cut -f1)"
}
EOF

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type d -name "*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_*" -mtime +$RETENTION_DAYS -exec rm -rf {} \;
find "$BACKUP_DIR" -name "backup_manifest_*.json" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] System backup completed successfully"
```

#### Recovery Procedures

##### PostgreSQL Recovery
```bash
# Full database recovery
#!/bin/bash
# recover_postgresql.sh

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "WARNING: This will replace the current database!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

# Stop application
docker stop clo-app-container

# Drop and recreate database
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS clo_management;"
psql -h localhost -U postgres -c "CREATE DATABASE clo_management OWNER clo_user;"

# Restore from backup
gunzip -c "$BACKUP_FILE" | psql -h localhost -U clo_user -d clo_management

if [ $? -eq 0 ]; then
    echo "Database recovery completed successfully"
    
    # Restart application
    docker start clo-app-container
    
    # Verify recovery
    sleep 10
    curl -f "http://localhost:8000/api/v1/monitoring/health" && echo "Application is healthy"
else
    echo "ERROR: Database recovery failed"
    exit 1
fi
```

##### SQLite Recovery
```bash
# SQLite database recovery
#!/bin/bash
# recover_sqlite.sh

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Recovering SQLite databases from $BACKUP_DIR..."

# Stop application to prevent database locks
docker stop clo-app-container

# Backup current databases
mkdir -p backup_current
cp *.db backup_current/ 2>/dev/null

# Restore from backup
SQLITE_DBS=("assets.db" "correlations.db" "scenarios.db" "config.db" "reference.db")

for db in "${SQLITE_DBS[@]}"; do
    if [ -f "$BACKUP_DIR/$db" ]; then
        cp "$BACKUP_DIR/$db" .
        echo "Restored $db"
        
        # Verify integrity
        sqlite3 "$db" "PRAGMA integrity_check;" | grep -q "ok"
        if [ $? -eq 0 ]; then
            echo "$db integrity check passed"
        else
            echo "WARNING: $db integrity check failed"
        fi
    else
        echo "WARNING: $db not found in backup"
    fi
done

# Restart application
docker start clo-app-container

echo "SQLite recovery completed"
```

### Disaster Recovery Plan

#### RTO/RPO Objectives
- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 1 hour (based on backup frequency)

#### Recovery Procedures
```bash
# Disaster recovery runbook
#!/bin/bash
# disaster_recovery.sh

echo "=== CLO SYSTEM DISASTER RECOVERY ==="
echo "RTO: 4 hours | RPO: 1 hour"
echo

# Step 1: Assess situation
echo "1. SITUATION ASSESSMENT"
read -p "Describe the incident: " incident_description
read -p "Systems affected (app/db/all): " affected_systems

# Step 2: Notify stakeholders
echo "2. STAKEHOLDER NOTIFICATION"
echo "Sending incident notification..."
# In production: send email/Slack alerts

# Step 3: Infrastructure recovery
echo "3. INFRASTRUCTURE RECOVERY"
if [[ "$affected_systems" == *"all"* ]] || [[ "$affected_systems" == *"db"* ]]; then
    echo "Recovering database infrastructure..."
    # Restore from latest backup
    LATEST_BACKUP=$(ls -t /backup/clo-system/backup_manifest_*.json | head -1)
    echo "Using backup: $LATEST_BACKUP"
    
    # Execute database recovery
    ./recover_postgresql.sh /backup/clo-system/postgresql/$(basename $LATEST_BACKUP .json | cut -d'_' -f3-4)/clo_management.sql.gz
    ./recover_sqlite.sh /backup/clo-system/sqlite/$(basename $LATEST_BACKUP .json | cut -d'_' -f3-4)/
fi

# Step 4: Application recovery
echo "4. APPLICATION RECOVERY"
if [[ "$affected_systems" == *"all"* ]] || [[ "$affected_systems" == *"app"* ]]; then
    echo "Recovering application services..."
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    sleep 30
    
    # Health check
    curl -f "http://localhost:8000/api/v1/monitoring/health"
    if [ $? -eq 0 ]; then
        echo "Application recovery successful"
    else
        echo "Application recovery failed - manual intervention required"
    fi
fi

# Step 5: Verification
echo "5. SYSTEM VERIFICATION"
echo "Running system verification tests..."

# Test database connectivity
psql -h localhost -U clo_user -d clo_management -c "SELECT COUNT(*) FROM users;" > /dev/null
echo "Database connectivity: $([ $? -eq 0 ] && echo 'OK' || echo 'FAILED')"

# Test API endpoints
curl -s "http://localhost:8000/api/v1/monitoring/health" > /dev/null
echo "API availability: $([ $? -eq 0 ] && echo 'OK' || echo 'FAILED')"

# Test data integrity
# Add specific data validation tests here

echo "6. POST-RECOVERY ACTIONS"
echo "- Update incident log"
echo "- Notify stakeholders of recovery"
echo "- Schedule post-incident review"
echo "- Update recovery procedures if needed"

echo "=== DISASTER RECOVERY COMPLETED ==="
```

---

## Security Maintenance

### Security Updates

#### System Security Updates
```bash
#!/bin/bash
# security_updates.sh

echo "[$(date)] Starting security maintenance..."

# Update system packages
echo "Updating system packages..."
apt update && apt upgrade -y

# Update Docker images
echo "Updating Docker images..."
docker pull postgres:13
docker pull redis:6-alpine
docker pull grafana/grafana

# Rebuild application image with latest base image
echo "Rebuilding application image..."
docker build -t clo-app:latest .

# Update Python dependencies
echo "Checking for Python security updates..."
pip-audit --format=json --output=security_audit.json

# Check for known vulnerabilities
echo "Scanning for vulnerabilities..."
docker run --rm -v "$(pwd):/src" securecodewarrior/docker-security-scanner /src

echo "[$(date)] Security maintenance completed"
```

#### SSL Certificate Renewal
```bash
#!/bin/bash
# renew_ssl_certificates.sh

echo "Checking SSL certificate expiration..."

# Check certificate expiry
CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/ssl/certs/clo-system.crt | cut -d'=' -f2)
EXPIRY_DATE=$(date -d "$CERT_EXPIRY" +%s)
CURRENT_DATE=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_DATE - $CURRENT_DATE) / 86400 ))

echo "Certificate expires in $DAYS_UNTIL_EXPIRY days"

# Renew if expiring within 30 days
if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "Certificate renewal required"
    
    # Renew certificate (example with Let's Encrypt)
    certbot renew --nginx
    
    # Restart nginx to load new certificate
    systemctl reload nginx
    
    echo "Certificate renewed successfully"
else
    echo "Certificate renewal not required"
fi
```

---

## Scheduled Maintenance Tasks

### Maintenance Schedule

#### Daily Tasks (Automated)
```bash
# /etc/cron.d/clo-system-daily
0 2 * * * root /opt/clo-system/scripts/daily_maintenance.sh >> /var/log/clo-maintenance.log 2>&1
```

#### Weekly Tasks (Automated)
```bash
# /etc/cron.d/clo-system-weekly  
0 3 * * 0 root /opt/clo-system/scripts/weekly_maintenance.sh >> /var/log/clo-maintenance.log 2>&1
```

#### Monthly Tasks (Manual)
```bash
# Monthly maintenance checklist
#!/bin/bash
# monthly_maintenance_checklist.sh

echo "=== MONTHLY MAINTENANCE CHECKLIST ==="

echo "□ 1. Review system performance metrics"
echo "□ 2. Analyze security logs and alerts"
echo "□ 3. Update documentation"
echo "□ 4. Test backup and recovery procedures"
echo "□ 5. Review user access permissions"
echo "□ 6. Update security patches"
echo "□ 7. Performance baseline review"
echo "□ 8. Capacity planning review"
echo "□ 9. Incident retrospective"
echo "□ 10. Update emergency contacts"

echo
echo "Tasks to complete manually:"
echo "- Review and archive old audit logs"
echo "- Validate data integrity across all systems"
echo "- Update system documentation"
echo "- Review and test disaster recovery procedures"
```

### Maintenance Scripts

#### System Health Report
```python
#!/usr/bin/env python3
# generate_health_report.py

import json
import requests
from datetime import datetime, timedelta

class HealthReportGenerator:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
        self.report_data = {}
    
    def generate_weekly_report(self):
        """Generate comprehensive weekly health report"""
        print("Generating weekly system health report...")
        
        # Collect system metrics
        self.report_data['system_health'] = self.get_system_health()
        self.report_data['performance_metrics'] = self.get_performance_metrics()
        self.report_data['database_stats'] = self.get_database_stats()
        self.report_data['security_summary'] = self.get_security_summary()
        self.report_data['error_analysis'] = self.analyze_errors()
        
        # Generate report
        self.create_report()
        
    def get_system_health(self):
        """Get current system health status"""
        try:
            response = requests.get(f"{self.api_base}/monitoring/health")
            return response.json() if response.status_code == 200 else None
        except:
            return {"status": "unavailable"}
    
    def get_performance_metrics(self):
        """Get performance metrics for the past week"""
        try:
            response = requests.get(f"{self.api_base}/monitoring/performance?time_range=7d")
            return response.json() if response.status_code == 200 else None
        except:
            return {"status": "unavailable"}
    
    def create_report(self):
        """Create formatted health report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""
CLO MANAGEMENT SYSTEM - WEEKLY HEALTH REPORT
Generated: {datetime.now().isoformat()}
Report Period: {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}

=== SYSTEM HEALTH ===
Overall Status: {self.report_data['system_health'].get('overall_status', 'Unknown')}
Uptime: {self.report_data['system_health'].get('uptime_human', 'Unknown')}
CPU Usage: {self.report_data['system_health'].get('cpu_usage_percent', 0):.1f}%
Memory Usage: {self.report_data['system_health'].get('memory_usage_percent', 0):.1f}%
Disk Usage: {self.report_data['system_health'].get('disk_usage_percent', 0):.1f}%

=== PERFORMANCE METRICS ===
Average Response Time: {self.report_data['performance_metrics'].get('avg_response_time', 0):.2f}ms
Request Count: {self.report_data['performance_metrics'].get('total_requests', 0):,}
Error Rate: {self.calculate_error_rate():.2f}%

=== RECOMMENDATIONS ===
{self.generate_recommendations()}

=== NEXT ACTIONS ===
- Monitor disk usage if > 80%
- Investigate if error rate > 1%
- Schedule maintenance if uptime > 90 days
"""
        
        # Save report to file
        with open(f"health_report_{timestamp}.txt", "w") as f:
            f.write(report)
        
        print(f"Health report saved: health_report_{timestamp}.txt")
    
    def calculate_error_rate(self):
        """Calculate system error rate"""
        # Implementation would analyze actual error metrics
        return 0.5  # Mock value
    
    def generate_recommendations(self):
        """Generate maintenance recommendations"""
        recommendations = []
        
        health = self.report_data['system_health']
        
        if health.get('disk_usage_percent', 0) > 80:
            recommendations.append("- Disk usage high: Consider cleanup or expansion")
        
        if health.get('memory_usage_percent', 0) > 85:
            recommendations.append("- Memory usage high: Monitor for memory leaks")
        
        if not recommendations:
            recommendations.append("- System operating within normal parameters")
        
        return "\n".join(recommendations)

if __name__ == "__main__":
    generator = HealthReportGenerator()
    generator.generate_weekly_report()
```

---

## Emergency Procedures

### Emergency Contacts

#### Escalation Matrix
```
Level 1: System Administrator
- Name: [Admin Name]
- Phone: [Phone Number]
- Email: [Email Address]
- Availability: 24/7

Level 2: Technical Lead
- Name: [Tech Lead Name] 
- Phone: [Phone Number]
- Email: [Email Address]
- Availability: Business hours + on-call rotation

Level 3: Management
- Name: [Manager Name]
- Phone: [Phone Number]
- Email: [Email Address]
- Availability: Business hours + critical incidents
```

### Critical Issue Response

#### System Down Procedure
```bash
#!/bin/bash
# emergency_response.sh

echo "=== EMERGENCY RESPONSE ACTIVATED ==="
echo "Time: $(date)"

# Step 1: Immediate assessment
echo "1. IMMEDIATE ASSESSMENT"
echo "Checking system status..."

# Quick health check
curl -f --max-time 10 "http://localhost:8000/api/v1/monitoring/health" > /dev/null 2>&1
APP_STATUS=$?

psql -h localhost -U clo_user -d clo_management -c "SELECT 1;" > /dev/null 2>&1
DB_STATUS=$?

redis-cli ping > /dev/null 2>&1
REDIS_STATUS=$?

echo "Application: $([ $APP_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')"
echo "Database: $([ $DB_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')"
echo "Redis: $([ $REDIS_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')"

# Step 2: Immediate containment
echo "2. IMMEDIATE ACTIONS"

if [ $APP_STATUS -ne 0 ]; then
    echo "Application is down - attempting restart..."
    docker restart clo-app-container
    sleep 10
    
    curl -f --max-time 10 "http://localhost:8000/api/v1/monitoring/health" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Application restart successful"
    else
        echo "Application restart failed - escalating..."
    fi
fi

if [ $DB_STATUS -ne 0 ]; then
    echo "Database is down - checking status..."
    systemctl status postgresql
    echo "Manual intervention required for database issues"
fi

# Step 3: Notification
echo "3. NOTIFICATIONS"
echo "Sending emergency notifications..."
# In production: send alerts to phone, email, Slack

# Step 4: Logging
echo "4. INCIDENT LOGGING"
INCIDENT_ID="INC_$(date +%Y%m%d_%H%M%S)"
echo "Incident ID: $INCIDENT_ID"

cat >> /var/log/emergency_incidents.log << EOF
[$(date -Iseconds)] EMERGENCY INCIDENT: $INCIDENT_ID
Application Status: $([ $APP_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')
Database Status: $([ $DB_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')
Redis Status: $([ $REDIS_STATUS -eq 0 ] && echo 'UP' || echo 'DOWN')
Response Actions: Attempted automatic recovery
EOF

echo "=== EMERGENCY RESPONSE LOG: /var/log/emergency_incidents.log ==="
```

### Communication Templates

#### Incident Notification Template
```
SUBJECT: [URGENT] CLO System Incident - {INCIDENT_ID}

INCIDENT SUMMARY
Incident ID: {INCIDENT_ID}
Severity: {SEVERITY}
Status: {STATUS}
Detected: {DETECTION_TIME}

IMPACT
- Affected Services: {AFFECTED_SERVICES}
- User Impact: {USER_IMPACT}
- Business Impact: {BUSINESS_IMPACT}

CURRENT STATUS
{CURRENT_STATUS_DESCRIPTION}

ACTIONS TAKEN
- {ACTION_1}
- {ACTION_2}
- {ACTION_3}

NEXT UPDATES
Next update scheduled for: {NEXT_UPDATE_TIME}

CONTACT INFORMATION
Primary: {PRIMARY_CONTACT}
Secondary: {SECONDARY_CONTACT}

This is an automated message. For urgent issues, call {EMERGENCY_PHONE}.
```

This comprehensive troubleshooting and maintenance guide provides the necessary procedures and scripts to maintain a healthy, secure, and performant CLO Management System.