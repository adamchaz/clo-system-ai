# 🧪 Backend Test Suite Organization

> ## 🛡️ Database isolation (`tests/conftest.py`)
>
> The suite always runs against a **separate test database**, never the dev database:
>
> - `tests/conftest.py` runs before any test module is imported. It takes the dev
>   `DATABASE_URL` (environment or `backend/.env.development`), swaps the database name to
>   `<name>_test` (`clo_dev` -> **`clo_dev_test`**), exports that as `DATABASE_URL`, creates the
>   database if needed, and verifies the application engine points at it.
> - Override with `TEST_DATABASE_URL=postgresql://...`. A test database name must contain
>   `test` and differ from the dev database; otherwise pytest exits before running anything.
> - The report header shows which database is used:
>   `database isolation: tests use 'clo_dev_test' ... (development database 'clo_dev' is not touched)`
> - `backend/pytest.ini` limits collection to `tests/`, so a bare `pytest` won't pick up the
>   scripts in `backend/debug/` or loose `test_*.py` files in `backend/`.
>
> Run from `backend/` with the venv active: `pytest` (or `pytest tests/test_utils` etc.).
> Docker's PostgreSQL must be running for the database tests.
>
> **Why:** six files use the application's real engine, and five of them
> (`test_fee_service.py`, `test_fee_waterfall_integration.py`, `test_ic_trigger.py`,
> `test_oc_trigger.py`, `test_trigger_integration.py`) run `Base.metadata.drop_all()` in
> teardown. Before this conftest existed, a full run on 2026-11-08 dropped every model table in
> `clo_dev`, which then had to be rebuilt from Excel (`docs/technical/DATA_MIGRATION_GUIDE.md`).
> Verified after adding it: a full run left every `clo_dev` row count unchanged.
>
> `clo_dev_test` starts empty and tests create/drop their own tables, so tests that expect the
> real portfolio data (`tests/integration/`) find nothing there. Those are script-style tests
> that return True/False instead of asserting, so pytest reports them as passing anyway.

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

**Last full run (2026-11-08, isolated database):** 667 tests collected - **478 passed,
81 failed, 108 errors**. These are genuine failures in the test code, not side effects of
the database: an identical result was produced before isolation existed. Main causes:
- integration tests pass arguments the models no longer accept (e.g. `analysis_date` to
  `CLODeal`) - most of the errors in `test_reinvestment_integration.py`,
  `test_incentive_fee_integration.py`, `test_rating_system_integration.py`
- SQLite-based tests that create only part of the schema (`no such table: clo_deals`) -
  `test_liability_model.py`
- waterfall configuration tests passing strings where lists are expected - `test_waterfall.py`,
  `test_waterfall_implementations.py`

Coverage has not been measured.

## 🔧 **Test Configuration**

### **pytest Configuration**
- Configuration file: `pytest.ini` (if present)
- Test discovery: Automatic for `test_*.py` files
- `tests/conftest.py` provides database isolation only (see top); each file sets up its own fixtures

### **Environment Variables**
No setup is needed: `tests/conftest.py` points the application at `clo_dev_test`
automatically. To use a different test database:
```bash
set TEST_DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5433/my_test_db
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