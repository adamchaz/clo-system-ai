# CLO Management System - User Guide

## 🎯 **Welcome to the CLO Management System**

The CLO Management System is a comprehensive platform for managing Collateralized Loan Obligation portfolios, converting sophisticated Excel/VBA calculations to a modern web application with real-time analytics and professional workflows.

## 👥 **User Roles and Access**

### **System Administrator**
- **Full System Access**: Complete control over users, system settings, and infrastructure
- **User Management**: Create, modify, and deactivate user accounts
- **System Monitoring**: Access to health metrics, performance data, and system logs
- **Configuration**: Manage system-wide settings and feature flags

### **Portfolio Manager** 
- **Portfolio Operations**: Create, edit, and manage CLO portfolios
- **Asset Management**: Add, modify, and analyze portfolio assets
- **Risk Analysis**: Access to risk metrics, VaR calculations, and stress testing
- **Performance Tracking**: Monitor portfolio performance and attribution analysis

### **Financial Analyst**
- **Advanced Analytics**: Access to waterfall analysis, scenario modeling, and correlation analysis
- **CLO Structuring**: Design and optimize CLO deal structures
- **Monte Carlo Simulations**: Run complex stress testing and scenario analysis
- **Data Analysis**: Export data and create custom analytical reports

### **Viewer**
- **Read-Only Access**: View portfolios, reports, and performance data
- **Report Access**: Access to standard reports and performance summaries
- **Dashboard Viewing**: Monitor key metrics and portfolio summaries

## 🚀 **Getting Started**

### **1. Logging In**

1. Navigate to the CLO Management System URL
2. Enter your username and password
3. Click "Sign In"
4. You'll be redirected to your role-specific dashboard

### **2. Understanding Your Dashboard**

Each user role has a customized dashboard with relevant information:

- **System Admin**: System health, user activity, alerts
- **Portfolio Manager**: Portfolio overview, recent activity, performance metrics
- **Financial Analyst**: Analytics tools, calculation status, model results  
- **Viewer**: Portfolio summaries, available reports, key metrics

### **3. Navigation**

Use the left sidebar to navigate between sections:
- **Dashboard**: Overview and key metrics
- **Portfolios**: Portfolio management and analysis
- **Assets**: Individual asset management
- **Analytics**: Advanced analysis tools
- **Reports**: Reporting and export functions
- **Admin** (if applicable): User and system management

## 📊 **Core Features**

### **Portfolio Management**

#### **Creating a New Portfolio**
1. Navigate to **Portfolios** → **Create New**
2. Fill in basic portfolio information:
   - Portfolio Name
   - Manager
   - Inception Date
   - Target Size
   - Currency
3. Configure portfolio settings:
   - Investment Strategy
   - Risk Parameters
   - Compliance Rules
4. Click **Create Portfolio**

#### **Managing Portfolio Assets**
1. Open a portfolio from the **Portfolios** list
2. Go to the **Assets** tab
3. **Add Asset**: Click **+ Add Asset** button
   - Select asset type (Loan, Bond, etc.)
   - Enter asset details (CUSIP, amount, rating, etc.)
   - Set asset-specific parameters
4. **Edit Asset**: Click the edit icon next to any asset
5. **Remove Asset**: Use the delete icon (requires confirmation)

#### **Portfolio Analysis**
1. **Performance Tab**: View portfolio performance metrics
   - Total return, IRR, MOIC
   - Performance attribution
   - Benchmark comparison
2. **Risk Tab**: Access risk analytics
   - Value at Risk (VaR)
   - Duration and convexity
   - Concentration analysis
3. **Cash Flow Tab**: Review cash flow projections
   - Payment waterfalls
   - Principal and interest forecasts
   - Reinvestment scenarios

### **Asset Management**

#### **Asset Details**
Each asset contains comprehensive information:
- **Basic Information**: CUSIP, issuer, rating, maturity
- **Financial Details**: Principal amount, coupon, spread
- **Risk Metrics**: Duration, rating migration probability
- **Performance Data**: Price history, payment history
- **Documentation**: Loan agreements, amendments

#### **Asset Analysis**
- **Credit Analysis**: Rating history, credit events, migration analysis
- **Performance Tracking**: Payment performance, default probability
- **Correlation Analysis**: Asset correlation with portfolio
- **Scenario Analysis**: Stress testing individual assets

### **Advanced Analytics**

#### **Waterfall Analysis**
1. Navigate to **Analytics** → **Waterfall Analysis**
2. Select portfolio and analysis date
3. Choose waterfall methodology (MAG 6-17 available)
4. Run calculation to see:
   - Payment priorities and sequences
   - Interest and principal distributions
   - Equity distributions and clawback calculations
   - Performance fee calculations

#### **Scenario Modeling**
1. Go to **Analytics** → **Scenario Modeling**
2. Define scenario parameters:
   - Interest rate scenarios
   - Default rate assumptions
   - Recovery rate assumptions
   - Prepayment speed assumptions
3. Run Monte Carlo simulations
4. Review results:
   - Distribution of outcomes
   - Key metrics (IRR, MOIC, default rates)
   - Sensitivity analysis

