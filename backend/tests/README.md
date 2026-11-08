# 🧪 Backend Test Suite Organization

> ## ⛔ DO NOT RUN THE FULL SUITE AGAINST YOUR DEV DATABASE
>
> These files import the application's real `engine` / `SessionLocal` from
> `app.core.database`, which connects to whatever `DATABASE_URL` points at (by default the
> local dev database `clo_dev`):
>
> - `test_fee_service.py`, `test_fee_waterfall_integration.py`, `test_ic_trigger.py`,
>   `test_oc_trigger.py`, `test_trigger_integration.py` - these run
>   **`Base.metadata.drop_all()`** in teardown, which **drops every model table**
>   (users, deals, assets, positions, tranches, thresholds, ...)
> - `test_fee_calculator.py` - writes to the same database
>
> On 2026-11-08 a full `pytest tests` run wiped `clo_dev` this way. It was rebuilt from Excel
> with `scripts/rebuild_dev_db_from_excel.py` (see `docs/technical/DATA_MIGRATION_GUIDE.md`).
>
> There is **no `conftest.py`** isolating the database yet. Until one exists:
> - only run tests that don't touch the database (e.g. `pytest tests/test_utils`), or
> - point `DATABASE_URL` at a disposable database first, e.g.
>   `set DATABASE_URL=postgresql://postgres:<pw>@127.0.0.1:5433/clo_test`, and
> - take a backup before any database-touching run:
>   `docker exec clo-postgres pg_dump -U postgres -d clo_dev -Fc > data/db_backups/clo_dev_<date>.dump`
>
> The other ~21 database-using test files create their own in-memory SQLite engines and are safe.

## 📂 **Test Directory Structure**

```
backend/tests/
├── README.md                           # This file
├── environment/                        # Environment & Setup Tests
│   ├── test_db_connection.py          # Database connectivity tests
│   ├── test_environment.py            # Environment configuration tests
│   ├── test_environment_simple.py     # Basic environment validation
│   ├── test_quantlib.py               # QuantLib library integration tests
│   └── quantlib_essentials_test.py    # QuantLib essentials validation
├── integration/                        # Integration Tests
│   ├── test_postgresql_migration.py   # PostgreSQL migration integration tests
│   └── test_mag17_api.py              # MAG17 API integration tests
├── test_utils/                        # Utility Test Modules
│   ├── __init__.py
│   ├── test_date_utils.py             # Date utility function tests
│   ├── test_financial_utils.py        # Financial calculation tests
│   ├── test_math_utils.py             # Mathematical utility tests
│   ├── test_matrix_utils.py           # Matrix operation tests
│   └── test_string_utils.py           # String utility tests
└── [Business Logic Tests]              # Core business logic tests
    ├── test_accounts.py               # Account management tests
    ├── test_asset_model.py            # Asset model tests
    ├── test_clo_deal_engine.py        # CLO deal engine tests
    ├── test_collateral_pool.py        # Collateral pool tests
    ├── test_concentration_test_enhanced.py # Concentration testing
    ├── test_credit_migration.py       # Credit migration tests
    ├── test_dynamic_waterfall.py      # Dynamic waterfall tests
    ├── test_fee_calculator.py         # Fee calculation tests
    ├── test_incentive_fee.py          # Incentive fee tests
    ├── test_liability_model.py        # Liability model tests
    ├── test_mag_waterfall.py          # MAG waterfall tests
    ├── test_portfolio_optimization.py # Portfolio optimization tests
    ├── test_rating_system.py          # Rating system tests
    ├── test_rebalancing.py            # Rebalancing algorithm tests
    ├── test_reinvestment.py           # Reinvestment logic tests
    ├── test_waterfall.py              # Waterfall engine tests
    └── test_yield_curve.py            # Yield curve tests
```

## 🎯 **Test Categories**

### **Environment Tests** (`environment/`)
- **Purpose**: Validate system setup and environment configuration
- **Scope**: Database connections, library installations, configuration validation
- **Run Frequency**: Before deployment, environment changes

### **Integration Tests** (`integration/`)
- **Purpose**: Test system component integration and end-to-end workflows
- **Scope**: API endpoints, database migrations, cross-component interactions
- **Run Frequency**: CI/CD pipeline, before releases

### **Business Logic Tests** (Root Level)
- **Purpose**: Validate core financial calculations and business rules
- **Scope**: VBA conversion validation, financial accuracy, algorithm correctness
- **Run Frequency**: Every commit, continuous integration

### **Utility Tests** (`test_utils/`)
- **Purpose**: Test utility functions and helper modules
- **Scope**: Mathematical functions, string operations, date calculations
- **Run Frequency**: With business logic tests

## 🚀 **Running Tests**

### **All Tests**
```bash
cd backend
python -m pytest tests/ -v
```

### **By Category**
```bash
# Environment tests only
python -m pytest tests/environment/ -v

# Integration tests only  
python -m pytest tests/integration/ -v

# Business logic tests only
python -m pytest tests/test_*.py -v

# Utility tests only
python -m pytest tests/test_utils/ -v
```

### **Specific Test Files**
```bash
# Single test file
python -m pytest tests/test_clo_deal_engine.py -v

# Specific test function
python -m pytest tests/test_mag_waterfall.py::test_mag17_waterfall -v
```

## 📊 **Test Coverage**

**Last full run (2026-11-08):** 667 tests collected - **478 passed, 81 failed, 108 errors**.
Treat these numbers as approximate: that run dropped the dev database tables part-way
through (see the warning at the top), which likely caused some of the failures. Re-measure
once the suite runs against an isolated database. Coverage has not been measured.

## 🔧 **Test Configuration**

### **pytest Configuration**
- Configuration file: `pytest.ini` (if present)
- Test discovery: Automatic for `test_*.py` files
- Fixtures: there is currently **no** `conftest.py`; each file sets up its own fixtures

### **Environment Variables**
Tests that use the application engine connect to `DATABASE_URL`. Always set it to a
disposable database before running them:
```bash
set DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5433/clo_test
set REDIS_URL=redis://127.0.0.1:6379
```

## 📝 **Adding New Tests**

### **Environment Tests**
- Place in `tests/environment/`
- Focus on system setup and configuration validation
- Use descriptive names: `test_database_connectivity.py`

### **Integration Tests**
- Place in `tests/integration/`
- Test component interactions and API endpoints
- Include end-to-end workflow validation

### **Business Logic Tests**
- Place in root `tests/` directory
- Focus on financial calculations and business rules
- Maintain VBA conversion parity validation

## 🎯 **Test Quality Standards**

### **Test Naming**
- Files: `test_[module_name].py`
- Functions: `test_[specific_functionality]()`
- Classes: `Test[ModuleName]`

### **Test Structure**
```python
def test_specific_functionality():
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_result
    assert validate_side_effects()
```

### **Documentation**
- Include docstrings for complex test cases
- Document test data requirements
- Explain business rule validation logic

---

**Status**: 🧪 **ORGANIZED - READY FOR SYSTEMATIC TESTING**  
**Coverage**: 1,100+ tests across all categories with 96% average coverage