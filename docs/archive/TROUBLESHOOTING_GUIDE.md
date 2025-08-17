# CLO Management System - Troubleshooting Guide

## 🔧 **Quick Reference**

This guide provides step-by-step troubleshooting procedures for common issues in the CLO Management System.

## ⚡ **Emergency Quick Fixes**

### **System Not Responding**
```bash
# Check system status
docker-compose -f docker-compose.production.yml ps

# Restart services
docker-compose -f docker-compose.production.yml restart

# Check logs for errors
docker-compose -f docker-compose.production.yml logs --tail=100
```

### **Database Connection Failed**
```bash
# Test database connectivity
psql -h localhost -p 5433 -U postgres -d clo_dev

# Restart database
docker-compose -f docker-compose.production.yml restart postgres

# Check database logs
docker logs clo-postgres-prod --tail=50
```

### **Users Cannot Login**
```bash
# Check authentication service
curl -f https://your-domain.com/api/v1/monitoring/health/live

# Restart API service
docker-compose -f docker-compose.production.yml restart clo-api

# Check authentication logs
docker logs clo-api-prod | grep "auth"
```

## 🖥️ **System Issues**

### **High CPU Usage**

#### **Symptoms**
- System response times > 1 second
- API endpoints timing out
- Dashboard loading slowly
- High server temperature alerts

#### **Diagnosis Steps**
1. **Check Current CPU Usage**
   ```bash
   # System-wide CPU usage
   htop
   
   # Container-specific usage
   docker stats --no-stream
   
   # Process analysis
   ps aux --sort=-%cpu | head -10
   ```

2. **Identify Resource-Heavy Operations**
   ```bash
   # Check running calculations
   curl -H "Authorization: Bearer $TOKEN" \
        https://your-domain.com/api/v1/monitoring/system/processes
   
   # Database query analysis
   SELECT query, calls, mean_time, total_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;
   ```

#### **Resolution Steps**
1. **Immediate Relief**
   - Kill non-essential processes
   - Pause heavy calculations
   - Implement rate limiting

2. **Medium-term Fix**
   - Optimize database queries
   - Scale up CPU resources
   - Implement caching

3. **Long-term Solution**
   - Horizontal scaling
   - Code optimization
   - Infrastructure upgrade

### **Memory Issues**

#### **Symptoms**
- Out of memory errors
- Application crashes
- Slow garbage collection
- Docker containers restarting

#### **Diagnosis Steps**
```bash
# System memory usage
free -h

# Container memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Memory-consuming processes
ps aux --sort=-%mem | head -10
```

#### **Memory Leak Detection**
```python
# Monitor Python memory usage
import psutil
import gc

def check_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'objects': len(gc.get_objects())
    }
```

#### **Resolution Steps**
1. **Immediate**
   - Restart services with memory issues
   - Clear application caches
   - Reduce concurrent operations

2. **Short-term**
   - Increase memory allocation
   - Optimize data structures
   - Implement memory monitoring

3. **Long-term**
   - Fix memory leaks in code
   - Implement proper garbage collection
   - Scale infrastructure

## 🗄️ **Database Issues**

### **Slow Query Performance**

#### **Symptoms**
- API responses > 500ms
- Dashboard loading slowly
- Database timeout errors
- High database CPU usage

#### **Diagnosis Steps**
1. **Identify Slow Queries**
   ```sql
   -- Enable query logging
   ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1 second
   SELECT pg_reload_conf();
   
   -- Check slow queries
   SELECT query, calls, total_time, mean_time, stddev_time
   FROM pg_stat_statements 
   WHERE mean_time > 100  -- queries > 100ms
   ORDER BY mean_time DESC;
   ```

2. **Query Analysis**
   ```sql
   -- Analyze specific query
   EXPLAIN ANALYZE VERBOSE 
   SELECT * FROM portfolios p 
   JOIN assets a ON p.id = a.portfolio_id 
   WHERE p.status = 'active';
   ```

#### **Resolution Steps**
1. **Query Optimization**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_assets_portfolio_id ON assets(portfolio_id);
   CREATE INDEX CONCURRENTLY idx_portfolios_status ON portfolios(status);
   
   -- Update statistics
   ANALYZE portfolios;
   ANALYZE assets;
   ```

2. **Configuration Tuning**
   ```sql
   -- Optimize PostgreSQL settings
   ALTER SYSTEM SET shared_buffers = '2GB';
   ALTER SYSTEM SET effective_cache_size = '6GB';  
   ALTER SYSTEM SET work_mem = '256MB';
   SELECT pg_reload_conf();
   ```

### **Connection Pool Exhaustion**

#### **Symptoms**
- "Too many connections" errors
- New users cannot login
- API requests timing out
- Database refusing connections

#### **Diagnosis Steps**
```sql
-- Check current connections
SELECT count(*) as active_connections FROM pg_stat_activity;

-- Check connection details
SELECT datname, usename, application_name, client_addr, state, query_start
FROM pg_stat_activity 
ORDER BY query_start;

