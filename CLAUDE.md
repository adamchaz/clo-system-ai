# CLO Management System

A comprehensive Collateralized Loan Obligation (CLO) Portfolio Management System converting from Excel/VBA to a modern Python web application.

## Project Overview

This is a **HIGH COMPLEXITY** financial technology project modernizing a sophisticated CLO portfolio management system from Excel/VBA (TradeHypoPrelimv32.xlsm) to a scalable Python web application.

### Legacy System Analysis
- **VBA Codebase**: 69 modules with 15,000+ lines of professional financial logic
- **Core Classes**: 32 sophisticated business classes (CLODeal, Asset, Waterfall engines)
- **Excel Integration**: 20 worksheets with 17,622+ complex formulas
- **Business Logic**: Object-oriented architecture with Strategy Pattern implementation

### Tech Stack
- **Backend**: Python FastAPI with SQLAlchemy + QuantLib for financial calculations
- **Frontend**: React TypeScript with Material-UI + Recharts for financial visualizations
- **Database**: PostgreSQL + Redis for caching correlation matrices
- **Infrastructure**: Docker containerization + async processing (Celery)

### Key Features Identified from VBA Analysis
- **Cash Flow Waterfall Engine**: 9 different magnitude implementations (Mag 6-17)
- **Asset Management**: 1,004 assets with 70+ properties each (Asset.cls - 1,217 lines)
- **Portfolio Optimization**: Advanced algorithms with 91 compliance constraints
- **Hypothesis Testing**: Complex scenario analysis and Monte Carlo simulations
- **Credit Risk Modeling**: Rating migration and correlation analysis (489×489 matrix)
- **PIK Payment Support**: Payment-in-kind instruments with complex accrual logic
- **Regulatory Compliance**: Comprehensive OC/IC trigger testing framework

## Development Commands

### Frontend (React TypeScript)
```bash
cd frontend
npm start      # Development server
npm run build  # Production build
npm test       # Run tests
```

### Backend (Python FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload  # Development server
```

### Docker Services
```bash
cd infrastructure/docker
docker-compose up -d    # Start databases
docker-compose down     # Stop services
```

### Development Scripts
```bash
scripts\start-dev.bat   # Start full development environment
scripts\stop-dev.bat    # Stop development environment
```

## Project Structure

- `backend/` - Python FastAPI application
- `frontend/` - React TypeScript application  
- `infrastructure/` - Docker and deployment configs
- `scripts/` - Development automation scripts
- `data/` - Data files (gitignored)
- `docs/` - Documentation
- `vba_extracted/` - Extracted VBA source code (69 modules)
  - `classes/` - 32 business logic classes
  - `modules/` - 16 calculation and utility modules
  - `forms/` - 2 user interface forms
  - `sheets/` - 15 worksheet event handlers

## Analysis Documentation

- `CLO_Analysis_Report.md` - Comprehensive 11-section technical analysis
- `VBA_ANALYSIS_SUPPLEMENT.md` - Detailed VBA code breakdown and conversion strategy
- `TradeHypoPrelimv32.xlsm` - Legacy Excel system (3.11 MB with complex business logic)

## Security Notes

This system handles sensitive financial data:
- All Excel files, databases, and credentials are excluded from Git
- Use environment variables for sensitive configuration
- Follow secure coding practices for financial data

## Current Status

**ANALYSIS COMPLETE** - Comprehensive VBA code analysis and Python conversion planning finished.

### Conversion Roadmap (20-28 weeks, HIGH complexity)

#### **Phase 1: Data Architecture (4-6 weeks)**
- Database schema design for 1,004 assets with 70+ properties
- Migration scripts for Excel data to PostgreSQL
- SQLAlchemy ORM models for core business entities

#### **Phase 2: VBA Business Logic Migration (10-14 weeks)**
- **CLODeal.cls** (1,100 lines) → Master orchestration class
- **Asset.cls** (1,217 lines) → Comprehensive asset modeling  
- **9 Waterfall Classes** → Strategy pattern for cash flow calculations
- **Main.bas** (1,176 lines) → Portfolio optimization algorithms
- **91 Compliance Tests** → Regulatory validation framework

#### **Phase 3: API & Integration (4-6 weeks)**  
- FastAPI endpoints for all business operations
- QuantLib integration for financial calculations
- Async processing for heavy computations

#### **Phase 4: User Interface (6-8 weeks)**
- React dashboard with financial visualizations
- Waterfall calculation results display
- Portfolio management interface

### Key Technical Challenges
- **Excel Function Translation**: YearFrac, Yield calculations → QuantLib equivalents
- **VBA Array Operations** → NumPy vectorized operations  
- **Complex Waterfall Logic**: 9 different payment sequences with PIK support
- **Performance**: 500,000+ data points with correlation matrices
- **Financial Accuracy**: Validation against existing Excel calculations

### Next Steps
1. **Team Assembly**: 5-7 developers with CLO domain expertise
2. **Environment Setup**: Development infrastructure and tools
3. **Proof of Concept**: Core Asset class conversion validation
4. **Iterative Development**: Phase-by-phase conversion with testing