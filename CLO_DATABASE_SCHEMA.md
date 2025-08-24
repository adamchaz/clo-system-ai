# CLO Management System - Database Schema Overview

## Executive Summary

The CLO (Collateralized Loan Obligation) Management System database schema represents a comprehensive financial system with 25+ core tables supporting the complete lifecycle of CLO portfolio management. The schema has been converted from a sophisticated VBA-based Excel system to a modern PostgreSQL database with full relationship integrity and business logic preservation.

**Key Statistics**:
- **259,767+ records** migrated from legacy system
- **384 assets** with 71 properties each
- **5 yield curves** with 3,600+ data points
- **25+ SQLAlchemy models** with complete relationships
- **Production-ready** with comprehensive indexing and constraints

---

## 1. Core Entity Tables

### 1.1 Asset Management

#### **`assets`** - Core Asset Repository
**Purpose**: Individual financial assets in CLO portfolios with comprehensive credit and financial data
- **Primary Key**: `blkrock_id` (BlackRock asset identifier)  
- **Key Fields**: 
  - `issue_name`, `issuer_name`, `par_amount`, `maturity`
  - `coupon`, `coupon_type`, `payment_freq` (interest terms)
  - `mdy_rating`, `sp_rating` (credit ratings)
  - `flags` (JSON - asset classification flags)
- **Business Logic**: 71 financial properties including rating derivations, yield curve integration, and cash flow calculations

#### **`asset_cash_flows`** - Asset Cash Flow Projections  
**Purpose**: Period-by-period cash flow projections for individual assets
- **Primary Key**: `id` (auto-increment)
- **Foreign Key**: `blkrock_id` → `assets.blkrock_id`
- **Key Fields**: `payment_date`, `interest_payment`, `scheduled_principal`, `unscheduled_principal`, `defaults`, `recoveries`

#### **`asset_history`** - Historical Asset Data
**Purpose**: Track historical changes in asset properties (ratings, prices, etc.)
- **Primary Key**: `id` (auto-increment)
- **Foreign Key**: `blkrock_id` → `assets.blkrock_id`
- **Key Fields**: `history_date`, `property_name`, `property_value`

### 1.2 CLO Deal Structure

#### **`clo_deals`** - Master Deal Records
**Purpose**: CLO deal master information and key dates
- **Primary Key**: `deal_id`
- **Key Fields**: `deal_name`, `manager_name`, `pricing_date`, `closing_date`, `maturity_date`, `target_par_amount`
- **Relationships**: One-to-many with tranches, assets, liabilities, triggers, fees

#### **`clo_tranches`** - Note Tranches
**Purpose**: Individual note tranches within CLO deals
- **Primary Key**: `tranche_id`
- **Foreign Key**: `deal_id` → `clo_deals.deal_id`
- **Key Fields**: `tranche_name`, `current_balance`, `coupon_rate`, `seniority_level`, `payment_rank`

#### **`deal_assets`** - Deal-Asset Position Linking
**Purpose**: Links assets to specific deals with position details
- **Composite Primary Key**: (`deal_id`, `blkrock_id`)
- **Key Fields**: `par_amount`, `purchase_price`, `purchase_date`, `position_status`

### 1.3 Authentication & Authorization

#### **`users`** - User Account Management
**Purpose**: User accounts with role-based access control
- **Primary Key**: `user_id`
- **Key Fields**: `username`, `email`, `password_hash`, `role` (admin/manager/analyst/viewer)
- **RBAC**: Four-tier role system with differentiated permissions

---

## 2. Financial Tables

### 2.1 Cash Flow & Payment Systems

#### **`liability_cash_flows`** - Tranche Payment Tracking
**Purpose**: Period-by-period liability payments with PIK support
- **Primary Key**: `id` (auto-increment)
- **Foreign Key**: `liability_id` → `liabilities.liability_id`
- **Key Fields**: `beginning_balance`, `interest_accrued`, `interest_paid`, `principal_paid`, `deferred_balance`

#### **`fees`** - Fee Configuration
**Purpose**: Management fees, trustee fees, incentive fees with complex calculation logic
- **Primary Key**: `fee_id` (auto-increment)
- **Foreign Key**: `deal_id` → `clo_deals.deal_id`
- **Key Fields**: `fee_type` (BEGINNING/AVERAGE/FIXED), `fee_percentage`, `interest_on_fee`

