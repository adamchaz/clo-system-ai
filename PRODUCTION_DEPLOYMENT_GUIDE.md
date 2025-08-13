# CLO Management System - Production Deployment Guide

## 🚀 **Production Deployment Overview**

This guide provides comprehensive instructions for deploying the CLO Management System to production with enterprise security, monitoring, and scalability.

## 📋 **Prerequisites**

### **Infrastructure Requirements**
- **Docker**: Version 20.10+ with Docker Compose v2
- **SSL Certificates**: Valid SSL certificates for your production domain
- **Database**: PostgreSQL 13+ (cloud or self-hosted)
- **Cache**: Redis 6+ with persistence
- **Domain**: Registered domain with DNS configuration
- **Server**: Linux server with minimum 8GB RAM, 4 CPU cores, 100GB storage

### **Security Requirements**
- **Secrets Management**: Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault
- **Backup Storage**: Cloud storage for database backups
- **Monitoring**: Application monitoring and alerting system
- **SSL/TLS**: Valid certificates from trusted CA

## 🔧 **Step 1: Environment Preparation**

### **1.1 Create Production Environment File**

Create `.env.production` with actual production values:

```bash
# Copy the template and customize
cp backend/.env.production .env.production
```

**🔒 CRITICAL: Update these values:**

```bash
# Security - Generate secure values
PRODUCTION_SECRET_KEY="your-256-bit-secret-key"
PRODUCTION_DATABASE_URL="postgresql://username:password@production-host:5432/clo_production"
PRODUCTION_REDIS_URL="redis://username:password@production-host:6379"

# Domain Configuration
PRODUCTION_DOMAIN="your-domain.com"
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]

# SSL Certificates
SSL_CERTIFICATE_PATH="/path/to/ssl/cert.pem"
SSL_PRIVATE_KEY_PATH="/path/to/ssl/private-key.pem"
SSL_CA_BUNDLE_PATH="/path/to/ssl/ca-bundle.pem"

# Azure Integration (if using Azure)
AZURE_STORAGE_ACCOUNT="your-storage-account"
AZURE_STORAGE_KEY="your-storage-key"
AZURE_KEY_VAULT_URL="https://your-vault.vault.azure.net/"

# Email Configuration
PRODUCTION_SMTP_HOST="smtp.your-provider.com"
PRODUCTION_SMTP_USERNAME="noreply@your-domain.com"
PRODUCTION_SMTP_PASSWORD="your-smtp-password"
```

### **1.2 Generate Security Credentials**

```bash
# Generate secret key (256-bit)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT key pair (RSA 2048-bit)
openssl genrsa -out jwt-private-key.pem 2048
openssl rsa -in jwt-private-key.pem -pubout -out jwt-public-key.pem
```

### **1.3 Prepare SSL Certificates**

```bash
# Create certificate directory
mkdir -p /opt/clo-system/certs

# Copy SSL certificates (from your CA provider)
cp your-domain.crt /opt/clo-system/certs/ssl-cert.pem
cp your-domain.key /opt/clo-system/certs/ssl-key.pem
cp ca-bundle.crt /opt/clo-system/certs/ssl-ca.pem

# Set proper permissions
chmod 600 /opt/clo-system/certs/*
chown -R root:docker /opt/clo-system/certs
```

## 🗄️ **Step 2: Database Setup**

### **2.1 PostgreSQL Production Configuration**

Create production database:

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE clo_production;
CREATE USER clo_prod WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE clo_production TO clo_prod;

-- Enable required extensions
\c clo_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

### **2.2 Database Migration**

```bash
# Run database migrations
cd backend
python -m alembic upgrade head

# Verify migration
python -c "from app.core.database import DatabaseManager; print('✅ Database connection:', DatabaseManager.test_connection())"
```

### **2.3 Initial Data Setup**

```bash
# Create admin user
python scripts/create_admin_user.py --email admin@your-domain.com --password your-admin-password

# Load reference data
python scripts/load_reference_data.py --environment production
```

## 🐳 **Step 3: Docker Deployment**

### **3.1 Build Production Images**

```bash
# Build backend image
docker build -f backend/Dockerfile.production -t clo-system/api:latest backend/

# Build frontend image (if using Docker for frontend)
docker build -f frontend/Dockerfile.production -t clo-system/frontend:latest frontend/

# Verify images
docker images | grep clo-system
```

### **3.2 Deploy with Docker Compose**

```bash
# Set environment variables for Docker Compose
export PRODUCTION_DATABASE_URL="postgresql://user:pass@host:5432/clo_production"
export PRODUCTION_REDIS_URL="redis://user:pass@host:6379"
export PRODUCTION_SECRET_KEY="your-secret-key"
export PRODUCTION_DOMAIN="your-domain.com"
export SSL_CERTS_PATH="/opt/clo-system/certs"
export PRODUCTION_DATA_PATH="/opt/clo-system/data"
export PRODUCTION_LOG_PATH="/opt/clo-system/logs"
export PRODUCTION_BACKUP_PATH="/opt/clo-system/backups"

# Deploy production stack
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs -f clo-api
```

### **3.3 Health Check Validation**

```bash
# Test API health
curl -f https://your-domain.com/api/v1/monitoring/health/live

# Test comprehensive health
curl -H "Authorization: Bearer your-jwt-token" \
     https://your-domain.com/api/v1/monitoring/health/detailed

# Test database connectivity
curl https://your-domain.com/api/v1/monitoring/health/database
```

## 🔐 **Step 4: Security Hardening**

### **4.1 Firewall Configuration**

