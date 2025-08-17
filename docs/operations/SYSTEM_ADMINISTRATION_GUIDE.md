# CLO Management System - System Administration Guide

## 🔧 **System Administrator Overview**

This guide provides comprehensive instructions for administering the CLO Management System, including user management, system monitoring, maintenance procedures, and troubleshooting.

## 👥 **User Management**

### **User Roles and Permissions**

#### **System Administrator**
- **Full System Access**: Complete control over all system functions
- **User Management**: Create, modify, deactivate user accounts
- **System Configuration**: Modify system settings and parameters
- **Monitoring Access**: View system health, performance, and logs
- **Security Management**: Manage security settings and audit logs

#### **Portfolio Manager**
- **Portfolio Operations**: Create and manage CLO portfolios
- **Asset Management**: Add, modify, and analyze assets
- **Performance Analysis**: Access to performance metrics and analytics
- **Risk Management**: View risk reports and analysis

#### **Financial Analyst** 
- **Advanced Analytics**: Waterfall analysis and scenario modeling
- **Data Analysis**: Export and analyze portfolio data
- **Report Generation**: Create custom reports and analysis
- **Model Access**: Use financial models and calculations

#### **Viewer**
- **Read-Only Access**: View portfolios and reports
- **Report Access**: Access to standard reports only
- **Dashboard Viewing**: Monitor key metrics and summaries

### **User Account Management**

#### **Creating New Users**

1. **Access User Management**
   - Navigate to **Admin** → **User Management**
   - Click **+ Add New User**

2. **Enter User Information**
   ```
   Username: user@company.com
   Full Name: John Smith
   Role: Financial Analyst
   Department: Investment Management
   Manager: manager@company.com
   ```

3. **Set Permissions**
   - Select role-appropriate permissions
   - Configure portfolio access restrictions
   - Set data export permissions
   - Enable/disable specific features

4. **Account Security**
   - Set temporary password (user must change on first login)
   - Enable multi-factor authentication requirement
   - Set session timeout preferences
   - Configure password policy compliance

#### **Modifying User Accounts**

1. **Find User**: Use search or filter in User Management
2. **Edit Profile**: Modify basic information and contact details
3. **Update Permissions**: Change role or specific permissions
4. **Account Status**: Activate, deactivate, or suspend accounts
5. **Reset Password**: Generate temporary password for user

#### **Deactivating Users**

1. **Soft Deactivation**: Disable login but preserve data
   - User cannot log in
   - Historical data and audit trail preserved
   - Can be reactivated later

2. **Account Suspension**: Temporary restriction
   - Set suspension period
   - Automatic reactivation available
   - Notification to user and manager

3. **Complete Removal**: Permanent account deletion
   - ⚠️ **Warning**: Cannot be undone
   - Requires manager approval
   - Data anonymization procedures

### **Bulk User Operations**

#### **CSV User Import**
```csv
username,full_name,role,department,manager_email
analyst1@company.com,Jane Doe,Financial Analyst,Investment,manager@company.com
analyst2@company.com,Bob Smith,Portfolio Manager,Investment,manager@company.com
```

#### **User Export**
- Export user lists for compliance reporting
- Generate access control reports
- Create user activity summaries

## 🖥️ **System Monitoring**

### **Dashboard Overview**

The System Admin Dashboard provides real-time system status:

- **System Health**: Overall system status and component health
- **Performance Metrics**: CPU, memory, disk usage, and response times
- **Active Users**: Current logged-in users and session information  
- **Recent Activity**: User actions, system events, and alerts
- **Security Events**: Failed login attempts, permission changes, alerts

### **Health Monitoring**

#### **System Components**
- **API Server**: Application server status and response times
- **Database**: PostgreSQL connection status and performance
- **Cache**: Redis cache status and hit rates
- **QuantLib**: Financial calculation engine status
- **File Storage**: Storage system status and capacity

#### **Performance Metrics**
```
CPU Usage: 35% (Good)
Memory Usage: 2.1GB / 8GB (26%)
Disk Usage: 125GB / 500GB (25%)
Active Connections: 45
Average Response Time: 28ms
```

#### **Database Performance**
```
Connection Pool: 8/20 active connections
Query Performance: 15ms average
Slow Queries: 2 in last hour
Cache Hit Rate: 95%
```

### **Alerting and Notifications**

