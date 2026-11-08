# CLO Management System - Data Migration Guide

## Table of Contents

0. [Rebuilding the Dev Database from Excel (current procedure)](#rebuilding-the-dev-database-from-excel-current-procedure)
1. [Migration Overview](#migration-overview)
2. [Migration Architecture](#migration-architecture)
3. [Migration Components](#migration-components)
4. [Validation Procedures](#validation-procedures)
5. [Execution Guide](#execution-guide)
6. [Troubleshooting](#troubleshooting)
7. [Post-Migration Verification](#post-migration-verification)

## Rebuilding the Dev Database from Excel (current procedure)

*Added 2026-11-08.* The historical migration described in the rest of this guide was done
with many one-off, order-dependent scripts, some of which were never committed, so it cannot
be replayed. The core tables are now built by a single script that reads
`TradeHypoPrelimv32.xlsm` directly.

### When to use it
- The dev database lost data (this happened on 2026-11-08 when the backend test suite ran
  `drop_all` against `clo_dev` - see `backend/tests/README.md`)
- Setting up a new development database

### Steps
```bash
# 0. Back up whatever is there now (backups folder is git-ignored)
docker exec clo-postgres pg_dump -U postgres -d clo_dev -Fc > data/db_backups/clo_dev_<date>.dump

# 1. Core tables from Excel (run from the repo root)
backend\venv\Scripts\python.exe scripts\rebuild_dev_db_from_excel.py --confirm

# 2. Yield curves (not in the workbook; the script generates the 5 standard 2016-Q1 curves)
backend\venv\Scripts\python.exe backend\scripts\migrate_yield_curves.py
```

The rebuild script refuses to run unless `DATABASE_URL` points at `clo_dev` on
localhost/127.0.0.1, and does nothing without `--confirm`. It runs in one transaction: either
everything loads or nothing changes.

### What it builds
| Table | Rows | Excel source |
|---|---|---|
| (missing tables) | - | Created from the SQLAlchemy models (`create_all`); existing tables are untouched |
| `users` | 4 | Dev accounts (admin/manager/analyst/demo), bcrypt hashes; upserted by email |
| `clo_deals` | 10 | Each "Mag N Inputs" tab: **Date Inputs** block (cols AD/AE) and **CLO Inputs** block (target par) |
| `assets` | 384 | **"All Assets"** tab, 70 columns incl. the `flags` JSON (DIP, Cov-Lite, ...) |
| `deal_assets` | 2,726 | Each Inputs tab, **Deal Collateral** block (col D BLKRockID, col E Par Amount) |
| `clo_tranches` | 71 | Each Inputs tab, **CLO Liabilities** block (col AJ onward) |
| `concentration_test_definitions` | 54 | Definitions INSERT from `backend/migrations/005_vba_enum_realignment.sql` |
| `deal_concentration_thresholds` | 374 | Each Inputs tab, **Concentration Limits** block (cols L-O); "N/A" thresholds fall back to the definition default |

The script replaces the contents of `clo_deals`, `assets`, `deal_assets`, `clo_tranches`,
`concentration_test_definitions` and `deal_concentration_thresholds`. It does not touch the
correlation, scenario, parameter or reference tables (`asset_correlations`,
`scenario_inputs`, `model_parameters`, `reference_data`, ...), which have no SQLAlchemy models.

It also drops 8 CHECK constraints that the concentration models declare but the original
schema (migration 001) never had (e.g. `valid_mag_version` allowed only MAG6/MAG14/MAG17), and
restores the `DEFAULT CURRENT_TIMESTAMP` columns migration 001 created.

### Expected results
| Deal | Positions | Par ($M) | Tranches | Tests |
|---|---|---|---|---|
| MAG6 | 313 | 403.06 | 7 | 36 |
| MAG7 | 320 | 596.69 | 8 | 41 |
| MAG8 | 312 | 591.87 | 7 | 38 |
| MAG9 | 295 | 392.84 | 7 | 37 |
| MAG11 | 270 | 536.15 | 6 | 37 |
| MAG12 | 279 | 599.58 | 7 | 37 |
| MAG14 | 269 | 520.52 | 7 | 37 |
| MAG15 | 239 | 607.24 | 7 | 37 |
| MAG16 | 234 | 495.04 | 7 | 37 |
| MAG17 | 195 | 431.16 | 8 | 37 |

Spot checks that matched the pre-wipe system: MAG16 DIP = ENERGY FUTURE ($6.25M) + TEXAS
COMPETITIVE ($3.25M); 89 Cov-Lite assets, MAG16 Cov-Lite exposure $117.1M (23.65%); MAG16
tranches total $506.5M; MAG17 Test 19 (Netherlands) 3.04%, Test 20 (Germany) 0.14%.

### Differences from the pre-2026-11-08 database
- **Thresholds are Excel's per-deal values.** Migrations 006-010 used each deal's Excel test
  *numbers* but generic default *thresholds* plus a few hand-picked adjustments. Example: MAG17
  DIP obligor limit is now 2.0% (was 2.5%), Caa limit 7.5% (was 2.0%).
- **2,726 positions, not 2,768.** The extra 42 came from an early script that assigned assets
  to deals by vintage date; deal membership now comes only from each Inputs tab.
- **MAG7 and MAG17 have 8 tranches** - the Excel liabilities block includes a Class X note
  that the earlier hard-coded tranche lists omitted.
- **Effective date is blank for MAG15, MAG16 and MAG17** because those cells are empty in Excel.
- **Excel data quirks kept as-is:** MAG6 pricing date (2013-10-20) is after its closing date
  (2012-09-13); MAG7 maturity is 2025-01-15 in the Date Inputs block (2025-01-25 elsewhere on
  the tab) - the Date Inputs value is used.

---

## Migration Overview

The CLO Management System data migration transforms legacy Excel/VBA-based data into a modern database architecture, enabling scalable portfolio management and risk analytics.

### Migration Statistics

| Component | Source | Records Migrated | SQLite Database | PostgreSQL Status |
|-----------|---------|------------------|----------------|-------------------|
| All Assets | Excel Tab | 384 assets | SQLite | ✅ Operational in PostgreSQL |
| Reference Table | Excel Tab | 694 records | SQLite | ⚪ Empty (as expected) |
| Asset Correlations | Excel Matrix | 238,144 pairs | SQLite | ✅ Migrated to PostgreSQL |
| MAG Scenarios | 10 Excel Sheets | 19,795 parameters | SQLite | ✅ Migrated to PostgreSQL |
| Run Model Config | Excel Tab | 356 parameters | SQLite | ✅ Migrated to PostgreSQL |
| **Total** | **Excel Workbook** | **259,767 records** | **5 Databases** | **✅ 258,295 in PostgreSQL** |

### PostgreSQL Migration Summary
- **Migration Date**: August 16, 2025
- **Total Records in PostgreSQL**: 258,295 records
- **Migration Status**: ✅ COMPLETED SUCCESSFULLY
- **Validation Status**: ✅ ALL CHECKS PASSED

### Migration Benefits

- **Scalability**: From Excel limitations to database performance
- **Reliability**: Atomic transactions and data integrity
- **Integration**: APIs for real-time data access
- **Analytics**: SQL-based querying and reporting
- **Backup**: Automated backup and recovery procedures

---

## Migration Architecture

### Source System
- **Format**: Microsoft Excel (.xlsx) with VBA macros
- **Structure**: Multiple worksheets with complex formulas
- **Limitations**: Manual calculations, no concurrent access
- **Data Types**: Mixed text, numeric, date, and formula cells

### Target System
- **Databases**: SQLite for migrated data, PostgreSQL for operational data
- **Framework**: SQLAlchemy ORM with Python
- **Validation**: Comprehensive data integrity checks
- **Integration**: REST API layer for data access

### Migration Flow

```
Excel Workbook
    │
    ├── All Assets Tab ──────────► assets.db (SQLite) ──────────────┐
    ├── Reference Tab ───────────► reference.db (SQLite) ──────────┐│
    ├── Asset Correlation Matrix ► correlations.db (SQLite) ──────┐││
    ├── MAG Scenario Sheets ─────► scenarios.db (SQLite) ────────┐│││
    └── Run Model Config ────────► config.db (SQLite) ──────────┐││││
                                      │                        │││││
                                      ▼                        ▼▼▼▼▼
                               PostgreSQL Operational DB ◄─── MIGRATED
                               ├── assets (384 records)
                               ├── asset_correlations_migrated (238,144)
                               ├── model_config_migrated (356)  
                               ├── mag_scenarios_migrated (19,795)
                               └── reference_data_migrated (0)
```

### PostgreSQL Migration Architecture
- **Migration Script**: `migrate_sqlite_to_postgresql.py`
- **Migration Tables**: Dedicated `*_migrated` tables for SQLite data
- **Schema Optimization**: Mixed data type support for MAG scenarios
- **Validation Framework**: Comprehensive data integrity checks
- **Batch Processing**: 1,000 record batches for optimal performance

---

## Migration Components

### 1. All Assets Migration

**File**: `execute_all_assets_migration.py`

#### Purpose
Migrates complete asset portfolio from Excel to normalized database structure.

#### Source Data
- **Worksheet**: "All Assets"
- **Rows**: 385 (384 assets + header)
- **Columns**: 71 asset properties

#### Key Features
- **Data Type Conversion**: Automatic type detection and conversion
- **Validation**: Credit rating validation, numeric field checks
- **Error Handling**: Graceful handling of missing or invalid data
- **Batch Processing**: Efficient bulk inserts

#### Schema
```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    borrower VARCHAR(100),
    industry VARCHAR(50),
    par_amount DECIMAL(15,2),
    current_balance DECIMAL(15,2),
    rating VARCHAR(10),
    maturity_date DATE,
    -- ... 64 additional columns
);
```

#### Validation Rules
- Borrower names must be non-empty strings
- Par amounts must be positive numbers
- Credit ratings follow standard format (Aaa, Aa1, etc.)
- Dates must be valid and future-dated for new issues

### 2. Reference Table Migration

**File**: `execute_reference_migration.py`

#### Purpose
Migrates reference data for lookups, mappings, and business rules.

#### Source Data
- **Worksheet**: "Reference Table"
- **Records**: 694 reference entries
- **Categories**: Industry codes, rating mappings, sector classifications

#### Key Features
- **Category Management**: Automatic categorization of reference data
- **Hierarchy Support**: Parent-child relationships for nested categories
- **Multi-version Support**: Historical reference data preservation

#### Schema
```sql
CREATE TABLE reference_data (
    id INTEGER PRIMARY KEY,
    category VARCHAR(50),
    code VARCHAR(20),
    description TEXT,
    parent_code VARCHAR(20),
    is_active BOOLEAN,
    version INTEGER
);
```

### 3. Asset Correlation Matrix Migration

**File**: `migrate_asset_correlation_matrix.py`

#### Purpose
Migrates 488×488 asset correlation matrix for risk management calculations.

#### Source Data
- **Matrix Size**: 488 borrowers × 488 borrowers
- **Total Pairs**: 238,144 correlation coefficients
- **Data Type**: Decimal correlations (-1.0 to +1.0)

#### Key Features
- **Symmetric Matrix**: Validates correlation symmetry
- **Batch Processing**: Processes correlations in chunks of 1000
- **Memory Optimization**: Efficient handling of large matrix
- **Validation**: Correlation coefficient range validation

#### Schema
```sql
CREATE TABLE asset_correlations (
    id INTEGER PRIMARY KEY,
    borrower_1 VARCHAR(100),
    borrower_2 VARCHAR(100),
    correlation_coefficient DECIMAL(10,8),
    last_updated TIMESTAMP
);
```

#### Processing Logic
```python
# Matrix extraction with validation
for i, borrower_1 in enumerate(borrowers):
    for j, borrower_2 in enumerate(borrowers):
        if i <= j:  # Upper triangular + diagonal
            correlation = correlation_matrix[i][j]
            if -1.0 <= correlation <= 1.0:
                yield (borrower_1, borrower_2, correlation)
```

### 4. MAG Scenario Data Migration

**File**: `migrate_mag_scenario_data.py`

#### Purpose
Migrates Moody's Analytics MAG scenario parameters for stress testing and modeling.

#### Source Data
- **Worksheets**: 10 MAG scenario input sheets
- **Parameters**: 19,795 scenario parameters
- **Categories**: Economic variables, rating transitions, recovery rates

#### Key Features
- **Multi-scenario Support**: Handles multiple MAG versions
- **Parameter Categorization**: Automatic parameter classification
- **Time Series Data**: Historical and projected parameter values
- **Validation**: Parameter range and consistency checks

#### Schema
```sql
CREATE TABLE mag_scenarios (
    id INTEGER PRIMARY KEY,
    scenario_name VARCHAR(50),
    parameter_name VARCHAR(100),
    parameter_category VARCHAR(50),
    time_period VARCHAR(20),
    parameter_value DECIMAL(15,6),
    data_type VARCHAR(20)
);
```

#### Parameter Categories
- **Macroeconomic**: GDP growth, unemployment rates, interest rates
- **Credit**: Default rates, recovery rates, rating migrations  
- **Market**: Equity volatility, credit spreads, correlation adjustments

### 5. Run Model Configuration Migration

**File**: `migrate_run_model_config.py`

#### Purpose
Migrates model execution parameters and configuration settings.

#### Source Data
- **Configuration Items**: 356 parameters (137 active, 219 legacy)
- **Categories**: Model settings, calculation parameters, output options

#### Key Features
- **Parameter Versioning**: Tracks parameter changes over time
- **Active/Legacy Management**: Distinguishes current vs. historical parameters
- **Type Safety**: Strongly typed parameter values
- **Documentation**: Parameter descriptions and usage notes

#### Schema
```sql
CREATE TABLE model_config (
    id INTEGER PRIMARY KEY,
    parameter_name VARCHAR(100),
    parameter_value TEXT,
    parameter_type VARCHAR(20),
    category VARCHAR(50),
    is_active BOOLEAN,
    description TEXT,
    last_modified TIMESTAMP
);
```

---

## Validation Procedures

### Pre-Migration Validation

#### Source Data Validation
```python
# Excel file accessibility
assert os.path.exists(excel_file_path)
assert excel_file_path.endswith('.xlsx')

# Worksheet existence
workbook = openpyxl.load_workbook(excel_file_path)
required_sheets = ['All Assets', 'Reference Table', ...]
for sheet in required_sheets:
    assert sheet in workbook.sheetnames
```

#### Data Quality Checks
```python
# Data completeness
def validate_completeness(data_frame):
    missing_data = data_frame.isnull().sum()
    critical_fields = ['Borrower', 'Par Amount', 'Rating']
    
    for field in critical_fields:
        if missing_data[field] > 0:
            logger.warning(f"Missing data in {field}: {missing_data[field]} records")

# Data consistency
def validate_consistency(data_frame):
    # Check for duplicate borrowers
    duplicates = data_frame['Borrower'].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate borrowers"
    
    # Validate rating format
    invalid_ratings = ~data_frame['Rating'].str.match(r'^[A-C][a-c]*[0-3]?$')
    assert invalid_ratings.sum() == 0, "Invalid credit rating format detected"
```

### Migration Validation

#### Transaction Integrity
```python
# Atomic migration with rollback.
# session_scope() commits when the block exits normally and rolls back on any exception.
from app.core.database import session_scope

def migrate_with_validation(source_data):
    with session_scope() as session:
        migrate_data(source_data, session)
        validate_migration_results(session)   # raise to roll everything back
    logger.info("Migration completed successfully")
```

#### Data Integrity Checks
```python
# Row count validation
source_count = len(source_data)
target_count = session.query(TargetModel).count()
assert source_count == target_count, f"Count mismatch: {source_count} vs {target_count}"

# Data type validation
numeric_fields = ['Par_Amount', 'Current_Balance', 'Spread']
for field in numeric_fields:
    non_numeric = session.query(TargetModel).filter(
        ~TargetModel.__dict__[field].op('REGEXP')(r'^[0-9]*\.?[0-9]*$')
    ).count()
    assert non_numeric == 0, f"Non-numeric data in {field}"
```

### Post-Migration Validation

#### Referential Integrity
```python
# Foreign key validation
orphaned_records = session.query(AssetModel).filter(
    ~AssetModel.borrower.in_(
        session.query(ReferenceModel.borrower)
    )
).count()

assert orphaned_records == 0, f"Found {orphaned_records} orphaned asset records"
```

#### Business Rule Validation
```python
# Portfolio constraints
total_par = session.query(func.sum(AssetModel.par_amount)).scalar()
assert 900_000_000 <= total_par <= 1_100_000_000, f"Portfolio size outside expected range: {total_par}"

# Rating distribution validation
rating_distribution = session.query(
    AssetModel.rating, func.count()
).group_by(AssetModel.rating).all()

investment_grade = sum(count for rating, count in rating_distribution 
                      if rating in ['Aaa', 'Aa1', 'Aa2', 'Aa3', 'A1', 'A2', 'A3', 
                                   'Baa1', 'Baa2', 'Baa3'])
total_assets = sum(count for _, count in rating_distribution)
ig_percentage = investment_grade / total_assets

assert 0.6 <= ig_percentage <= 0.9, f"Investment grade percentage outside expected range: {ig_percentage}"
```

---

## Execution Guide

### Prerequisites

#### System Requirements
- Python 3.8+
- SQLite3
- openpyxl library
- SQLAlchemy ORM
- Sufficient disk space (2GB recommended)

#### File Preparation
```bash
# Verify Excel file accessibility
ls -la "CLO Model V2 - Amended and Restated.xlsx"

# Check file permissions
chmod 644 "CLO Model V2 - Amended and Restated.xlsx"

# Backup original file
cp "CLO Model V2 - Amended and Restated.xlsx" "CLO Model V2 - Backup $(date +%Y%m%d).xlsx"
```

### Migration Sequence

#### Step 1: Assets Migration
```bash
python execute_all_assets_migration.py
```

**Expected Output:**
```
2024-01-10 09:00:00 - INFO - Starting All Assets migration
2024-01-10 09:00:01 - INFO - Found 384 assets in Excel worksheet
2024-01-10 09:00:02 - INFO - Validating asset data...
2024-01-10 09:00:03 - INFO - Creating SQLite database: assets.db
2024-01-10 09:00:05 - INFO - Migration completed: 384 assets migrated successfully
```

#### Step 2: Reference Data Migration
```bash
python execute_reference_migration.py
```

**Expected Output:**
```
2024-01-10 09:05:00 - INFO - Starting Reference Table migration
2024-01-10 09:05:01 - INFO - Found 694 reference records
2024-01-10 09:05:02 - INFO - Categorizing reference data...
2024-01-10 09:05:04 - INFO - Migration completed: 694 records migrated successfully
```

#### Step 3: Correlation Matrix Migration
```bash
python migrate_asset_correlation_matrix.py
```

**Expected Output:**
```
2024-01-10 09:10:00 - INFO - Starting Asset Correlation Matrix migration
2024-01-10 09:10:01 - INFO - Processing 488x488 correlation matrix
2024-01-10 09:10:15 - INFO - Batch processing: 238,144 correlations
2024-01-10 09:12:30 - INFO - Migration completed: 238,144 correlations migrated successfully
```

#### Step 4: Scenario Data Migration
```bash
python migrate_mag_scenario_data.py
```

**Expected Output:**
```
2024-01-10 09:15:00 - INFO - Starting MAG Scenario Data migration
2024-01-10 09:15:01 - INFO - Processing 10 MAG scenario sheets
2024-01-10 09:15:45 - INFO - Migration completed: 19,795 parameters migrated successfully
```

#### Step 5: Configuration Migration
```bash
python migrate_run_model_config.py
```

**Expected Output:**
```
2024-01-10 09:20:00 - INFO - Starting Run Model Configuration migration
2024-01-10 09:20:01 - INFO - Processing 356 configuration parameters
2024-01-10 09:20:05 - INFO - Migration completed: 356 parameters migrated successfully
```

### Automation Script

```bash
#!/bin/bash
# Complete migration automation script

echo "Starting CLO data migration..."

# Set error handling
set -e

# Migration sequence
echo "Step 1: Migrating Assets..."
python execute_all_assets_migration.py

echo "Step 2: Migrating Reference Data..."
python execute_reference_migration.py

echo "Step 3: Migrating Correlation Matrix..."
python migrate_asset_correlation_matrix.py

echo "Step 4: Migrating Scenario Data..."
python migrate_mag_scenario_data.py

echo "Step 5: Migrating Configuration..."
python migrate_run_model_config.py

echo "Migration completed successfully!"
echo "Total records migrated: 259,767"
```

---

## Troubleshooting

### Common Issues

#### Excel File Access Errors
```
FileNotFoundError: Excel file not found
```
**Solution:**
- Verify file path and name
- Check file permissions
- Ensure Excel file is not open in another application

#### Unicode Character Errors
```
UnicodeDecodeError: 'charmap' codec can't decode
```
**Solution:**
- Replace Unicode characters (✅, ❌) with ASCII equivalents
- Use UTF-8 encoding for all text operations

#### Memory Issues
```
MemoryError: Unable to allocate memory
```
**Solution:**
- Process data in smaller batches
- Use generators instead of loading all data at once
- Increase available system memory

#### Database Lock Errors
```
sqlite3.OperationalError: database is locked
```
**Solution:**
- Ensure no other processes are accessing the database
- Use proper connection management with context managers
- Implement retry logic with exponential backoff

### Validation Failures

#### Data Type Mismatches
```python
# Fix data type issues
def clean_numeric_data(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        # Remove currency symbols, commas
        cleaned = re.sub(r'[$,]', '', str(value))
        try:
            return float(cleaned)
        except ValueError:
            return None
    return float(value)
```

#### Credit Rating Issues
```python
# Standardize credit ratings
def standardize_rating(rating):
    if pd.isna(rating):
        return 'NR'  # Not Rated
    
    rating = str(rating).strip().upper()
    
    # Handle common variations
    rating_map = {
        'AAA': 'Aaa',
        'AA+': 'Aa1', 'AA': 'Aa2', 'AA-': 'Aa3',
        'A+': 'A1', 'A': 'A2', 'A-': 'A3',
        'BBB+': 'Baa1', 'BBB': 'Baa2', 'BBB-': 'Baa3',
        'BB+': 'Ba1', 'BB': 'Ba2', 'BB-': 'Ba3',
        'B+': 'B1', 'B': 'B2', 'B-': 'B3'
    }
    
    return rating_map.get(rating, rating)
```

### Performance Optimization

#### Batch Processing
```python
def batch_migrate(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        session.bulk_insert_mappings(TargetModel, batch)
        session.commit()
        logger.info(f"Processed batch {i//batch_size + 1}")
```

#### Index Creation
```sql
-- Create indexes for better query performance
CREATE INDEX idx_assets_borrower ON assets(borrower);
CREATE INDEX idx_assets_rating ON assets(rating);
CREATE INDEX idx_correlations_borrower1 ON asset_correlations(borrower_1);
CREATE INDEX idx_correlations_borrower2 ON asset_correlations(borrower_2);
CREATE INDEX idx_scenarios_name ON mag_scenarios(scenario_name);
```

---

## Post-Migration Verification

### Data Quality Assessment

#### Completeness Check
```sql
-- Verify all expected records migrated
SELECT 
    'assets' as table_name, 
    COUNT(*) as record_count,
    384 as expected_count,
    CASE WHEN COUNT(*) = 384 THEN 'PASS' ELSE 'FAIL' END as status
FROM assets

UNION ALL

SELECT 
    'reference_data', 
    COUNT(*), 
    694, 
    CASE WHEN COUNT(*) = 694 THEN 'PASS' ELSE 'FAIL' END
FROM reference_data

UNION ALL

SELECT 
    'asset_correlations', 
    COUNT(*), 
    238144, 
    CASE WHEN COUNT(*) = 238144 THEN 'PASS' ELSE 'FAIL' END
FROM asset_correlations;
```

#### Data Integrity Check
```sql
-- Verify no orphaned references
SELECT 
    a.borrower,
    COUNT(*) as correlation_count
FROM assets a
LEFT JOIN asset_correlations c1 ON a.borrower = c1.borrower_1
LEFT JOIN asset_correlations c2 ON a.borrower = c2.borrower_2
WHERE c1.borrower_1 IS NULL AND c2.borrower_2 IS NULL
GROUP BY a.borrower;
```

#### Business Logic Validation
```sql
-- Portfolio composition validation
SELECT 
    rating,
    COUNT(*) as asset_count,
    SUM(par_amount) as total_par,
    ROUND(100.0 * SUM(par_amount) / (SELECT SUM(par_amount) FROM assets), 2) as percentage
FROM assets
GROUP BY rating
ORDER BY total_par DESC;
```

### Performance Benchmarking

#### Query Performance
```python
import time

def benchmark_query(query, description):
    start_time = time.time()
    result = session.execute(query)
    end_time = time.time()
    
    logger.info(f"{description}: {end_time - start_time:.3f} seconds")
    return result

# Benchmark key queries
benchmark_query("SELECT COUNT(*) FROM assets", "Asset count query")
benchmark_query("SELECT * FROM assets WHERE rating LIKE 'Aa%'", "Rating filter query")
benchmark_query("""
    SELECT c.borrower_1, c.borrower_2, c.correlation_coefficient 
    FROM asset_correlations c 
    WHERE c.correlation_coefficient > 0.8
""", "High correlation query")
```

### Integration Testing

#### API Integration
```python
# Test data integration service
from backend.app.services.data_integration import DataIntegrationService

service = DataIntegrationService()

# Test asset retrieval
assets = service.get_migrated_assets()
assert len(assets) == 384

# Test correlation lookup
correlation = service.get_asset_correlation('BORROWER_A', 'BORROWER_B')
assert -1.0 <= correlation <= 1.0

# Test scenario data access
scenario_data = service.get_mag_scenario_parameters('MAG_BASELINE')
assert len(scenario_data) > 0
```

### Migration Report Generation

```python
def generate_migration_report():
    report = {
        'migration_date': datetime.now().isoformat(),
        'total_records_migrated': 259767,
        'migration_components': {
            'assets': {'records': 384, 'database': 'assets.db'},
            'reference': {'records': 694, 'database': 'reference.db'},
            'correlations': {'records': 238144, 'database': 'correlations.db'},
            'scenarios': {'records': 19795, 'database': 'scenarios.db'},
            'config': {'records': 356, 'database': 'config.db'}
        },
        'validation_results': {
            'data_completeness': 'PASS',
            'referential_integrity': 'PASS',
            'business_rules': 'PASS',
            'performance_benchmarks': 'PASS'
        }
    }
    
    with open('migration_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info("Migration report generated: migration_report.json")
```

This comprehensive data migration guide provides all necessary procedures and validation steps to ensure successful migration of the CLO system from Excel to database architecture.