-- ===============================================
-- Fixed MAG17 Concentration Test Thresholds
-- Migration 004: Proper foreign key relationships
-- ===============================================

-- First, ensure the tables exist (in case previous migration wasn't run)
CREATE TABLE IF NOT EXISTS concentration_test_definitions (
    test_id SERIAL PRIMARY KEY,
    test_number INTEGER UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_description TEXT,
    test_category VARCHAR(50) NOT NULL,
    result_type VARCHAR(20) NOT NULL DEFAULT 'percentage',
    default_threshold NUMERIC(18,6),
    calculation_method TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deal_concentration_thresholds (
    id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL,
    test_id INTEGER NOT NULL REFERENCES concentration_test_definitions(test_id) ON DELETE CASCADE,
    threshold_value NUMERIC(18,6) NOT NULL,
    effective_date DATE NOT NULL DEFAULT '2016-03-23',
    expiry_date DATE NULL,
    mag_version VARCHAR(10),
    rating_agency VARCHAR(20),
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(deal_id, test_id, effective_date)
);

CREATE TABLE IF NOT EXISTS concentration_test_executions (
    id SERIAL PRIMARY KEY,
    deal_id VARCHAR(50) NOT NULL,
    test_id INTEGER NOT NULL REFERENCES concentration_test_definitions(test_id),
    analysis_date DATE NOT NULL,
    threshold_used NUMERIC(18,6) NOT NULL,
    calculated_value NUMERIC(18,6) NOT NULL,
    numerator NUMERIC(18,6),
    denominator NUMERIC(18,6),
    pass_fail_status VARCHAR(10) NOT NULL,
    threshold_source VARCHAR(20) NOT NULL,
    excess_amount NUMERIC(18,6),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clear existing data to ensure clean state
DELETE FROM deal_concentration_thresholds WHERE deal_id = 'MAG17';
DELETE FROM concentration_test_definitions;

-- ========================================
-- Insert Complete VBA Test Definitions (Key Tests Only)
-- ========================================
INSERT INTO concentration_test_definitions (test_number, test_name, test_category, result_type, default_threshold, test_description) VALUES
-- Asset Quality Tests
(1, 'Limitation on Senior Secured Loans', 'asset_quality', 'percentage', 0.9, 'Minimum percentage of senior secured loans - Pass if result > 90.0%'),
(2, 'Limitation on non Senior Secured Loans', 'asset_quality', 'percentage', 0.1, 'Maximum percentage of non-senior secured loans - Pass if result < 10.0%'),
(3, 'Limitation on Obligor', 'asset_quality', 'percentage', 0.02, 'Maximum percentage per obligor - Pass if result < 2.0%'),
(4, 'Limitation on DIP Obligor', 'asset_quality', 'percentage', 0.025, 'Maximum percentage for DIP obligor - Pass if result < 2.5%'),
(5, 'Limitation on Non Senior Secured Obligor', 'asset_quality', 'percentage', 0.02, 'Maximum percentage for non-senior secured obligor - Pass if result < 2.0%'),
(6, 'Limitation on Caa Loans', 'asset_quality', 'percentage', 0.02, 'Maximum percentage of Caa-rated loans - Pass if result < 2.0%'),
(7, 'Limitation on CCC Loans', 'asset_quality', 'percentage', 0.075, 'Maximum percentage of CCC-rated loans - Pass if result < 7.5%'),
(8, 'Limitation on Assets Pay Less Frequently Quarterly', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of assets paying less than quarterly - Pass if result < 5.0%'),
(9, 'Limitation on Fixed Rate Obligations', 'asset_quality', 'percentage', 0.025, 'Maximum percentage of fixed rate obligations - Pass if result < 2.5%'),
(10, 'Limitation on Current Pay Obligations', 'asset_quality', 'percentage', 0.025, 'Maximum percentage of current pay obligations - Pass if result < 2.5%'),
(11, 'Limitation on DIP Obligations', 'asset_quality', 'percentage', 0.075, 'Maximum percentage of DIP obligations - Pass if result < 7.5%'),
(12, 'Limitation on Unfunded Commitments', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of unfunded commitments - Pass if result < 5.0%'),
(13, 'Limitation on Participation Int', 'asset_quality', 'percentage', 0.15, 'Maximum percentage of participation interests - Pass if result < 15.0%'),
(14, 'Limitation on SP Criteria', 'asset_quality', 'percentage', 0.15, 'Maximum percentage for S&P criteria - Pass if result < 15.0%'),

-- Geographic Concentration Tests
(15, 'Limitation on Country Not USA', 'geographic', 'percentage', 0.2, 'Maximum percentage for non-USA countries - Pass if result < 20.0%'),
(16, 'Limitation on Country Canada Tax Jurisdiction', 'geographic', 'percentage', 0.125, 'Maximum percentage for Canada tax jurisdiction - Pass if result < 12.5%'),
(17, 'Limitation on Country Canada', 'geographic', 'percentage', 0.125, 'Maximum percentage for Canada - Pass if result < 12.5%'),
(18, 'Limitation on Non Emerging Market', 'geographic', 'percentage', 0.125, 'Maximum percentage for non-emerging markets - Pass if result < 12.5%'),
(19, 'Limitation on Countries Not US Canada UK', 'geographic', 'percentage', 0.1, 'Maximum percentage for countries other than US/Canada/UK - Pass if result < 10.0%'),
(20, 'Limitation on Group Countries', 'geographic', 'percentage', 0.15, 'Maximum percentage for group countries - Pass if result < 15.0%'),

-- Industry Concentration Tests
(25, 'Limitation on SP Industry Classification', 'industry', 'percentage', 0.075, 'Maximum percentage for S&P industry classification - Pass if result < 7.5%'),
(26, 'SP Industry - Oil Gas', 'industry', 'percentage', 0.1, 'Maximum percentage for Oil & Gas industry - Pass if result < 10.0%'),
(27, 'SP Industry - Telecom', 'industry', 'percentage', 0.12, 'Maximum percentage for Telecom industry - Pass if result < 12.0%'),
(28, 'SP Industry - Automotive', 'industry', 'percentage', 0.15, 'Maximum percentage for Automotive industry - Pass if result < 15.0%'),

-- Asset Type Tests
(29, 'Limitation on Bridge Loans', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of bridge loans - Pass if result < 5.0%'),
(30, 'Limitation on Cov Lite', 'asset_quality', 'percentage', 0.6, 'Maximum percentage of covenant lite loans - Pass if result < 60.0%'),
(31, 'Limitation on Deferrable Securities', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of deferrable securities - Pass if result < 5.0%'),
(32, 'Limitation on Letter of Credit', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of letter of credit - Pass if result < 5.0%'),
(33, 'Limitation on Long Dated', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of long dated assets - Pass if result < 5.0%'),
(34, 'Limitation on Unsecured', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of unsecured assets - Pass if result < 5.0%'),
(35, 'Limitation on Swap Non Discount', 'asset_quality', 'percentage', 0.05, 'Maximum percentage of swap non discount - Pass if result < 5.0%'),
(36, 'Limitation on Facility Size', 'asset_quality', 'percentage', 0.07, 'Maximum percentage per facility size - Pass if result < 7.0%'),

-- Portfolio Metrics Tests
(88, 'Weighted Average Spread', 'portfolio_metrics', 'basis_points', 425.0, 'Minimum weighted average spread - Pass if result > 425 bps'),
(89, 'Weighted Average Spread MAG14', 'portfolio_metrics', 'basis_points', 425.0, 'Minimum weighted average spread MAG14 - Pass if result > 425 bps'),
(90, 'Weighted Average Spread MAG06', 'portfolio_metrics', 'basis_points', 400.0, 'Minimum weighted average spread MAG06 - Pass if result > 400 bps'),
(91, 'Weighted Average Recovery Rate', 'portfolio_metrics', 'percentage', 0.47, 'Minimum weighted average recovery rate - Pass if result > 47.0%'),
(92, 'Weighted Average Coupon', 'portfolio_metrics', 'percentage', 0.07, 'Minimum weighted average coupon - Pass if result >= 7.0%'),
(93, 'Weighted Average Life', 'portfolio_metrics', 'years', 6.0, 'Maximum weighted average life - Pass if result < 6.0 years'),
(94, 'Weighted Average Rating Factor', 'portfolio_metrics', 'rating_factor', 2900.0, 'Maximum weighted average rating factor - Pass if result < 2900'),
(95, 'Weighted Average Rating Factor MAG14', 'portfolio_metrics', 'rating_factor', 2900.0, 'Maximum weighted average rating factor MAG14 - Pass if result < 2900');

-- ========================================
-- Insert MAG17-Specific Threshold Overrides (using proper test_id references)
-- ========================================

-- Insert MAG17 overrides using test_number to test_id lookup
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 
    'MAG17',
    ctd.test_id,
    threshold_data.threshold_value,
    '2016-03-23'::DATE,
    NULL,
    'MAG17',
    threshold_data.notes,
    1,
    CURRENT_TIMESTAMP
FROM concentration_test_definitions ctd
JOIN (VALUES
    -- (test_number, threshold_value, notes)
    (1, 0.9, 'Senior Secured Loans - VBA verified 90% - CRITICAL FIX'),
    (2, 0.1, 'Non-Senior Secured Loans maximum 10%'),
    (3, 0.02, 'Single obligor maximum 2%'),
    (4, 0.025, 'DIP obligor maximum 2.5%'),
    (5, 0.02, 'Non-senior secured obligor maximum 2%'),
    (6, 0.02, 'Caa loans maximum 2%'),
    (7, 0.075, 'CCC loans maximum 7.5% - matches existing system'),
    (8, 0.05, 'Assets paying less than quarterly maximum 5%'),
    (15, 0.2, 'Non-USA country exposure maximum 20%'),
    (30, 0.6, 'Covenant lite maximum 60%'),
    (91, 0.47, 'Weighted average recovery rate minimum 47%'),
    (92, 0.07, 'Weighted average coupon minimum 7%')
) AS threshold_data(test_number, threshold_value, notes) ON ctd.test_number = threshold_data.test_number;

-- ========================================
-- Create Performance Indexes
-- ========================================
CREATE INDEX IF NOT EXISTS idx_concentration_test_definitions_test_number ON concentration_test_definitions(test_number);
CREATE INDEX IF NOT EXISTS idx_concentration_test_definitions_category ON concentration_test_definitions(test_category);
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_deal_test ON deal_concentration_thresholds(deal_id, test_id);
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_effective_date ON deal_concentration_thresholds(effective_date);
CREATE INDEX IF NOT EXISTS idx_concentration_test_executions_deal_date ON concentration_test_executions(deal_id, analysis_date);

-- ========================================
-- Update sequence values (PostgreSQL)
-- ========================================
SELECT setval('concentration_test_definitions_test_id_seq', (SELECT MAX(test_id) FROM concentration_test_definitions));
SELECT setval('deal_concentration_thresholds_id_seq', (SELECT MAX(id) FROM deal_concentration_thresholds));

-- ========================================
-- Validation Queries
-- ========================================
-- Verify test definitions loaded
SELECT 
    'Test definitions loaded' as status,
    COUNT(*) as count
FROM concentration_test_definitions;

-- Verify MAG17 overrides
SELECT 
    'MAG17 threshold overrides' as status,
    COUNT(*) as count
FROM deal_concentration_thresholds
WHERE deal_id = 'MAG17';

-- Show critical Senior Secured Loans threshold
SELECT 
    'Senior Secured Loans MAG17 Threshold' as test_name,
    CONCAT(dct.threshold_value * 100, '%') as threshold_value,
    'VBA requirement: 90%' as requirement,
    CASE 
        WHEN ABS(dct.threshold_value - 0.9) < 0.0001 THEN 'CORRECT' 
        ELSE 'INCORRECT' 
    END as status
FROM concentration_test_definitions ctd
JOIN deal_concentration_thresholds dct ON ctd.test_id = dct.test_id
WHERE ctd.test_number = 1 AND dct.deal_id = 'MAG17';

COMMIT;