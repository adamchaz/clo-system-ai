-- CLO Waterfall Schema Extension
-- Adds waterfall logic tables to support payment sequencing and distribution

-- =============================================================================
-- WATERFALL CONFIGURATION AND EXECUTION TABLES
-- =============================================================================

-- Waterfall configuration by deal
CREATE TABLE waterfall_configurations (
    config_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    
    -- Configuration metadata
    config_name VARCHAR(100) NOT NULL,
    effective_date DATE NOT NULL,
    version INTEGER DEFAULT 1,
    
    -- Waterfall rules (JSON structure)
    payment_rules TEXT NOT NULL, -- JSON string of waterfall steps and priorities
    
    -- Reserve account requirements
    interest_reserve_target DECIMAL(18,2),
    interest_reserve_cap DECIMAL(18,2),
    
    -- Management fee rates (annual basis)
    senior_mgmt_fee_rate DECIMAL(6,4), -- e.g., 0.004 = 40bps
    junior_mgmt_fee_rate DECIMAL(6,4),
    incentive_fee_rate DECIMAL(6,4),
    incentive_hurdle_rate DECIMAL(6,4),
    
    -- Trustee and administrative fees (annual)
    trustee_fee_annual DECIMAL(10,2),
    admin_fee_cap DECIMAL(10,2),
    
    -- Trigger events
    enable_oc_tests BOOLEAN DEFAULT TRUE,
    enable_ic_tests BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, effective_date, version)
);

-- Waterfall execution records by payment date
CREATE TABLE waterfall_executions (
    execution_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    payment_date DATE NOT NULL,
    config_id INTEGER REFERENCES waterfall_configurations(config_id),
    
    -- Available cash
    collection_amount DECIMAL(18,2) NOT NULL,
    beginning_cash DECIMAL(18,2) DEFAULT 0,
    total_available DECIMAL(18,2) NOT NULL,
    
    -- Reserve account balances
    interest_reserve_beginning DECIMAL(18,2) DEFAULT 0,
    interest_reserve_ending DECIMAL(18,2) DEFAULT 0,
    
    -- Final residuals
    remaining_cash DECIMAL(18,2) DEFAULT 0,
    
    -- Trigger test results
    oc_test_pass BOOLEAN,
    ic_test_pass BOOLEAN,
    
    -- Execution status
    execution_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, COMPLETED, FAILED
    execution_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, payment_date)
);

-- Individual payments within waterfall execution
CREATE TABLE waterfall_payments (
    payment_id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES waterfall_executions(execution_id) ON DELETE CASCADE,
    
    -- Payment details
    payment_step VARCHAR(30) NOT NULL, -- TRUSTEE_FEES, CLASS_A_INTEREST, etc.
    step_sequence INTEGER NOT NULL,    -- Order within waterfall
    payment_priority VARCHAR(20),      -- SENIOR, SUBORDINATED, RESIDUAL
    
    -- Amounts
    amount_due DECIMAL(18,2) NOT NULL,
    amount_paid DECIMAL(18,2) NOT NULL,
    amount_deferred DECIMAL(18,2) DEFAULT 0,
    
    -- Payment targets (tranche, account, etc.)
    target_tranche_id VARCHAR(50) REFERENCES clo_tranches(tranche_id),
    target_account VARCHAR(50), -- COLLECTION, INTEREST_RESERVE, TRUSTEE_PAYABLE, etc.
    
    -- Calculation details
    calculation_base DECIMAL(18,2), -- Base amount for rate calculations
    payment_rate DECIMAL(8,6),      -- Rate applied (for fees)
    
    -- Notes
    payment_notes TEXT,
    
    UNIQUE(execution_id, step_sequence)
);

-- =============================================================================
-- ACCOUNT BALANCES AND RESERVES
-- =============================================================================

-- Account balances by deal and date
CREATE TABLE account_balances (
    balance_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    account_name VARCHAR(50) NOT NULL, -- COLLECTION, INTEREST_RESERVE, PRINCIPAL_RESERVE, etc.
    balance_date DATE NOT NULL,
    
    -- Balance amounts
    beginning_balance DECIMAL(18,2) DEFAULT 0,
    deposits DECIMAL(18,2) DEFAULT 0,
    withdrawals DECIMAL(18,2) DEFAULT 0,
    ending_balance DECIMAL(18,2) DEFAULT 0,
    
    -- Account metadata
    account_type VARCHAR(30), -- OPERATING, RESERVE, PAYABLE, etc.
    currency VARCHAR(3) DEFAULT 'USD',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, account_name, balance_date)
);

