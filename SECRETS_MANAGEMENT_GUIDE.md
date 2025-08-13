# CLO Management System - Secrets Management Guide

## 🔐 **Production Secrets Management**

This guide provides comprehensive instructions for securely managing secrets, credentials, and sensitive configuration in production.

## 📋 **Security Principles**

### **Never Store Secrets In:**
- ❌ Source code repositories
- ❌ Docker images
- ❌ Configuration files in plain text
- ❌ Environment variables in Docker Compose files
- ❌ Documentation or README files

### **Always Store Secrets In:**
- ✅ Dedicated secrets management systems (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault)
- ✅ Encrypted environment variables
- ✅ Secure credential stores
- ✅ Hardware Security Modules (HSMs) for critical keys

## 🔑 **Required Secrets for Production**

### **Database Secrets**
```bash
PRODUCTION_POSTGRES_USER="secure-username"
PRODUCTION_POSTGRES_PASSWORD="complex-password-32-chars+"
PRODUCTION_DATABASE_URL="postgresql://user:pass@host:5432/db"
```

### **Redis Cache Secrets**
```bash
PRODUCTION_REDIS_PASSWORD="secure-redis-password"
PRODUCTION_REDIS_URL="redis://user:pass@host:6379"
```

### **Application Security Secrets**
```bash
PRODUCTION_SECRET_KEY="256-bit-secret-key-for-jwt-signing"
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----..."
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
```

### **SSL/TLS Certificates**
```bash
SSL_CERTIFICATE="-----BEGIN CERTIFICATE-----..."
SSL_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
SSL_CA_BUNDLE="-----BEGIN CERTIFICATE-----..."
```

### **External Service Secrets**
```bash
AZURE_STORAGE_KEY="azure-storage-account-key"
AZURE_KEY_VAULT_CLIENT_SECRET="azure-service-principal-secret"
SMTP_PASSWORD="email-service-password"
GRAFANA_ADMIN_PASSWORD="monitoring-dashboard-password"
```

## ☁️ **Azure Key Vault Configuration**

### **Step 1: Create Azure Key Vault**

```bash
# Create resource group
az group create --name clo-system-prod --location eastus

# Create Key Vault
az keyvault create \
  --name clo-system-vault \
  --resource-group clo-system-prod \
  --location eastus \
  --sku standard \
  --enable-rbac-authorization

# Get Key Vault URL
az keyvault show --name clo-system-vault --query properties.vaultUri
```

### **Step 2: Create Service Principal**

```bash
# Create service principal for application access
az ad sp create-for-rbac --name clo-system-app --role contributor

# Note the output:
# {
#   "appId": "your-app-id",
#   "displayName": "clo-system-app", 
#   "password": "your-service-principal-password",
#   "tenant": "your-tenant-id"
# }
```

### **Step 3: Grant Key Vault Permissions**

```bash
# Assign Key Vault Secrets User role to service principal
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "your-app-id" \
  --scope "/subscriptions/your-subscription-id/resourceGroups/clo-system-prod/providers/Microsoft.KeyVault/vaults/clo-system-vault"
```

### **Step 4: Add Secrets to Key Vault**

```bash
# Database secrets
az keyvault secret set --vault-name clo-system-vault --name "postgres-password" --value "your-secure-password"
az keyvault secret set --vault-name clo-system-vault --name "database-url" --value "postgresql://user:pass@host:5432/db"

# Redis secrets
az keyvault secret set --vault-name clo-system-vault --name "redis-password" --value "your-redis-password"

# Application secrets
az keyvault secret set --vault-name clo-system-vault --name "secret-key" --value "your-256-bit-secret-key"
az keyvault secret set --vault-name clo-system-vault --name "jwt-private-key" --file jwt-private-key.pem
az keyvault secret set --vault-name clo-system-vault --name "jwt-public-key" --file jwt-public-key.pem

# SSL certificates
az keyvault secret set --vault-name clo-system-vault --name "ssl-certificate" --file ssl-cert.pem
az keyvault secret set --vault-name clo-system-vault --name "ssl-private-key" --file ssl-key.pem

# External service secrets
az keyvault secret set --vault-name clo-system-vault --name "azure-storage-key" --value "your-storage-key"
az keyvault secret set --vault-name clo-system-vault --name "smtp-password" --value "your-smtp-password"
```