#### **Correlation Analysis**
1. Access **Analytics** → **Correlation Analysis**
2. Select assets or portfolios for analysis
3. Choose correlation methodology
4. View correlation matrices and heatmaps
5. Analyze sector, geography, and rating correlations

### **Reporting**

#### **Standard Reports**
- **Portfolio Summary**: Key metrics and performance overview
- **Asset Detail Report**: Complete asset listing with key metrics
- **Performance Report**: Historical performance analysis
- **Risk Report**: Comprehensive risk metrics and analysis
- **Cash Flow Report**: Projected cash flows and waterfall analysis

#### **Custom Reports**
1. Navigate to **Reports** → **Report Builder**
2. Select report template or create custom
3. Choose data fields and filters
4. Set formatting and output options
5. Generate report (PDF, Excel, or CSV)

#### **Scheduled Reports**
1. Go to **Reports** → **Scheduled Reports**
2. Choose report type and parameters
3. Set schedule (daily, weekly, monthly)
4. Configure email distribution list
5. Save schedule

## 🔧 **Advanced Features**

### **Real-Time Data**

The system provides real-time updates through WebSocket connections:
- **Portfolio Values**: Live portfolio valuations
- **Calculation Status**: Real-time progress of complex calculations
- **Notifications**: System alerts and important updates
- **Market Data**: Live market data feeds (when configured)

### **Data Export**

Multiple export formats are available:
- **Excel**: Full formatting with charts and calculations
- **CSV**: Raw data for further analysis
- **PDF**: Professional reports with formatting
- **JSON**: API-compatible data format

### **Calculation Engine**

The system uses QuantLib for advanced financial calculations:
- **Yield Curve Analysis**: Interest rate calculations
- **Option Pricing**: Embedded option valuations
- **Risk Metrics**: VaR, duration, convexity calculations
- **Monte Carlo Simulations**: Complex scenario analysis

## 🎨 **User Interface Features**

### **Dashboard Customization**
- **Widget Layout**: Drag and drop dashboard widgets
- **Theme Selection**: Choose from multiple color themes
- **Chart Preferences**: Customize chart types and data displays
- **Quick Actions**: Set up frequently used actions

### **Keyboard Shortcuts**
- **Ctrl+K**: Open command palette for quick navigation
- **Ctrl+S**: Save current work
- **Ctrl+E**: Quick export of current view
- **Ctrl+F**: Search within current page
- **Ctrl+H**: Open help documentation

### **Data Tables**
- **Sorting**: Click column headers to sort data
- **Filtering**: Use column filters to narrow data
- **Search**: Global search across all visible data
- **Pagination**: Navigate through large datasets
- **Column Customization**: Show/hide columns as needed

## 🔍 **Searching and Filtering**

### **Global Search**
Use the search bar at the top of the application:
- Search across portfolios, assets, and reports
- Use filters to narrow search results
- Save frequently used searches

### **Advanced Filters**
Most data tables support advanced filtering:
- **Date Range**: Filter by date ranges
- **Numeric Range**: Filter by value ranges
- **Multiple Selection**: Select multiple values
- **Text Search**: Partial text matching

## 📱 **Mobile Access**

The system is optimized for mobile devices:
- **Responsive Design**: Adapts to all screen sizes
- **Touch Navigation**: Optimized for touch interfaces
- **Mobile Dashboards**: Simplified mobile views
- **Offline Capability**: Basic functionality when offline

## ❓ **Getting Help**

### **In-Application Help**
- **Tooltips**: Hover over any element for quick help
- **Help Icons**: Click ? icons for contextual help
- **Command Palette**: Press Ctrl+K for quick help search

### **Support Resources**
- **User Guide**: This comprehensive guide
- **Video Tutorials**: Step-by-step video walkthroughs
- **FAQ**: Frequently asked questions
- **Technical Support**: Contact information for technical issues

### **Training Materials**
- **Getting Started Tutorial**: Interactive system tour
- **Role-Specific Training**: Training materials for each user role  
- **Advanced Features Guide**: Deep-dive into complex features
- **Best Practices**: Recommended workflows and procedures

## 🚨 **Important Notes**

### **Data Security**
- **Access Control**: Access is restricted based on your user role
- **Audit Trail**: All actions are logged for compliance
- **Data Encryption**: All data is encrypted in transit and at rest
- **Session Management**: Sessions timeout for security

### **Performance Tips**
- **Large Datasets**: Use filters to limit large data displays
- **Complex Calculations**: Allow time for Monte Carlo simulations
- **Browser Performance**: Close unused tabs to maintain performance
- **Cache Management**: Refresh browser if data appears stale

### **System Maintenance**
- **Scheduled Downtime**: Check system status for maintenance windows
- **Backup Schedule**: System backups occur daily during off-hours
- **Update Notifications**: You'll be notified of system updates
- **Data Retention**: Historical data is retained per company policy

## 📞 **Support and Contact**

**Technical Support**: [Insert contact information]  
**User Training**: [Insert training contact]  
**System Admin**: [Insert admin contact]

**System Status**: Check system health at [monitoring URL]  
**Documentation**: Additional documentation at [docs URL]

---

**Welcome to the CLO Management System! This guide will help you make the most of the platform's powerful features for managing your CLO portfolios effectively.**