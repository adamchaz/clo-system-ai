# CLO Management System

A comprehensive **Collateralized Loan Obligation (CLO) Portfolio Management System** converting from Excel/VBA to a modern Python web application.

## 🏗️ Architecture Overview

- **Backend**: Python FastAPI with SQLAlchemy
- **Frontend**: React TypeScript with Material-UI  
- **Database**: PostgreSQL + Redis
- **Infrastructure**: Docker containerization
- **Legacy System**: Excel VBA (TradeHypoPrelimv32.xlsm)

## 🎯 System Capabilities

### **Portfolio Management**
- Multi-deal CLO management (Mag 6-17 series)
- ~1,000 asset universe with BlackRock IDs
- Real-time portfolio rebalancing
- Asset correlation and concentration analysis

### **Trading & Hypothesis Testing**
- Buy/sell scenario analysis
- Portfolio optimization with ranking algorithms
- Individual asset vs. pool analysis
- Price and transaction modeling

### **Risk & Compliance**
- 10+ CLO-specific compliance tests
- Senior secured loan limitations
- Obligor concentration limits  
- Credit rating constraints
- Quality test monitoring

### **Advanced Analytics**
- Credit migration modeling
- Cash flow projections
- Payment waterfall calculations
- Stress testing scenarios

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Administrator privileges
- 5GB free disk space

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/clo-management-system.git
cd clo-management-system

# Start development environment
scripts\start-dev.bat

# Access applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000  
# API Docs: http://localhost:8000/docs
```

### Docker Services
```bash
# Start databases
cd infrastructure/docker
docker-compose up -d

# Stop services  
docker-compose down
```

## 📁 Project Structure

```
clo-management-system/
├── backend/                 # Python FastAPI application
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Core business logic
│   │   ├── models/         # SQLAlchemy models
│   │   └── services/       # Business services
│   └── requirements.txt
├── frontend/               # React TypeScript application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Application pages  
│   │   └── services/       # API services
│   └── package.json
├── infrastructure/         # Infrastructure as code
│   ├── docker/            # Docker configurations
│   └── azure/             # Azure deployment
├── scripts/               # Development scripts
├── data/                  # Data files (gitignored)
└── docs/                  # Documentation
```

## 🔄 VBA Conversion Progress

### ✅ Completed
- [x] Development environment setup
- [x] Project structure creation
- [x] VBA code analysis
- [x] Database schema design

### 🚧 In Progress  
- [ ] Asset model conversion (Asset.cls → Python)
- [ ] Hypothesis testing engine
- [ ] Compliance testing framework
- [ ] Portfolio optimization algorithms

### 📋 Planned
- [ ] Credit migration modeling
- [ ] Cash flow engine
- [ ] Web interface development
- [ ] API integration
- [ ] Reporting system
- [ ] Production deployment

## 🔒 Security & Compliance

This system handles sensitive financial data:

- **Data Protection**: All Excel files, databases, and credentials are excluded from Git
- **Access Control**: Private repository with branch protection
- **Audit Trail**: Comprehensive Git history for all changes
- **Environment Separation**: Development, staging, and production environments

## 🛠️ Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push and create pull request
git push origin feature/new-feature
```

## 📊 Technology Stack

### **Backend Technologies**
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing
- **SciPy**: Scientific computing
- **CVXPY**: Convex optimization

### **Frontend Technologies** 
- **React**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Material-UI**: Component library
- **Recharts**: Data visualization
- **React Query**: State management

### **Infrastructure**
- **PostgreSQL**: Primary database
- **Redis**: Caching and sessions
- **Docker**: Containerization
- **Azure**: Cloud platform

## 📈 Performance Optimization

- **Database Indexing**: Optimized for CLO queries
- **Caching Strategy**: Redis for frequent calculations
- **Async Processing**: Background task queue
- **Real-time Updates**: WebSocket integration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)  
5. Open Pull Request

## 📝 License

This project is proprietary software for CLO portfolio management.

## 📞 Support

For questions about CLO modeling or system usage, please open an issue or contact the development team.

---

**⚠️ Important**: This system processes sensitive financial data. Ensure all security protocols are followed during development and deployment.