#### **Alert Categories**
- **System Health**: Component failures or degraded performance
- **Security**: Failed login attempts, permission changes
- **Performance**: High resource usage or slow response times  
- **Business**: Portfolio breaches, calculation errors
- **Maintenance**: Scheduled maintenance reminders

#### **Alert Configuration**
1. **Threshold Settings**
   - CPU usage > 80%
   - Memory usage > 90%
   - Disk usage > 85%
   - Response time > 500ms
   - Failed login attempts > 5

2. **Notification Methods**
   - Email notifications
   - Dashboard alerts
   - SMS for critical alerts
   - Webhook integrations

3. **Escalation Procedures**
   - Initial alert to system admin
   - Escalate to manager after 30 minutes
   - Page on-call team for critical issues

## 🔧 **System Configuration**

### **General Settings**

#### **System Parameters**
```
System Name: CLO Management System
Environment: Production
Time Zone: UTC
Default Language: English
Session Timeout: 60 minutes
Password Policy: Strong (min 12 chars, complex)
```

#### **Feature Flags**
- **Excel Integration**: Enable/disable VBA bridge
- **Real-time Updates**: WebSocket functionality
- **Advanced Analytics**: Monte Carlo simulations
- **API Documentation**: Interactive API explorer

#### **Performance Settings**
```
Max Concurrent Users: 100
Request Timeout: 30 seconds
File Upload Limit: 100MB
Calculation Timeout: 300 seconds
Report Generation Timeout: 600 seconds
```

### **Security Configuration**

#### **Authentication Settings**
- **Multi-Factor Authentication**: Required for all users
- **Session Management**: Concurrent session limits
- **Password Policy**: Complexity and rotation requirements
- **Account Lockout**: Failed login attempt policies

#### **Access Control**
- **IP Restrictions**: Whitelist company IP ranges
- **API Rate Limiting**: Prevent abuse and DoS attacks
- **Audit Logging**: Log all user actions and system events
- **Data Encryption**: Ensure all data encrypted at rest and in transit

### **Integration Configuration**

#### **External Systems**
- **Market Data Feeds**: Configure data providers
- **Email Services**: SMTP configuration for notifications
- **Cloud Storage**: Azure Blob Storage integration
- **Monitoring Tools**: Prometheus and Grafana setup

#### **API Configuration**
- **Rate Limiting**: Configure limits per user role
- **CORS Settings**: Configure allowed origins for web access
- **Webhook Endpoints**: Configure external system notifications

## 📊 **System Maintenance**

### **Scheduled Maintenance**

#### **Daily Maintenance** (Automated)
- **Database Backup**: Full backup at 2:00 AM UTC
- **Log Rotation**: Archive logs older than 30 days
- **Cache Cleanup**: Remove expired cache entries
- **Health Checks**: Automated system health validation

#### **Weekly Maintenance**
- **Security Updates**: Apply security patches during maintenance window
- **Performance Optimization**: Database maintenance and optimization
- **Capacity Planning**: Review resource usage and plan for growth
- **Backup Verification**: Test backup restoration procedures

#### **Monthly Maintenance**
- **User Access Review**: Review user permissions and access logs
- **Security Audit**: Comprehensive security assessment
- **Compliance Reporting**: Generate compliance and audit reports
- **System Performance Review**: Analyze trends and optimize

### **Backup and Recovery**

#### **Backup Strategy**
- **Database Backups**: Daily full backups, hourly transaction log backups
- **File Storage**: Daily file system backups
- **Configuration**: Weekly configuration and settings backups
- **Code Deployment**: Version-controlled deployment packages

#### **Recovery Procedures**
1. **Database Recovery**
   ```bash
   # Stop application
   docker-compose -f docker-compose.production.yml stop clo-api
   
   # Restore database
   pg_restore -h localhost -U postgres -d clo_production backup_file.sql
   
   # Restart application
   docker-compose -f docker-compose.production.yml start clo-api
   ```

2. **Full System Recovery**
   - Restore from cloud backup
   - Redeploy application containers
   - Verify system functionality
   - Notify users of restoration

#### **Disaster Recovery**
- **Recovery Time Objective (RTO)**: 4 hours maximum downtime
- **Recovery Point Objective (RPO)**: Maximum 1 hour data loss
- **Hot Standby**: Secondary system for critical operations
- **Communication Plan**: User notification procedures

## 🔍 **Monitoring and Logging**

### **Log Management**