-- =============================================================================
-- TRIGGER TESTS AND RATIOS
-- =============================================================================

-- Over-collateralization and Interest Coverage test results
CREATE TABLE coverage_test_results (
    test_result_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    test_date DATE NOT NULL,
    
    -- Over-collateralization tests
    class_a_oc_ratio DECIMAL(8,6),
    class_a_oc_threshold DECIMAL(8,6),
    class_a_oc_pass BOOLEAN,
    
    class_b_oc_ratio DECIMAL(8,6),
    class_b_oc_threshold DECIMAL(8,6), 
    class_b_oc_pass BOOLEAN,
    
    class_c_oc_ratio DECIMAL(8,6),
    class_c_oc_threshold DECIMAL(8,6),
    class_c_oc_pass BOOLEAN,
    
    class_d_oc_ratio DECIMAL(8,6),
    class_d_oc_threshold DECIMAL(8,6),
    class_d_oc_pass BOOLEAN,
    
    -- Interest coverage tests
    class_a_ic_ratio DECIMAL(8,6),
    class_a_ic_threshold DECIMAL(8,6),
    class_a_ic_pass BOOLEAN,
    
    class_b_ic_ratio DECIMAL(8,6),
    class_b_ic_threshold DECIMAL(8,6),
    class_b_ic_pass BOOLEAN,
    
    class_c_ic_ratio DECIMAL(8,6),
    class_c_ic_threshold DECIMAL(8,6),
    class_c_ic_pass BOOLEAN,
    
    class_d_ic_ratio DECIMAL(8,6),
    class_d_ic_threshold DECIMAL(8,6),
    class_d_ic_pass BOOLEAN,
    
    -- Overall test results
    all_oc_tests_pass BOOLEAN,
    all_ic_tests_pass BOOLEAN,
    principal_payments_allowed BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, test_date)
);

-- =============================================================================
-- PAYMENT SCHEDULES AND PROJECTIONS
-- =============================================================================

-- Scheduled payment dates for deal
CREATE TABLE payment_schedules (
    schedule_id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL REFERENCES clo_deals(deal_id),
    
    payment_date DATE NOT NULL,
    payment_type VARCHAR(20) NOT NULL, -- REGULAR, OPTIONAL_REDEMPTION, MATURITY
    
    -- Date calculations
    interest_determination_date DATE,
    collection_period_start DATE,
    collection_period_end DATE,
    
    -- Payment status
    payment_status VARCHAR(20) DEFAULT 'SCHEDULED', -- SCHEDULED, EXECUTED, SKIPPED
    actual_payment_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(deal_id, payment_date)
);

-- =============================================================================
-- INDEXES FOR WATERFALL PERFORMANCE
-- =============================================================================

-- Waterfall execution indexes
CREATE INDEX idx_waterfall_executions_deal_date ON waterfall_executions(deal_id, payment_date);
CREATE INDEX idx_waterfall_executions_status ON waterfall_executions(execution_status);

-- Waterfall payments indexes
CREATE INDEX idx_waterfall_payments_execution ON waterfall_payments(execution_id);
CREATE INDEX idx_waterfall_payments_step ON waterfall_payments(payment_step);
CREATE INDEX idx_waterfall_payments_tranche ON waterfall_payments(target_tranche_id);

-- Account balances indexes
CREATE INDEX idx_account_balances_deal_date ON account_balances(deal_id, balance_date);
CREATE INDEX idx_account_balances_account ON account_balances(account_name, balance_date);

-- Coverage tests indexes
CREATE INDEX idx_coverage_tests_deal_date ON coverage_test_results(deal_id, test_date);
CREATE INDEX idx_coverage_tests_pass ON coverage_test_results(all_oc_tests_pass, all_ic_tests_pass);

-- Payment schedule indexes
CREATE INDEX idx_payment_schedules_deal ON payment_schedules(deal_id, payment_date);
CREATE INDEX idx_payment_schedules_status ON payment_schedules(payment_status);