-- Check connection limits
SHOW max_connections;
```

#### **Resolution Steps**
1. **Immediate**
   ```sql
   -- Kill idle connections
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity 
   WHERE state = 'idle' AND query_start < now() - interval '1 hour';
   ```

2. **Configuration Fix**
   ```python
   # backend/app/core/database.py
   engine = create_engine(
       database_url,
       pool_size=20,        # Increase pool size
       max_overflow=30,     # Allow overflow connections
       pool_timeout=30,     # Connection timeout
       pool_recycle=3600,   # Recycle connections hourly
       pool_pre_ping=True   # Validate connections
   )
   ```

### **Database Corruption**

#### **Symptoms**
- Data inconsistency errors
- Constraint violation failures
- Index corruption warnings
- Unexpected query results

#### **Diagnosis Steps**
```sql
-- Check database integrity
SELECT datname, pg_database_size(datname) as size
FROM pg_database;

-- Check for corruption
REINDEX DATABASE clo_production;

-- Validate constraints
SELECT conname, conrelid::regclass
FROM pg_constraint
WHERE NOT convalidated;
```

#### **Recovery Procedures**
1. **Minor Corruption**
   ```sql
   -- Reindex specific tables
   REINDEX TABLE portfolios;
   REINDEX TABLE assets;
   
   -- Validate and fix constraints
   ALTER TABLE assets VALIDATE CONSTRAINT assets_portfolio_fk;
   ```

2. **Major Corruption**
   ```bash
   # Stop application
   docker-compose -f docker-compose.production.yml stop clo-api
   
   # Restore from backup
   pg_restore -h localhost -U postgres -d clo_production_new backup_file.sql
   
   # Verify data integrity
   python scripts/validate_data_integrity.py
   
   # Switch to new database
   # Update connection string and restart
   ```

## 🌐 **Network and Connectivity Issues**

### **API Endpoints Not Responding**

#### **Symptoms**
- 404 errors for valid endpoints
- Connection timeout errors
- Intermittent connectivity
- Load balancer errors

#### **Diagnosis Steps**
```bash
# Test specific endpoints
curl -v https://your-domain.com/api/v1/monitoring/health/live

# Check API service status
docker logs clo-api-prod --tail=50

# Test internal connectivity
docker exec clo-api-prod curl http://localhost:8000/health

# Check load balancer
curl -I https://your-domain.com
```

#### **Resolution Steps**
1. **Service Issues**
   ```bash
   # Restart API service
   docker-compose -f docker-compose.production.yml restart clo-api
   
   # Check service health
   docker-compose -f docker-compose.production.yml ps clo-api
   ```

2. **Load Balancer Issues**
   - Check load balancer configuration
   - Verify SSL certificate validity
   - Update DNS if necessary

### **WebSocket Connection Problems**

#### **Symptoms**
- Real-time updates not working
- "Connection failed" in browser console
- Intermittent disconnections
- Client-side timeout errors

#### **Diagnosis Steps**
```bash
# Test WebSocket connectivity
wscat -c wss://your-domain.com/ws

# Check WebSocket logs
docker logs clo-api-prod | grep "websocket"

# Browser testing
# Open browser console and check for WebSocket errors
```

#### **Resolution Steps**
```python
# backend/app/websocket.py
# Add connection health checks
@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send periodic ping
            await websocket.send_json({"type": "ping"})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

## 🔐 **Authentication and Authorization Issues**

### **Users Cannot Login**

#### **Symptoms**
- Invalid credentials errors (with correct password)
- JWT token validation failures
- Session timeout issues
- MFA not working

#### **Diagnosis Steps**
1. **Test Authentication Flow**
   ```bash
   # Test login endpoint
   curl -X POST https://your-domain.com/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username": "test@company.com", "password": "password123"}'
   
   # Check authentication logs
   docker logs clo-api-prod | grep "authentication"
   ```

2. **Database User Verification**
   ```sql
   -- Check user account status
   SELECT username, email, is_active, last_login, failed_login_attempts
   FROM users 
   WHERE email = 'user@company.com';
   ```

#### **Resolution Steps**
1. **Account Issues**
   ```sql
   -- Reset failed login attempts
   UPDATE users 
   SET failed_login_attempts = 0, account_locked_until = NULL
   WHERE email = 'user@company.com';
   
   -- Activate account
   UPDATE users 
   SET is_active = true
   WHERE email = 'user@company.com';
   ```

2. **JWT Issues**
   ```python
   # Reset user sessions
   redis-cli DEL "user_session:user123"
   
   # Generate new JWT secret (requires restart)
   # Update SECRET_KEY in environment
   ```

### **Permission Denied Errors**

#### **Symptoms**
- 403 Forbidden responses
- "Insufficient permissions" messages
- Features not visible to users
- API access denied

