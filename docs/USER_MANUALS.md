# CLO Management System - User Manuals

## Table of Contents

1. [System Administrator Manual](#system-administrator-manual)
2. [Portfolio Manager Manual](#portfolio-manager-manual)
3. [Financial Analyst Manual](#financial-analyst-manual)
4. [Viewer Manual](#viewer-manual)
5. [Common Operations](#common-operations)
6. [Troubleshooting](#troubleshooting)

---

## System Administrator Manual

### Overview
As a System Administrator, you have full access to all system functions including user management, system configuration, data migration, and monitoring.

### Key Responsibilities
- User account management and access control
- System monitoring and performance optimization
- Data backup and migration operations
- Security configuration and compliance

### Core Functions

#### User Management
- **Create Users**: Add new users with appropriate roles
- **Manage Permissions**: Assign and modify user roles (Admin, Manager, Analyst, Viewer)
- **Monitor Sessions**: Track active user sessions and security events
- **Password Resets**: Handle password reset requests

#### System Monitoring
- **Health Dashboard**: Monitor system uptime, performance metrics, and service status
- **Database Management**: Monitor PostgreSQL and Redis performance
- **Alert Management**: Configure and respond to system alerts
- **Audit Logs**: Review system access and operation logs

#### Data Operations
- **Migration Management**: Execute and monitor data migrations from Excel
- **Backup Procedures**: Schedule and verify data backups
- **Data Validation**: Ensure data integrity across migrations
- **Cache Management**: Clear and optimize Redis cache

### Daily Operations

#### Morning Checklist
1. Check system health dashboard
2. Review overnight alerts and logs
3. Verify backup completion
4. Monitor database performance metrics

#### Weekly Tasks
1. Generate system performance reports
2. Review user access patterns
3. Update system documentation
4. Plan maintenance windows

### API Endpoints (Admin Access)

#### User Management
```
POST /api/v1/auth/users          # Create user
PUT /api/v1/auth/users/{id}      # Update user
GET /api/v1/auth/users           # List users
DELETE /api/v1/auth/users/{id}   # Deactivate user
```

#### System Monitoring
```
GET /api/v1/monitoring/health           # System health
GET /api/v1/monitoring/performance      # Performance metrics
GET /api/v1/monitoring/alerts          # System alerts
GET /api/v1/monitoring/audit-logs      # Audit trail
```

#### Data Management
```
GET /api/v1/monitoring/database-stats   # Database statistics
POST /api/v1/monitoring/cache/clear    # Clear cache
GET /api/v1/monitoring/resources       # System resources
```

---

## Portfolio Manager Manual

### Overview
As a Portfolio Manager, you manage CLO portfolios, execute waterfall calculations, and oversee risk management operations.

### Key Responsibilities
- Portfolio creation and management
- Waterfall calculation oversight
- Risk assessment and reporting
- Scenario analysis and stress testing

### Core Functions

#### Portfolio Management
- **Create Portfolios**: Set up new CLO deals with complete asset allocation
- **Manage Assets**: Add, remove, and modify assets within portfolios
- **Track Performance**: Monitor portfolio performance metrics and trends
- **Generate Reports**: Create comprehensive portfolio reports

#### Waterfall Operations
- **Calculate Waterfalls**: Execute payment waterfalls for CLO structures
- **Review Results**: Analyze waterfall outputs and payment priorities
- **Scenario Testing**: Run stress tests and scenario analyses
- **Export Reports**: Generate waterfall reports for stakeholders

#### Risk Management
- **Correlation Analysis**: Review asset correlation matrices
- **Risk Metrics**: Calculate VaR, expected shortfall, and concentration risk
- **Stress Testing**: Execute stress scenarios and analyze results
- **Compliance Monitoring**: Ensure portfolio compliance with deal documents

### Workflow Examples

#### Daily Portfolio Review
1. Access portfolio dashboard
2. Review overnight performance metrics
3. Check for rating changes or defaults
4. Update portfolio parameters if needed
5. Generate daily performance report

#### Monthly Waterfall Process
1. Update asset data and market conditions
2. Execute waterfall calculations
3. Review payment distributions
4. Validate results against expectations
5. Export reports for distribution

### API Endpoints (Manager Access)

#### Portfolio Operations
```
GET /api/v1/portfolios                    # List portfolios
POST /api/v1/portfolios                   # Create portfolio
GET /api/v1/portfolios/{id}              # Get portfolio details
PUT /api/v1/portfolios/{id}              # Update portfolio
```

#### Waterfall Calculations
```
POST /api/v1/waterfall/calculate/{portfolio_id}  # Calculate waterfall
GET /api/v1/waterfall/results/{calculation_id}   # Get results
GET /api/v1/waterfall/history/{portfolio_id}     # Calculation history
```

#### Risk Analytics
```
GET /api/v1/risk/portfolio/{id}/var             # Portfolio VaR
GET /api/v1/risk/portfolio/{id}/concentration   # Concentration analysis
GET /api/v1/risk/correlations                   # Correlation matrix
POST /api/v1/risk/stress-test/{portfolio_id}    # Stress testing
```

---

## Financial Analyst Manual

### Overview
As a Financial Analyst, you perform detailed analysis, generate reports, and support investment decision-making through data analysis and modeling.

### Key Responsibilities
- Asset analysis and valuation
- Performance reporting
- Scenario modeling
- Data analysis and research

### Core Functions

#### Asset Analysis
- **Asset Research**: Analyze individual asset performance and characteristics
- **Valuation Models**: Build and maintain asset valuation models
- **Rating Analysis**: Monitor credit ratings and rating migration
- **Industry Analysis**: Sector and industry-level analysis

#### Reporting & Analytics
- **Performance Reports**: Generate detailed portfolio performance reports
- **Risk Reports**: Create risk analytics and compliance reports
- **Comparative Analysis**: Benchmark performance against peers
- **Trend Analysis**: Identify and report on market trends

#### Scenario Modeling
- **MAG Scenarios**: Utilize Moody's MAG scenarios for analysis
- **Custom Scenarios**: Create and run custom stress scenarios
- **Sensitivity Analysis**: Analyze sensitivity to key parameters
- **Monte Carlo**: Execute Monte Carlo simulations

### Key Workflows

#### Asset Analysis Process
1. Select assets for analysis
2. Gather historical performance data
3. Apply valuation models
4. Generate analysis reports
5. Document findings and recommendations

#### Monthly Reporting
1. Compile portfolio performance data
2. Calculate performance metrics
3. Create visualization charts
4. Generate executive summary
5. Distribute reports to stakeholders

### API Endpoints (Analyst Access)

#### Asset Analytics
```
GET /api/v1/assets                       # List assets
GET /api/v1/assets/{id}                  # Asset details
GET /api/v1/assets/{id}/performance      # Performance history
GET /api/v1/assets/{id}/correlations     # Asset correlations
```

#### Scenarios
```
GET /api/v1/scenarios                    # List scenarios
GET /api/v1/scenarios/{id}              # Scenario details
POST /api/v1/scenarios/analyze          # Run scenario analysis
GET /api/v1/scenarios/results/{id}      # Analysis results
```

#### Reporting
```
GET /api/v1/portfolios/{id}/performance  # Portfolio performance
GET /api/v1/risk/portfolio/{id}/metrics  # Risk metrics
GET /api/v1/monitoring/api-metrics      # System usage metrics
```

---

## Viewer Manual

### Overview
As a Viewer, you have read-only access to view portfolios, reports, and analytics without the ability to modify data or execute calculations.

### Key Responsibilities
- Portfolio monitoring
- Report review
- Data analysis
- Research support

### Available Functions

#### Portfolio Viewing
- **Portfolio Overview**: View portfolio composition and key metrics
- **Asset Details**: Review individual asset information
- **Performance Metrics**: View historical performance data
- **Risk Metrics**: Access risk analytics and reports

#### Report Access
- **Waterfall Reports**: View waterfall calculation results
- **Risk Reports**: Access risk analysis reports
- **Performance Reports**: Review portfolio performance reports
- **System Reports**: View system health and usage reports

### Navigation Guide

#### Dashboard Access
1. Log in to the system
2. Navigate to portfolio dashboard
3. Select portfolio to view
4. Review key metrics and charts

#### Report Generation
1. Access reports section
2. Select report type
3. Choose time period
4. Download or view online

### API Endpoints (Viewer Access)

```
GET /api/v1/portfolios                   # List portfolios (read-only)
GET /api/v1/portfolios/{id}             # Portfolio details
GET /api/v1/assets/{id}                 # Asset information
GET /api/v1/waterfall/results/{id}      # View waterfall results
GET /api/v1/risk/portfolio/{id}         # Risk metrics
GET /api/v1/scenarios/{id}              # Scenario results
```

---

## Common Operations

### Authentication
All users must authenticate using email and password. JWT tokens are used for session management.

#### Login Process
1. Navigate to login page
2. Enter email and password
3. Click "Login" button
4. System redirects to dashboard upon success

#### Password Reset
1. Click "Forgot Password" on login page
2. Enter email address
3. Check email for reset link
4. Click link and set new password

### Navigation
The system uses a sidebar navigation with sections for:
- Dashboard
- Portfolios
- Assets
- Risk Analytics
- Scenarios
- Reports
- System Monitoring (Admin only)

### Data Export
Most reports and data views include export options:
- **Excel**: Download as .xlsx file
- **PDF**: Generate PDF report
- **CSV**: Export raw data

### Search and Filtering
- Use search boxes to find specific assets or portfolios
- Apply filters by date range, asset type, rating, etc.
- Save common filter combinations

---

## Troubleshooting

### Common Issues

#### Login Problems
- **Issue**: "Invalid credentials" error
- **Solution**: Verify email/password, contact admin for password reset

#### Slow Performance
- **Issue**: Pages loading slowly
- **Solution**: Check system status, clear browser cache, contact admin if persistent

#### Data Not Loading
- **Issue**: Empty or missing data
- **Solution**: Refresh page, check network connection, verify permissions

#### Export Failures
- **Issue**: Reports fail to download
- **Solution**: Try smaller date ranges, check browser pop-up settings

### Getting Help

#### Contact Information
- **Technical Support**: support@clo-system.com
- **System Administrator**: admin@clo-system.com
- **Emergency Contact**: +1-555-0123

#### Self-Help Resources
- System documentation in `/docs` folder
- API documentation at `/api/docs`
- Training videos in company portal
- FAQ section in help menu

### Error Codes

#### Authentication Errors
- **401**: Unauthorized - login required
- **403**: Forbidden - insufficient permissions

#### Data Errors
- **404**: Resource not found
- **422**: Invalid data format
- **500**: Internal server error - contact admin

### Browser Requirements
- Chrome 80+ (recommended)
- Firefox 75+
- Safari 13+
- Edge 80+

Enable JavaScript and cookies for full functionality.