-- =============================================================================
-- VIEWS FOR WATERFALL REPORTING
-- =============================================================================

-- Current waterfall summary by deal
CREATE VIEW v_current_waterfall_summary AS
SELECT 
    we.deal_id,
    we.payment_date,
    we.collection_amount,
    we.total_available,
    we.remaining_cash,
    we.oc_test_pass,
    we.ic_test_pass,
    COUNT(wp.payment_id) as total_payments,
    SUM(wp.amount_paid) as total_distributed,
    SUM(wp.amount_deferred) as total_deferred
FROM waterfall_executions we
LEFT JOIN waterfall_payments wp ON we.execution_id = wp.execution_id
GROUP BY we.execution_id, we.deal_id, we.payment_date, 
         we.collection_amount, we.total_available, we.remaining_cash,
         we.oc_test_pass, we.ic_test_pass;

-- Payment summary by step and tranche
CREATE VIEW v_payment_summary_by_step AS
SELECT 
    wp.payment_step,
    wp.target_tranche_id,
    ct.tranche_name,
    COUNT(*) as payment_count,
    SUM(wp.amount_due) as total_due,
    SUM(wp.amount_paid) as total_paid,
    SUM(wp.amount_deferred) as total_deferred,
    AVG(wp.amount_paid / NULLIF(wp.amount_due, 0)) as payment_ratio
FROM waterfall_payments wp
LEFT JOIN clo_tranches ct ON wp.target_tranche_id = ct.tranche_id
GROUP BY wp.payment_step, wp.target_tranche_id, ct.tranche_name;

-- Monthly collections and distributions
CREATE VIEW v_monthly_cash_flow AS
SELECT 
    we.deal_id,
    DATE_TRUNC('month', we.payment_date) as payment_month,
    SUM(we.collection_amount) as total_collections,
    SUM(we.total_available) as total_available,
    SUM(we.remaining_cash) as total_residual,
    COUNT(*) as payment_count
FROM waterfall_executions we
WHERE we.execution_status = 'COMPLETED'
GROUP BY we.deal_id, DATE_TRUNC('month', we.payment_date);

-- =============================================================================
-- TRIGGERS FOR WATERFALL CONSISTENCY
-- =============================================================================

-- Update tranche balances after principal payments
CREATE OR REPLACE FUNCTION update_tranche_balance_after_payment()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.payment_step LIKE '%_PRINCIPAL' AND NEW.target_tranche_id IS NOT NULL THEN
        UPDATE clo_tranches 
        SET current_balance = current_balance - NEW.amount_paid,
            updated_at = CURRENT_TIMESTAMP
        WHERE tranche_id = NEW.target_tranche_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_update_tranche_balance 
    AFTER INSERT OR UPDATE ON waterfall_payments
    FOR EACH ROW 
    EXECUTE FUNCTION update_tranche_balance_after_payment();

-- Calculate total available cash
CREATE OR REPLACE FUNCTION calculate_total_available()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_available = COALESCE(NEW.collection_amount, 0) + COALESCE(NEW.beginning_cash, 0);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_calculate_total_available 
    BEFORE INSERT OR UPDATE ON waterfall_executions
    FOR EACH ROW 
    EXECUTE FUNCTION calculate_total_available();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE waterfall_configurations IS 'Waterfall payment rules and configuration by CLO deal';
COMMENT ON TABLE waterfall_executions IS 'Historical record of waterfall executions by payment date';
COMMENT ON TABLE waterfall_payments IS 'Individual payments within waterfall showing priority and amounts';
COMMENT ON TABLE coverage_test_results IS 'Over-collateralization and interest coverage test results by date';
COMMENT ON TABLE account_balances IS 'Account balances for collection, reserve, and payable accounts';

COMMENT ON COLUMN waterfall_configurations.payment_rules IS 'JSON array defining waterfall steps and priorities';
COMMENT ON COLUMN waterfall_payments.payment_step IS 'Waterfall step (TRUSTEE_FEES, CLASS_A_INTEREST, etc.)';
COMMENT ON COLUMN waterfall_payments.step_sequence IS 'Execution order within waterfall (1=first)';
COMMENT ON COLUMN coverage_test_results.principal_payments_allowed IS 'TRUE if OC/IC tests allow normal principal payments';