#### **`fee_calculations`** - Period Fee Calculations
**Purpose**: Detailed fee calculations for each payment period
- **Primary Key**: `id` (auto-increment)
- **Foreign Key**: `fee_id` → `fees.fee_id`
- **Key Fields**: `period_number`, `base_fee_accrued`, `interest_on_unpaid_fee`, `fee_paid`

### 2.2 Waterfall & Distribution Logic

#### **`waterfall_configurations`** - Payment Waterfall Rules
**Purpose**: Defines payment priorities and waterfall logic by deal
- **Primary Key**: `config_id` (auto-increment)
- **Foreign Key**: `deal_id` → `clo_deals.deal_id`
- **Key Fields**: `payment_rules` (JSON), `senior_mgmt_fee_rate`, `interest_reserve_target`

#### **`waterfall_executions`** - Waterfall Execution Records
**Purpose**: Records of actual waterfall executions with cash distribution
- **Primary Key**: `execution_id` (auto-increment)
- **Key Fields**: `payment_date`, `collection_amount`, `total_available`, `oc_test_pass`, `ic_test_pass`

#### **`waterfall_payments`** - Individual Payment Steps
**Purpose**: Individual payments within waterfall execution
- **Primary Key**: `payment_id` (auto-increment)
- **Foreign Key**: `execution_id` → `waterfall_executions.execution_id`
- **Key Fields**: `payment_step`, `amount_due`, `amount_paid`, `amount_deferred`, `target_tranche_id`

### 2.3 Trigger & Compliance Systems

#### **`oc_triggers`** - Overcollateralization Tests
**Purpose**: OC trigger calculations and cure mechanism tracking
- **Primary Key**: `trigger_id` (auto-increment)
- **Foreign Key**: `deal_id` → `clo_deals.deal_id`
- **Key Fields**: `oc_threshold`, `calculated_ratio`, `pass_fail`, `interest_cure_amount`, `principal_cure_amount`

#### **`ic_triggers`** - Interest Coverage Tests
**Purpose**: IC trigger calculations (similar structure to OC triggers)
- **Primary Key**: `trigger_id` (auto-increment)
- **Key Fields**: Similar to oc_triggers but for interest coverage ratios

---

## 3. Reference Tables

### 3.1 Yield Curve System

#### **`yield_curves`** - Yield Curve Definitions
**Purpose**: Yield curve master records for pricing and discounting
- **Primary Key**: `curve_id` (auto-increment)
- **Key Fields**: `curve_name`, `curve_type`, `currency`, `analysis_date`, `last_month`

#### **`yield_curve_rates`** - Spot Rate Data
**Purpose**: Spot rates by maturity with interpolation support
- **Primary Key**: `rate_id` (auto-increment)
- **Foreign Key**: `curve_id` → `yield_curves.curve_id`
- **Key Fields**: `maturity_month`, `spot_rate`, `is_interpolated`

#### **`forward_rates`** - Forward Rate Calculations
**Purpose**: Forward rates calculated using VBA-exact formulas
- **Primary Key**: `forward_id` (auto-increment)
- **Foreign Key**: `curve_id` → `yield_curves.curve_id`
- **Key Fields**: `forward_date`, `forward_rate`, `calculation_method`

### 3.2 Portfolio Management

#### **`collateral_pools`** - Portfolio Aggregation
**Purpose**: Portfolio-level aggregation and compliance testing
- **Primary Key**: `pool_id` (auto-increment)
- **Foreign Key**: `deal_id` → `clo_deals.deal_id`
- **Key Fields**: `analysis_date`, `total_par_amount`, `total_assets`, `current_objective_value`

#### **`collateral_pool_assets`** - Pool Asset Membership
**Purpose**: Asset membership in collateral pools with position tracking
- **Primary Key**: `id` (auto-increment)
- **Foreign Keys**: `pool_id` → `collateral_pools.pool_id`, `asset_id` → `assets.blkrock_id`

#### **`concentration_test_results`** - Compliance Test Results
**Purpose**: Storage for concentration test results by pool
- **Primary Key**: `id` (auto-increment)
- **Foreign Key**: `pool_id` → `collateral_pools.pool_id`
- **Key Fields**: `test_number`, `test_name`, `threshold_value`, `result_value`, `pass_fail`

---