#### **Diagnosis Steps**
```sql
-- Check user permissions
SELECT u.username, r.name as role, p.name as permission
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id  
JOIN permissions p ON rp.permission_id = p.id
WHERE u.email = 'user@company.com';
```

#### **Resolution Steps**
```sql
-- Grant missing permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'financial_analyst' 
  AND p.name = 'portfolio_read';

-- Update user role
UPDATE user_roles 
SET role_id = (SELECT id FROM roles WHERE name = 'portfolio_manager')
WHERE user_id = (SELECT id FROM users WHERE email = 'user@company.com');
```

## 📊 **Performance Issues**

### **Slow Report Generation**

#### **Symptoms**
- Report timeouts (>10 minutes)
- Memory errors during generation
- Incomplete reports
- Browser crashes

#### **Diagnosis Steps**
```python
# Check report generation logs
import logging
logger = logging.getLogger('report_generation')

def diagnose_report_performance():
    # Monitor memory usage
    import psutil
    process = psutil.Process()
    
    # Check database query performance
    # Monitor file I/O
    # Track processing time per section
```

#### **Resolution Steps**
1. **Optimize Queries**
   ```sql
   -- Use pagination for large datasets
   SELECT * FROM portfolio_data 
   LIMIT 1000 OFFSET 0;
   
   -- Add appropriate indexes
   CREATE INDEX CONCURRENTLY idx_portfolio_data_date ON portfolio_data(report_date);
   ```

2. **Implement Streaming**
   ```python
   # Stream large reports instead of loading all in memory
   def generate_large_report():
       yield header_section()
       for chunk in data_chunks():
           yield process_chunk(chunk)
       yield footer_section()
   ```

### **Frontend Performance Issues**

#### **Symptoms**
- Slow page loading (>5 seconds)
- Unresponsive user interface
- Browser memory warnings
- Chart rendering issues

#### **Diagnosis Steps**
```javascript
// Browser performance monitoring
performance.mark('page-load-start');
// ... page loading code ...
performance.mark('page-load-end');
performance.measure('page-load', 'page-load-start', 'page-load-end');

const measures = performance.getEntriesByType('measure');
console.log('Page load time:', measures[0].duration);
```

#### **Resolution Steps**
1. **Optimize Bundle Size**
   ```javascript
   // Implement code splitting
   const LazyComponent = React.lazy(() => import('./HeavyComponent'));
   
   // Use React.memo for expensive components
   const OptimizedComponent = React.memo(({ data }) => {
       return <ExpensiveVisualization data={data} />;
   });
   ```

2. **Data Optimization**
   ```javascript
   // Implement virtual scrolling for large datasets
   import { FixedSizeList as List } from 'react-window';
   
   // Paginate large data requests
   const { data } = useQuery(['portfolios', page], 
       () => fetchPortfolios({ page, limit: 50 })
   );
   ```

## 🔍 **Monitoring and Logging Issues**

### **Missing Log Data**

#### **Symptoms**
- Empty log files
- Missing error messages
- Incomplete audit trails
- Monitoring gaps

#### **Diagnosis Steps**
```bash
# Check log file permissions
ls -la /var/log/clo-system/

# Verify log rotation
logrotate -d /etc/logrotate.d/clo-system

# Check disk space for logs
df -h /var/log
```

#### **Resolution Steps**
```bash
# Fix log permissions
chmod 644 /var/log/clo-system/*.log
chown clo:clo /var/log/clo-system/*.log

# Restart logging service
systemctl restart rsyslog

# Verify log configuration
tail -f /var/log/clo-system/app.log
```

### **Monitoring Dashboard Issues**

#### **Symptoms**
- Missing metrics data
- Dashboard not updating
- Graph display errors
- Alert failures

#### **Diagnosis Steps**
```bash
# Check Prometheus status
curl http://localhost:9090/api/v1/query?query=up

# Verify Grafana connection
curl http://localhost:3001/api/health

# Test metric collection
curl http://localhost:8000/metrics
```

#### **Resolution Steps**
```yaml
# Update Prometheus configuration
# prometheus.yml
scrape_configs:
  - job_name: 'clo-system'
    static_configs:
      - targets: ['clo-api:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

## 📞 **Getting Help**

### **Internal Escalation**
1. **Check Documentation**: Review this guide and system documentation
2. **System Logs**: Gather relevant log files and error messages  
3. **Reproduce Issue**: Document steps to reproduce the problem
4. **Contact Support**: Email support team with detailed information

### **External Support**
- **Database Issues**: PostgreSQL Enterprise Support
- **Infrastructure**: Cloud provider support (Azure/AWS)
- **Security**: Security vendor support
- **Application**: Development team or vendor support

### **Emergency Contacts**
- **System Administrator**: admin@your-domain.com
- **On-Call Engineer**: +1-555-EMERGENCY  
- **Development Team**: dev-team@your-domain.com
- **Management**: manager@your-domain.com

---

**This troubleshooting guide covers the most common issues and their resolution procedures. For complex issues not covered here, contact the support team with detailed error information.**