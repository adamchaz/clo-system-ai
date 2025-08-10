-- CLO Portfolio Management System Database Schema
-- Converted from VBA TradeHypoPrelimv32.xlsm to PostgreSQL
-- Supports asset management, cash flows, compliance testing, and analytics
-- Includes comprehensive Magnetar (Mag 6-17) waterfall implementation

-- =============================================================================
-- CORE ASSET TABLES
-- =============================================================================

-- Main asset table (converted from Asset.cls)
CREATE TABLE assets (
    -- Primary Identification
    blkrock_id VARCHAR(50) PRIMARY KEY,
    issue_name VARCHAR(255) NOT NULL,
    issuer_name VARCHAR(255) NOT NULL,
    issuer_id VARCHAR(50),
    tranche VARCHAR(10),
    
    -- Asset Classification
    bond_loan VARCHAR(10),
    par_amount DECIMAL(18,2) NOT NULL,
    market_value DECIMAL(8,4),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Dates
    maturity DATE NOT NULL,
    dated_date DATE,
    issue_date DATE,
    first_payment_date DATE,
    date_of_default DATE,
    
    -- Interest Rate Properties
    coupon DECIMAL(10,6),
    coupon_type VARCHAR(10), -- FIXED, FLOAT
    index_name VARCHAR(20),  -- LIBOR, SOFR, etc.
    cpn_spread DECIMAL(10,6),
    libor_floor DECIMAL(10,6),
    index_cap DECIMAL(10,6),
    payment_freq INTEGER, -- 1,2,4,12
    
    -- Cash Flow Properties
    amortization_type VARCHAR(20),
    day_count VARCHAR(20),
    business_day_conv VARCHAR(30),
    payment_eom BOOLEAN DEFAULT FALSE,
    amount_issued DECIMAL(18,2),
    
    -- PIK Properties
    piking BOOLEAN DEFAULT FALSE,
    pik_amount DECIMAL(18,2),
    unfunded_amount DECIMAL(18,2),
    
    -- Credit Ratings (Current)
    mdy_rating VARCHAR(10),
    mdy_dp_rating VARCHAR(10),
    mdy_dp_rating_warf VARCHAR(10),
    mdy_recovery_rate DECIMAL(5,4),
    sp_rating VARCHAR(10),
    
    -- Additional Ratings
    mdy_facility_rating VARCHAR(10),
    mdy_facility_outlook VARCHAR(10),
    mdy_issuer_rating VARCHAR(10),
    mdy_issuer_outlook VARCHAR(10),
    mdy_snr_sec_rating VARCHAR(10),
    mdy_snr_unsec_rating VARCHAR(10),
    mdy_sub_rating VARCHAR(10),
    mdy_credit_est_rating VARCHAR(10),
    mdy_credit_est_date DATE,
    
    sandp_facility_rating VARCHAR(10),
    sandp_issuer_rating VARCHAR(10),
    sandp_snr_sec_rating VARCHAR(10),
    sandp_subordinate VARCHAR(10),
    sandp_rec_rating VARCHAR(10),
    
    -- Industry Classifications
    mdy_industry VARCHAR(100),
    sp_industry VARCHAR(100),
    country VARCHAR(50),
    seniority VARCHAR(20),
    mdy_asset_category VARCHAR(50),
    sp_priority_category VARCHAR(50),
    
    -- Financial Properties
    commit_fee DECIMAL(10,6),
    facility_size DECIMAL(18,2),
    wal DECIMAL(8,4),
    
    -- Asset Flags (JSON for flexibility)
    flags JSONB,
    
    -- Analyst Information
    analyst_opinion TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Historical asset data (ratings, prices, etc.)
CREATE TABLE asset_history (
    id SERIAL PRIMARY KEY,
    blkrock_id VARCHAR(50) NOT NULL REFERENCES assets(blkrock_id) ON DELETE CASCADE,
    history_date DATE NOT NULL,
    property_name VARCHAR(50) NOT NULL, -- mdy_rating, sp_rating, market_value, etc.
    property_value VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Asset cash flows (converted from SimpleCashflow.cls)
CREATE TABLE asset_cash_flows (
    id SERIAL PRIMARY KEY,
    blkrock_id VARCHAR(50) NOT NULL REFERENCES assets(blkrock_id) ON DELETE CASCADE,
    period_number INTEGER NOT NULL,
    
    -- Dates
    payment_date DATE NOT NULL,
    accrual_start_date DATE NOT NULL,
    accrual_end_date DATE NOT NULL,
    
    -- Balances
    beginning_balance DECIMAL(18,2) NOT NULL DEFAULT 0,
    ending_balance DECIMAL(18,2) NOT NULL DEFAULT 0,
    default_balance DECIMAL(18,2) DEFAULT 0,
    mv_default_balance DECIMAL(18,2) DEFAULT 0,
    
    -- Cash Flows
    interest_payment DECIMAL(18,2) DEFAULT 0,
    scheduled_principal DECIMAL(18,2) DEFAULT 0,
    unscheduled_principal DECIMAL(18,2) DEFAULT 0,
    default_amount DECIMAL(18,2) DEFAULT 0,
    mv_default_amount DECIMAL(18,2) DEFAULT 0,
    recoveries DECIMAL(18,2) DEFAULT 0,
    net_loss DECIMAL(18,2) DEFAULT 0,
    
    -- Purchases/Sales
    purchases DECIMAL(18,2) DEFAULT 0,
    sales DECIMAL(18,2) DEFAULT 0,
    
    -- Total
    total_cash_flow DECIMAL(18,2) DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(blkrock_id, period_number)
);

-- =============================================================================
-- CLO STRUCTURE TABLES
-- =============================================================================

-- CLO deal information
CREATE TABLE clo_deals (
    deal_id VARCHAR(50) PRIMARY KEY,
    deal_name VARCHAR(255) NOT NULL,
    manager_name VARCHAR(100),
    trustee_name VARCHAR(100),
    
    -- Key Dates
    pricing_date DATE,
    closing_date DATE,
    effective_date DATE,
    first_payment_date DATE,
    maturity_date DATE,
    reinvestment_end_date DATE,
    no_call_date DATE,
    
    -- Deal Parameters
    target_par_amount DECIMAL(18,2),
    ramp_up_period INTEGER, -- months
    payment_frequency INTEGER, -- payments per year
    
    -- Status
    deal_status VARCHAR(20), -- ACTIVE, CALLED, MATURED
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CLO tranches (notes)
CREATE TABLE clo_tranches (
    tranche_id VARCHAR(50) PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    tranche_name VARCHAR(50) NOT NULL,
    
    -- Tranche Properties
    initial_balance DECIMAL(18,2),
    current_balance DECIMAL(18,2),
    coupon_rate DECIMAL(10,6),
    coupon_type VARCHAR(10), -- FIXED, FLOAT
    index_name VARCHAR(20),
    margin DECIMAL(10,6),
    
    -- Rating and Seniority
    mdy_rating VARCHAR(10),
    sp_rating VARCHAR(10),
    seniority_level INTEGER,
    
    -- Payment Terms
    payment_rank INTEGER,
    interest_deferrable BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deal asset mapping
CREATE TABLE deal_assets (
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    blkrock_id VARCHAR(50) NOT NULL REFERENCES assets(blkrock_id),
    
    -- Position Details
    par_amount DECIMAL(18,2) NOT NULL,
    purchase_price DECIMAL(8,6), -- as % of par
    purchase_date DATE,
    sale_date DATE,
    sale_price DECIMAL(8,6),
    
    -- Status
    position_status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, SOLD, DEFAULTED
    
    PRIMARY KEY (deal_id, blkrock_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- COMPLIANCE AND TESTING
-- =============================================================================

-- Compliance tests (converted from TestThresholds type)
CREATE TABLE compliance_tests (
    test_id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL UNIQUE,
    test_category VARCHAR(50), -- CONCENTRATION, QUALITY, DIVERSITY, etc.
    
    -- Test Configuration
    test_formula TEXT, -- Filter expression for test
    threshold_value DECIMAL(10,6),
    threshold_type VARCHAR(20), -- MAX, MIN, EXACT
    
    -- Test Metadata
    test_description TEXT,
    regulatory_source VARCHAR(100),
    
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compliance test results by date
CREATE TABLE compliance_test_results (
    result_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    test_id INTEGER NOT NULL REFERENCES compliance_tests(test_id),
    test_date DATE NOT NULL,
    
    -- Test Results
    calculated_value DECIMAL(18,6),
    threshold_value DECIMAL(18,6),
    pass_fail BOOLEAN,
    
    -- Supporting Data
    numerator DECIMAL(18,6),
    denominator DECIMAL(18,6),
    test_comments TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, test_id, test_date)
);

-- =============================================================================
-- MARKET DATA AND CURVES
-- =============================================================================

-- Interest rate curves
CREATE TABLE yield_curves (
    curve_id SERIAL PRIMARY KEY,
    curve_name VARCHAR(50) NOT NULL, -- USD_LIBOR, USD_SOFR, etc.
    curve_date DATE NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(curve_name, curve_date)
);

-- Yield curve points
CREATE TABLE yield_curve_points (
    point_id SERIAL PRIMARY KEY,
    curve_id INTEGER NOT NULL REFERENCES yield_curves(curve_id) ON DELETE CASCADE,
    tenor_months INTEGER NOT NULL,
    rate DECIMAL(10,8) NOT NULL,
    
    UNIQUE(curve_id, tenor_months)
);

-- Asset pricing/market values
CREATE TABLE asset_pricing (
    pricing_id SERIAL PRIMARY KEY,
    blkrock_id VARCHAR(50) NOT NULL REFERENCES assets(blkrock_id),
    pricing_date DATE NOT NULL,
    
    -- Prices
    bid_price DECIMAL(8,6),
    ask_price DECIMAL(8,6),
    mid_price DECIMAL(8,6),
    
    -- Source
    pricing_source VARCHAR(50), -- BLOOMBERG, MARKIT, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blkrock_id, pricing_date, pricing_source)
);

-- =============================================================================
-- SCENARIO AND SIMULATION
-- =============================================================================

-- Monte Carlo scenarios (for risk modeling)
CREATE TABLE simulation_scenarios (
    scenario_id SERIAL PRIMARY KEY,
    simulation_name VARCHAR(100) NOT NULL,
    scenario_number INTEGER NOT NULL,
    
    -- Scenario Parameters
    base_case_cdr DECIMAL(6,4), -- Cumulative Default Rate
    base_case_cpr DECIMAL(6,4), -- Constant Prepayment Rate
    recovery_rate DECIMAL(5,4),
    correlation_factor DECIMAL(5,4),
    
    -- Paths (JSON array of period values)
    default_path JSONB,
    prepay_path JSONB,
    rate_path JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(simulation_name, scenario_number)
);

-- Simulation results
CREATE TABLE simulation_results (
    result_id SERIAL PRIMARY KEY,
    scenario_id INTEGER NOT NULL REFERENCES simulation_scenarios(scenario_id),
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    tranche_id VARCHAR(50) REFERENCES clo_tranches(tranche_id),
    
    -- Results
    irr DECIMAL(8,6),
    average_life DECIMAL(6,4),
    duration DECIMAL(6,4),
    total_losses DECIMAL(18,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- REFERENCE DATA
-- =============================================================================

-- Industry classifications
CREATE TABLE industry_classifications (
    industry_id SERIAL PRIMARY KEY,
    agency VARCHAR(20) NOT NULL, -- MOODY, SP
    industry_code VARCHAR(20),
    industry_name VARCHAR(100) NOT NULL,
    parent_industry_id INTEGER REFERENCES industry_classifications(industry_id),
    
    UNIQUE(agency, industry_code)
);

-- Rating scales
CREATE TABLE rating_scales (
    rating_id SERIAL PRIMARY KEY,
    agency VARCHAR(20) NOT NULL, -- MOODY, SP, FITCH
    rating_symbol VARCHAR(10) NOT NULL,
    rating_numeric INTEGER NOT NULL,
    warf_factor INTEGER, -- Weighted Average Rating Factor
    
    UNIQUE(agency, rating_symbol)
);

-- Holidays calendar
CREATE TABLE holidays (
    holiday_date DATE PRIMARY KEY,
    holiday_name VARCHAR(100),
    country_code VARCHAR(3) DEFAULT 'US'
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Asset indexes
CREATE INDEX idx_assets_issuer ON assets(issuer_name);
CREATE INDEX idx_assets_maturity ON assets(maturity);
CREATE INDEX idx_assets_ratings ON assets(mdy_rating, sp_rating);
CREATE INDEX idx_assets_industry ON assets(mdy_industry, sp_industry);
CREATE INDEX idx_assets_country ON assets(country);
CREATE INDEX idx_assets_flags ON assets USING GIN (flags);

-- Cash flow indexes
CREATE INDEX idx_cash_flows_payment_date ON asset_cash_flows(payment_date);
CREATE INDEX idx_cash_flows_asset_period ON asset_cash_flows(blkrock_id, period_number);

-- History indexes
CREATE INDEX idx_asset_history_date ON asset_history(blkrock_id, history_date);
CREATE INDEX idx_asset_history_property ON asset_history(property_name, history_date);

-- Deal indexes
CREATE INDEX idx_deal_assets_deal ON deal_assets(deal_id);
CREATE INDEX idx_deal_assets_status ON deal_assets(position_status);

-- Compliance indexes
CREATE INDEX idx_compliance_results_deal_date ON compliance_test_results(deal_id, test_date);
CREATE INDEX idx_compliance_results_pass_fail ON compliance_test_results(pass_fail, test_date);

-- Pricing indexes
CREATE INDEX idx_asset_pricing_date ON asset_pricing(pricing_date);
CREATE INDEX idx_yield_curves_date ON yield_curves(curve_date);

-- =============================================================================
-- TRIGGERS FOR AUDIT AND CONSISTENCY
-- =============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to tables with updated_at
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clo_deals_updated_at BEFORE UPDATE ON clo_deals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cash_flows_updated_at BEFORE UPDATE ON asset_cash_flows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cash flow total calculation trigger
CREATE OR REPLACE FUNCTION calculate_total_cash_flow()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_cash_flow = COALESCE(NEW.interest_payment, 0) + 
                         COALESCE(NEW.scheduled_principal, 0) + 
                         COALESCE(NEW.unscheduled_principal, 0) + 
                         COALESCE(NEW.recoveries, 0);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_cash_flow_total BEFORE INSERT OR UPDATE ON asset_cash_flows
    FOR EACH ROW EXECUTE FUNCTION calculate_total_cash_flow();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Current portfolio view
CREATE VIEW v_current_portfolio AS
SELECT 
    a.blkrock_id,
    a.issue_name,
    a.issuer_name,
    da.par_amount,
    a.coupon,
    a.maturity,
    a.mdy_rating,
    a.sp_rating,
    a.mdy_industry,
    a.country,
    da.deal_id,
    da.position_status
FROM assets a
JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
WHERE da.position_status = 'ACTIVE';

-- Portfolio summary by rating
CREATE VIEW v_portfolio_by_rating AS
SELECT 
    deal_id,
    mdy_rating,
    COUNT(*) as asset_count,
    SUM(par_amount) as total_par,
    AVG(coupon) as avg_coupon
FROM v_current_portfolio
WHERE mdy_rating IS NOT NULL
GROUP BY deal_id, mdy_rating;

-- Cash flow summary
CREATE VIEW v_cash_flow_summary AS
SELECT 
    cf.blkrock_id,
    cf.payment_date,
    SUM(cf.interest_payment) as total_interest,
    SUM(cf.scheduled_principal + cf.unscheduled_principal) as total_principal,
    SUM(cf.total_cash_flow) as total_cash_flow
FROM asset_cash_flows cf
GROUP BY cf.blkrock_id, cf.payment_date;

-- =============================================================================
-- MAGNETAR WATERFALL TABLES (Mag 6-17 Implementation)
-- =============================================================================

-- Magnetar-specific waterfall configurations
CREATE TABLE mag_waterfall_configurations (
    config_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    mag_version VARCHAR(10) NOT NULL, -- MAG_6, MAG_7, etc.
    
    -- Mag-specific parameters
    equity_hurdle_rate DECIMAL(6,4), -- Equity return hurdle (e.g., 0.12 = 12%)
    equity_catch_up_rate DECIMAL(6,4), -- Catch-up rate above hurdle
    management_fee_sharing_pct DECIMAL(5,4), -- % of incentive fee to manager
    
    -- Turbo features
    turbo_threshold_oc_ratio DECIMAL(8,6), -- OC ratio triggering turbo
    turbo_threshold_ic_ratio DECIMAL(8,6), -- IC ratio triggering turbo
    
    -- Performance metrics
    minimum_equity_irr DECIMAL(6,4), -- Minimum equity IRR requirement
    performance_test_frequency VARCHAR(20) DEFAULT 'QUARTERLY', -- Test frequency
    
    -- Reinvestment overlay
    reinvestment_overlay_rate DECIMAL(6,4), -- Additional reinvestment fee
    reinvestment_overlay_cap DECIMAL(18,2), -- Cap on overlay fees
    
    -- Call protection overrides
    call_protection_equity_threshold DECIMAL(8,6), -- Equity threshold for call override
    
    -- Distribution controls
    distribution_stopper_covenant VARCHAR(100), -- Covenant triggering stopper
    distribution_stopper_threshold DECIMAL(8,6), -- Threshold value
    
    -- Features enabled for this deal (JSON array)
    enabled_features JSON, -- List of MagPaymentFeature values
    
    -- Effective dates
    effective_date DATE NOT NULL,
    amendment_number INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    CONSTRAINT unique_mag_config UNIQUE (deal_id, mag_version, effective_date)
);

-- Performance metrics calculation for Magnetar deals
CREATE TABLE mag_performance_metrics (
    metric_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    calculation_date DATE NOT NULL,
    
    -- Equity performance
    equity_irr DECIMAL(8,6), -- Annualized equity IRR
    equity_moic DECIMAL(6,4), -- Multiple of invested capital
    cumulative_equity_distributions DECIMAL(18,2),
    
    -- Hurdle calculations  
    hurdle_achievement_pct DECIMAL(6,4), -- % of hurdle achieved
    excess_return_above_hurdle DECIMAL(8,6), -- Return above hurdle rate
    catch_up_provision_activated BOOLEAN DEFAULT FALSE,
    
    -- Fee calculations
    base_management_fee_ytd DECIMAL(18,2),
    incentive_fee_accrued DECIMAL(18,2),
    incentive_fee_paid_ytd DECIMAL(18,2),
    
    -- Performance tests
    oc_test_buffer DECIMAL(8,6), -- Cushion above minimum OC
    ic_test_buffer DECIMAL(8,6), -- Cushion above minimum IC
    portfolio_yield_spread DECIMAL(8,6), -- Spread above funding cost
    
    -- Calculation metadata
    calculation_method VARCHAR(50), -- ACTUAL, PROJECTED, STRESS_TEST
    calculation_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_mag_metrics UNIQUE (deal_id, calculation_date)
);

-- Tranche mappings for dynamic waterfall construction
CREATE TABLE tranche_mappings (
    mapping_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    tranche_id VARCHAR(50) NOT NULL REFERENCES clo_tranches(tranche_id),
    
    -- Tranche classification
    tranche_type VARCHAR(30) NOT NULL, -- TrancheType enum
    payment_category VARCHAR(30) NOT NULL, -- PaymentCategory enum
    
    -- Payment priority within category
    category_rank INTEGER NOT NULL DEFAULT 1, -- 1 = highest priority
    
    -- Payment step mapping
    interest_step VARCHAR(50), -- Mapped waterfall step for interest
    principal_step VARCHAR(50), -- Mapped waterfall step for principal
    
    -- Special characteristics
    is_deferrable BOOLEAN DEFAULT FALSE,
    is_pik_eligible BOOLEAN DEFAULT FALSE,
    supports_turbo BOOLEAN DEFAULT TRUE,
    
    -- Effective dates
    effective_date DATE NOT NULL,
    expiration_date DATE, -- NULL for permanent
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_tranche_mapping UNIQUE (deal_id, tranche_id, effective_date)
);

-- Waterfall structure templates for different tranche configurations
CREATE TABLE waterfall_structures (
    structure_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    structure_name VARCHAR(100) NOT NULL UNIQUE,
    
    -- Structure metadata
    min_tranches INTEGER NOT NULL,
    max_tranches INTEGER NOT NULL,
    typical_tranches INTEGER NOT NULL,
    
    -- Structure definition (JSON)
    payment_sequence JSON NOT NULL, -- Ordered list of payment categories
    category_rules JSON NOT NULL, -- Rules for each category
    
    -- Market and regulatory info
    jurisdiction VARCHAR(20),
    typical_use_case TEXT,
    regulatory_notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE assets IS 'Core asset table converted from VBA Asset.cls - stores individual financial instruments';
COMMENT ON TABLE asset_cash_flows IS 'Asset cash flow projections converted from SimpleCashflow.cls';
COMMENT ON TABLE clo_deals IS 'CLO deal master data with key dates and parameters';
COMMENT ON TABLE compliance_tests IS 'Portfolio compliance tests with thresholds and formulas';
COMMENT ON TABLE compliance_test_results IS 'Historical compliance test results by deal and date';

COMMENT ON COLUMN assets.flags IS 'JSON object storing asset classification flags (pik_asset, default_asset, cov_lite, etc.)';
COMMENT ON COLUMN asset_cash_flows.period_number IS 'Sequential period number for asset cash flow projections';
COMMENT ON COLUMN compliance_tests.test_formula IS 'Filter expression using Asset.apply_filter() syntax';