#### **Log Categories**
- **Application Logs**: System events, errors, and user actions
- **Access Logs**: HTTP requests, API calls, authentication events
- **Security Logs**: Security events, failed attempts, permission changes
- **Database Logs**: Query performance, connection events, errors
- **System Logs**: OS events, resource usage, hardware status

#### **Log Analysis**
- **Real-time Monitoring**: Live log streaming and analysis
- **Error Tracking**: Automatic error detection and alerting
- **Performance Analysis**: Response time and resource usage trends
- **Security Analysis**: Anomaly detection and threat identification

### **Performance Monitoring**

#### **Key Performance Indicators**
- **System Availability**: 99.9% uptime target
- **Response Time**: <100ms API response time
- **Error Rate**: <0.1% application error rate
- **User Satisfaction**: Based on user feedback and usage metrics

#### **Monitoring Tools**
- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboard visualization and alerting
- **ELK Stack**: Log aggregation and analysis (optional)
- **Custom Dashboards**: Business-specific metrics and KPIs

## 🔐 **Security Administration**

### **Security Monitoring**

#### **Security Events**
- **Authentication Events**: Login attempts, password changes
- **Authorization Events**: Permission changes, access violations
- **Data Access Events**: Sensitive data access, exports
- **System Events**: Configuration changes, administrative actions

#### **Threat Detection**
- **Anomaly Detection**: Unusual user behavior patterns
- **Intrusion Detection**: Unauthorized access attempts
- **Data Loss Prevention**: Unauthorized data export attempts
- **Malware Detection**: File upload security scanning

### **Compliance Management**

#### **Regulatory Compliance**
- **SOX Compliance**: Financial data controls and audit trails
- **SEC Regulations**: Investment company compliance requirements
- **GDPR**: Data privacy and protection (if applicable)
- **Industry Standards**: Financial services regulatory compliance

#### **Audit Procedures**
- **User Access Audit**: Quarterly review of user permissions
- **Security Audit**: Annual security assessment and penetration testing
- **Compliance Reporting**: Automated compliance report generation
- **Incident Documentation**: Security incident tracking and resolution

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Performance Issues**
1. **Slow Response Times**
   - Check system resource usage
   - Review database query performance
   - Analyze network connectivity
   - Optimize application settings

2. **High Memory Usage**
   - Review application memory leaks
   - Analyze cache usage patterns
   - Consider scaling resources
   - Implement memory optimization

#### **Connectivity Issues**
1. **Database Connection Problems**
   ```bash
   # Test database connectivity
   psql -h database_host -U username -d database_name
   
   # Check connection pool
   docker logs clo-api-prod | grep "connection"
   ```

2. **Cache Connection Issues**
   ```bash
   # Test Redis connectivity
   redis-cli -h redis_host -p redis_port ping
   
   # Check cache performance
   redis-cli info stats
   ```

### **Emergency Procedures**

#### **System Outage Response**
1. **Immediate Response** (0-15 minutes)
   - Assess scope and impact
   - Activate incident response team
   - Implement emergency communications

2. **Investigation** (15-60 minutes)
   - Identify root cause
   - Implement temporary workarounds
   - Document findings and actions

3. **Resolution** (1-4 hours)
   - Implement permanent fix
   - Test system functionality
   - Monitor for stability

4. **Post-Incident** (24-48 hours)
   - Conduct post-mortem analysis
   - Update procedures and documentation
   - Implement preventive measures

## 📞 **Support and Escalation**

### **Support Tiers**

#### **Tier 1: System Administrator**
- Initial troubleshooting and issue resolution
- User account management and password resets
- Routine maintenance and monitoring
- Standard configuration changes

#### **Tier 2: Technical Support**
- Advanced troubleshooting and system analysis
- Performance optimization and tuning
- Complex configuration changes
- Integration and API issues

#### **Tier 3: Development Team**
- Application bugs and code issues
- New feature development
- System architecture changes
- Database schema modifications

### **Contact Information**

**System Administrator**: admin@your-domain.com  
**Technical Support**: support@your-domain.com  
**Emergency Contact**: +1-555-EMERGENCY  
**On-Call Rotation**: oncall@your-domain.com

### **Documentation and Resources**

- **System Documentation**: Internal wiki and documentation portal
- **Vendor Support**: Database, cloud provider, and third-party support
- **Knowledge Base**: Searchable database of solutions and procedures
- **Training Materials**: Administrator training and certification programs

---

**This comprehensive guide provides system administrators with all necessary information for effective management of the CLO Management System.**