### **Step 5: Application Integration**

Create Azure Key Vault integration service:

```python
# backend/app/core/secrets.py
"""
Azure Key Vault integration for secrets management
"""

import os
from typing import Optional, Dict, Any
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from .config import settings

class SecretsManager:
    """Azure Key Vault secrets manager"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure Key Vault client"""
        if not settings.azure_key_vault_url:
            return
            
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET")
        )
        
        self.client = SecretClient(
            vault_url=settings.azure_key_vault_url,
            credential=credential
        )
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from Azure Key Vault"""
        if not self.client:
            return None
            
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            print(f"Failed to retrieve secret '{secret_name}': {e}")
            return None
    
    def get_database_url(self) -> str:
        """Get database URL from secrets"""
        url = self.get_secret("database-url")
        return url or settings.database_url
    
    def get_redis_url(self) -> str:
        """Get Redis URL from secrets"""
        url = self.get_secret("redis-url")
        return url or settings.redis_url
    
    def get_secret_key(self) -> str:
        """Get application secret key"""
        key = self.get_secret("secret-key")
        return key or settings.secret_key
    
    def get_jwt_keys(self) -> Dict[str, str]:
        """Get JWT signing keys"""
        return {
            "private_key": self.get_secret("jwt-private-key"),
            "public_key": self.get_secret("jwt-public-key")
        }
    
    def get_ssl_certificates(self) -> Dict[str, str]:
        """Get SSL certificates"""
        return {
            "certificate": self.get_secret("ssl-certificate"),
            "private_key": self.get_secret("ssl-private-key"),
            "ca_bundle": self.get_secret("ssl-ca-bundle")
        }

# Global secrets manager instance
secrets_manager = SecretsManager()
```

## 🚢 **Docker Secrets Integration**

### **Production Docker Compose with Secrets**

```yaml
# docker-compose.production.yml (secrets section)
version: '3.8'

services:
  clo-api:
    image: clo-system/api:latest
    environment:
      # Reference Docker secrets instead of environment variables
      - DATABASE_URL_FILE=/run/secrets/database_url
      - REDIS_URL_FILE=/run/secrets/redis_url
      - SECRET_KEY_FILE=/run/secrets/secret_key
    secrets:
      - database_url
      - redis_url
      - secret_key
      - jwt_private_key
      - jwt_public_key
      - ssl_certificate
      - ssl_private_key
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure

secrets:
  database_url:
    external: true
  redis_url:
    external: true
  secret_key:
    external: true
  jwt_private_key:
    file: /opt/clo-system/secrets/jwt-private-key.pem
  jwt_public_key:
    file: /opt/clo-system/secrets/jwt-public-key.pem
  ssl_certificate:
    file: /opt/clo-system/secrets/ssl-cert.pem
  ssl_private_key:
    file: /opt/clo-system/secrets/ssl-key.pem
```

### **Create Docker Secrets**

```bash
# Create Docker secrets from files
echo "postgresql://user:pass@host:5432/db" | docker secret create database_url -
echo "redis://user:pass@host:6379" | docker secret create redis_url -
echo "your-256-bit-secret-key" | docker secret create secret_key -

# Create secrets from files
docker secret create jwt_private_key /opt/clo-system/secrets/jwt-private-key.pem
docker secret create ssl_certificate /opt/clo-system/secrets/ssl-cert.pem

# List secrets
docker secret ls
```

## 🔧 **Environment Variable Security**

### **Secure Environment Configuration**