```bash
# Configure firewall (Ubuntu/Debian)
ufw enable
ufw allow ssh
ufw allow 80/tcp   # HTTP (redirects to HTTPS)
ufw allow 443/tcp  # HTTPS
ufw allow 9090/tcp # Prometheus (internal network only)
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw deny 6379/tcp  # Redis (internal only)
```

### **4.2 SSL/HTTPS Configuration**

```nginx
# nginx configuration for SSL termination
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/ssl-cert.pem;
    ssl_certificate_key /etc/nginx/ssl/ssl-key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    location / {
        proxy_pass http://clo-frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://clo-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **4.3 Database Security**

```bash
# PostgreSQL security configuration
echo "ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
log_statement = 'all'" >> /etc/postgresql/15/main/postgresql.conf
```

## 📊 **Step 5: Monitoring Setup**

### **5.1 Application Monitoring**

```bash
# Access Grafana dashboard
https://your-domain.com:3001
# Default login: admin / your-grafana-password

# Access Prometheus metrics
https://your-domain.com:9090
```

### **5.2 Log Monitoring**

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f clo-api

# Access log files
tail -f /opt/clo-system/logs/app.log
tail -f /opt/clo-system/logs/access.log
tail -f /opt/clo-system/logs/error.log
```

### **5.3 Health Monitoring**

```bash
# Set up health check monitoring (cron job)
echo "*/5 * * * * curl -f https://your-domain.com/api/v1/monitoring/health/live || echo 'API Health Check Failed' | mail -s 'CLO System Alert' admin@your-domain.com" | crontab -
```

## 💾 **Step 6: Backup Configuration**

### **6.1 Database Backup**

Create backup script:

```bash
#!/bin/bash
# /opt/clo-system/scripts/backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/clo-system/backups"
DB_NAME="clo_production"

# Create backup
pg_dump -h localhost -U clo_prod -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Upload to cloud storage (Azure example)
az storage blob upload --account-name $AZURE_STORAGE_ACCOUNT \
                      --container-name backups \
                      --name db_backup_$DATE.sql.gz \
                      --file $BACKUP_DIR/db_backup_$DATE.sql.gz

# Clean old local backups (keep last 7 days)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

### **6.2 Schedule Backups**

```bash
# Add to crontab
echo "0 2 * * * /opt/clo-system/scripts/backup-database.sh" | crontab -

# Verify backup schedule
crontab -l
```

## 🔄 **Step 7: CI/CD Pipeline Setup**

### **7.1 GitHub Actions Configuration**

Create `.github/workflows/production-deploy.yml`:

```yaml
name: Production Deployment

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to Production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/clo-system
          git pull origin main
          docker-compose -f docker-compose.production.yml down
          docker-compose -f docker-compose.production.yml build
          docker-compose -f docker-compose.production.yml up -d
          
          # Health check
          sleep 30
          curl -f https://${{ secrets.PRODUCTION_DOMAIN }}/api/v1/monitoring/health/live
```

## ✅ **Step 8: Production Validation**

### **8.1 Functional Testing**

```bash
# Test API endpoints
curl -X GET https://your-domain.com/api/v1/assets
curl -X GET https://your-domain.com/api/v1/portfolios  
curl -X GET https://your-domain.com/api/v1/monitoring/health/detailed

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin@your-domain.com", "password": "your-password"}'
```

### **8.2 Performance Testing**

```bash
# Load test with Apache Bench
ab -n 1000 -c 10 https://your-domain.com/api/v1/monitoring/health/live

# Monitor resource usage
docker stats
```

### **8.3 Security Testing**

```bash
# SSL certificate validation
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Security headers validation
curl -I https://your-domain.com
```

## 🚨 **Step 9: Monitoring & Alerting**

### **9.1 Set Up Alerts**

```bash
# Email alerts for system issues
# Configure in Grafana or use external monitoring service

# Disk space monitoring
echo "*/10 * * * * df -h | awk '$5 > 80 {print $0}' | mail -s 'Disk Space Alert' admin@your-domain.com" | crontab -

# Memory monitoring  
echo "*/5 * * * * free -m | awk 'NR==2{printf \"Memory Usage: %s/%sMB (%.2f%%)\\n\", \$3,\$2,\$3*100/\$2 }' | awk '{if(\$5 > 80.00) print \$0}' | mail -s 'Memory Alert' admin@your-domain.com" | crontab -
```

## 📚 **Step 10: Documentation & Handover**

### **10.1 Create Operations Manual**

- **System Architecture**: Document deployed components
- **Monitoring Procedures**: Health checks and alerts
- **Backup/Recovery**: Restoration procedures
- **Troubleshooting**: Common issues and solutions
- **Contact Information**: Support and escalation contacts

### **10.2 User Training**

- **Administrator Training**: System management and monitoring
- **End User Training**: Application features and workflows
- **Support Documentation**: User guides and FAQs

## 🎯 **Production Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrated and tested
- [ ] Backup procedures tested
- [ ] Monitoring configured
- [ ] Security hardening completed

### **Post-Deployment**
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Frontend application loading
- [ ] Authentication working
- [ ] Monitoring dashboards operational
- [ ] Backup schedule active
- [ ] Documentation complete
- [ ] User training conducted

## 🚀 **Go-Live Success Criteria**

✅ **System Health**: All health checks green  
✅ **Performance**: Response times < 500ms  
✅ **Security**: SSL/TLS configured, security headers active  
✅ **Monitoring**: Dashboards operational, alerts configured  
✅ **Backup**: Automated backups working  
✅ **Documentation**: Operations manual complete  
✅ **Training**: Users trained and ready  

**🎉 Congratulations! Your CLO Management System is now live in production!**