## 4. Relationship Tables

### 4.1 Many-to-Many Relationships

#### **`collateral_pool_assets`**
- **Links**: `collateral_pools` ↔ `assets`
- **Purpose**: Asset membership in multiple pools

#### **`deal_assets`**  
- **Links**: `clo_deals` ↔ `assets`
- **Purpose**: Asset positions within specific deals

#### **`document_folder_items`**
- **Links**: `document_folders` ↔ `documents`
- **Purpose**: Document organization in folder hierarchies

### 4.2 Hierarchical Relationships

#### **`documents`** - Self-referencing for versioning
- **Relationship**: `parent_document_id` → `documents.document_id`
- **Purpose**: Document version control

#### **`document_folders`** - Self-referencing for hierarchy
- **Relationship**: `parent_folder_id` → `document_folders.folder_id`
- **Purpose**: Nested folder structures

---

## 5. Key Relationships

### 5.1 Core Business Relationships

```
CLODeal (1) → (M) CLOTranche
         ↓
        (M) DealAsset (M) ← Asset
         ↓                   ↑
        (M) Liability       (M) AssetCashFlow
         ↓
        (M) LiabilityCashFlow

CLODeal (1) → (M) Fee → (M) FeeCalculation
         ↓
        (M) OCTrigger / ICTrigger
         ↓
        (M) WaterfallExecution → (M) WaterfallPayment
```

### 5.2 Portfolio Management Relationships

```
CLODeal (1) → (M) CollateralPool
                   ↓
                  (M) CollateralPoolAsset (M) ← Asset
                   ↓
                  (M) ConcentrationTestResult

YieldCurve (1) → (M) YieldCurveRate
            ↓
           (M) ForwardRate
```

### 5.3 Document & Reporting Relationships

```
User (1) → (M) Document
           ↓
          (M) DocumentAccess / DocumentShare

ReportTemplate (1) → (M) Report
                    ↓
                   (M) ReportSchedule
```

---

## 6. Table Purposes

### 6.1 Core Financial Operations
- **`assets`**: Master repository of financial instruments with comprehensive metadata
- **`asset_cash_flows`**: Cash flow projections supporting NPV and risk calculations
- **`clo_deals`**: Deal master data coordinating all deal-related entities
- **`liabilities`**: Note tranches with payment terms and risk measures
- **`fees`**: Complex fee structures with accrual and payment tracking

### 6.2 Risk & Compliance
- **`oc_triggers`** / **`ic_triggers`**: Regulatory compliance testing with cure mechanisms
- **`concentration_test_results`**: Portfolio compliance across 91 different test types
- **`collateral_pools`**: Portfolio aggregation for optimization and testing

### 6.3 Financial Calculations
- **`yield_curves`**: Market-based pricing and discounting infrastructure
- **`waterfall_*`**: Payment waterfall execution with detailed step tracking
- **`fee_calculations`**: Period-by-period fee accrual and payment history

### 6.4 Operations & Management
- **`users`**: Role-based access control with four-tier permissions
- **`documents`**: Document management with version control and access tracking
- **`reports`**: Report generation system with templates and scheduling

---

## 7. Technical Implementation Notes

### 7.1 Data Migration Status
- **Complete Migration**: 259,767 records successfully migrated from Excel/VBA system
- **Asset Data**: 384 assets with 71 properties each fully operational
- **Yield Curves**: 5 curves with 3,600+ rate points (spot + forward rates)
- **Historical Data**: March 23, 2016 baseline with time-series support

### 7.2 Business Logic Preservation
- **VBA Parity**: All financial calculations maintain exact VBA computational equivalence
- **QuantLib Integration**: Enhanced with QuantLib for advanced financial mathematics
- **Rating Systems**: Complete cross-agency rating derivation logic preserved
- **Waterfall Logic**: Complex payment priority systems fully converted

### 7.3 Performance & Scalability
- **Indexed Relationships**: All foreign keys properly indexed for query performance
- **JSON Columns**: Flexible metadata storage for evolving business requirements
- **Audit Trails**: Comprehensive created_at/updated_at timestamps throughout
- **Production Ready**: Full constraint integrity with proper cascade behaviors

This database schema represents a complete conversion of a sophisticated Excel-based CLO management system into a modern, scalable relational database structure while preserving all critical financial business logic and regulatory compliance requirements.