```bash
# Create secure environment file
sudo mkdir -p /opt/clo-system/config
sudo chmod 700 /opt/clo-system/config

# Create production environment file with restricted permissions
sudo touch /opt/clo-system/config/.env.production
sudo chmod 600 /opt/clo-system/config/.env.production
sudo chown root:docker /opt/clo-system/config/.env.production
```

### **Environment File Template**

```bash
# /opt/clo-system/config/.env.production
# 🔒 PRODUCTION SECRETS - RESTRICTED ACCESS ONLY

# Azure Authentication (for Key Vault access)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id  
AZURE_CLIENT_SECRET=your-client-secret
AZURE_KEY_VAULT_URL=https://clo-system-vault.vault.azure.net/

# Database Configuration (fallback if Key Vault unavailable)
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_SSL_MODE=require

# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Monitoring Configuration  
GRAFANA_ADMIN_PASSWORD=your-grafana-password
PROMETHEUS_ADMIN_PASSWORD=your-prometheus-password

# Domain and SSL
PRODUCTION_DOMAIN=your-domain.com
FORCE_HTTPS=true
```

## 🛡️ **Secret Rotation Strategy**

### **Automated Secret Rotation**

```bash
#!/bin/bash
# /opt/clo-system/scripts/rotate-secrets.sh

echo "Starting secret rotation..."

# Generate new database password
NEW_DB_PASSWORD=$(openssl rand -base64 32)

# Update database user password
PGPASSWORD=$OLD_DB_PASSWORD psql -h $DB_HOST -U $DB_USER -c "ALTER USER $DB_USER PASSWORD '$NEW_DB_PASSWORD';"

# Update Key Vault with new password
az keyvault secret set --vault-name clo-system-vault --name "postgres-password" --value "$NEW_DB_PASSWORD"

# Generate new JWT keys
openssl genrsa -out /tmp/jwt-private-key.pem 2048
openssl rsa -in /tmp/jwt-private-key.pem -pubout -out /tmp/jwt-public-key.pem

# Update Key Vault with new JWT keys
az keyvault secret set --vault-name clo-system-vault --name "jwt-private-key" --file /tmp/jwt-private-key.pem
az keyvault secret set --vault-name clo-system-vault --name "jwt-public-key" --file /tmp/jwt-public-key.pem

# Clean up temporary files
rm /tmp/jwt-private-key.pem /tmp/jwt-public-key.pem

# Restart application to pick up new secrets
docker-compose -f docker-compose.production.yml restart clo-api

echo "Secret rotation completed successfully!"
```

### **Rotation Schedule**

```bash
# Add to crontab for monthly rotation
echo "0 2 1 * * /opt/clo-system/scripts/rotate-secrets.sh 2>&1 | logger -t secret-rotation" | crontab -

# Verify rotation schedule
crontab -l
```

## 📊 **Secrets Monitoring**

### **Secret Expiration Monitoring**

```python
# backend/app/monitoring/secrets_monitor.py
"""
Monitor secrets for expiration and rotation requirements
"""

from datetime import datetime, timedelta
from azure.keyvault.secrets import SecretClient
from .core.secrets import secrets_manager

class SecretsMonitor:
    """Monitor secrets for security compliance"""
    
    def check_secret_age(self, secret_name: str) -> dict:
        """Check if secret needs rotation based on age"""
        try:
            client = secrets_manager.client
            secret = client.get_secret(secret_name)
            
            created_date = secret.properties.created_on
            age_days = (datetime.now() - created_date).days
            
            # Rotation thresholds
            warning_threshold = 75  # days
            critical_threshold = 90  # days
            
            status = "ok"
            if age_days >= critical_threshold:
                status = "critical"
            elif age_days >= warning_threshold:
                status = "warning"
            
            return {
                "secret_name": secret_name,
                "age_days": age_days,
                "status": status,
                "created_date": created_date.isoformat(),
                "needs_rotation": status in ["warning", "critical"]
            }
        except Exception as e:
            return {
                "secret_name": secret_name,
                "status": "error",
                "error": str(e)
            }
    
    def audit_all_secrets(self) -> list:
        """Audit all production secrets"""
        secrets_to_check = [
            "postgres-password",
            "redis-password", 
            "secret-key",
            "jwt-private-key",
            "jwt-public-key",
            "ssl-certificate",
            "ssl-private-key",
            "azure-storage-key",
            "smtp-password"
        ]
        
        return [self.check_secret_age(secret) for secret in secrets_to_check]
```

### **Security Alerts**

```bash
#!/bin/bash
# /opt/clo-system/scripts/check-secret-security.sh

# Check for secrets in logs (should return no results)
if grep -r "password\|secret\|key" /opt/clo-system/logs/ 2>/dev/null; then
    echo "⚠️ WARNING: Potential secrets found in logs!" | mail -s "Security Alert: Secrets in Logs" admin@your-domain.com
fi

# Check file permissions on secret files
find /opt/clo-system/secrets/ -type f ! -perm 600 -exec echo "⚠️ WARNING: Secret file {} has incorrect permissions!" \; | mail -s "Security Alert: File Permissions" admin@your-domain.com

# Check for expired SSL certificates
openssl x509 -in /opt/clo-system/secrets/ssl-cert.pem -noout -checkend 2592000 # 30 days
if [ $? -ne 0 ]; then
    echo "⚠️ WARNING: SSL certificate expires within 30 days!" | mail -s "Security Alert: SSL Certificate Expiration" admin@your-domain.com
fi
```

## 🎯 **Security Best Practices Checklist**

### **Secret Storage**
- [ ] All secrets stored in dedicated secrets management system
- [ ] No secrets in source code or Docker images
- [ ] Secrets encrypted at rest and in transit
- [ ] Access controlled with proper IAM/RBAC
- [ ] Regular access auditing performed

### **Secret Access**
- [ ] Principle of least privilege applied
- [ ] Service accounts used instead of user accounts
- [ ] Multi-factor authentication enabled
- [ ] Access logging and monitoring active
- [ ] Regular access review conducted

### **Secret Rotation**
- [ ] Automated rotation procedures implemented
- [ ] Rotation schedule defined and followed
- [ ] Emergency rotation procedures documented
- [ ] Rotation testing performed regularly
- [ ] Zero-downtime rotation validated

### **Monitoring & Compliance**
- [ ] Secret access monitored and logged
- [ ] Expiration alerts configured
- [ ] Security scanning implemented
- [ ] Compliance reporting automated
- [ ] Incident response procedures defined

## 🚨 **Emergency Procedures**

### **Compromised Secret Response**

```bash
#!/bin/bash
# Emergency secret rotation script

echo "🚨 EMERGENCY: Rotating compromised secrets..."

# 1. Immediately rotate all secrets
./rotate-secrets.sh

# 2. Revoke compromised credentials
az keyvault secret set --vault-name clo-system-vault --name "postgres-password" --value "$(openssl rand -base64 32)" --disabled true

# 3. Update firewall rules
ufw deny from suspicious-ip

# 4. Force logout all users
redis-cli FLUSHDB  # Clear session cache

# 5. Restart all services with new secrets
docker-compose -f docker-compose.production.yml restart

# 6. Send security alert
echo "🚨 SECURITY INCIDENT: Secrets rotated due to potential compromise. System secured." | mail -s "SECURITY ALERT" security-team@your-domain.com

echo "Emergency rotation completed. Review logs and monitor for suspicious activity."
```

## 📚 **Documentation Requirements**

### **Security Documentation**
- **Secrets Inventory**: List of all secrets and their purposes
- **Access Control**: Who has access to which secrets
- **Rotation Schedule**: When and how secrets are rotated
- **Emergency Procedures**: Response to security incidents
- **Compliance Records**: Audit trails and compliance reports

**🔐 Remember: Security is not a destination, it's a journey. Regularly review and update your secrets management practices!**