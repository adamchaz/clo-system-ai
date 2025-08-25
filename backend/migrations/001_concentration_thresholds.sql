-- Concentration Test Threshold System Database Schema
-- Migration: 001_concentration_thresholds
-- Date: 2025-08-25
-- Description: Database-driven concentration test thresholds per deal

-- ========================================
-- 1. Master Test Definitions Table
-- ========================================
CREATE TABLE concentration_test_definitions (
    test_id SERIAL PRIMARY KEY,
    test_number INTEGER UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_description TEXT,
    test_category VARCHAR(50) NOT NULL, -- 'obligor', 'industry', 'rating', 'geographic', 'asset_type'
    result_type VARCHAR(20) NOT NULL, -- 'percentage', 'absolute', 'rating_factor', 'years'
    default_threshold NUMERIC(18,6),
    calculation_method TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 2. Deal-Specific Threshold Overrides
-- ========================================
CREATE TABLE deal_concentration_thresholds (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES clo_deals(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES concentration_test_definitions(test_id) ON DELETE CASCADE,
    threshold_value NUMERIC(18,6) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    mag_version VARCHAR(10), -- 'MAG6', 'MAG14', 'MAG17'
    rating_agency VARCHAR(20), -- 'Moodys', 'SP', 'Fitch'
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_deal_test_date UNIQUE(deal_id, test_id, effective_date)
);

-- ========================================
-- 3. Enhanced Test Execution Results
-- ========================================
CREATE TABLE concentration_test_executions (
    id SERIAL PRIMARY KEY,
    deal_id INTEGER NOT NULL REFERENCES clo_deals(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES concentration_test_definitions(test_id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    threshold_used NUMERIC(18,6) NOT NULL,
    calculated_value NUMERIC(18,6) NOT NULL,
    numerator NUMERIC(18,6),
    denominator NUMERIC(18,6),
    pass_fail_status VARCHAR(10) NOT NULL CHECK (pass_fail_status IN ('PASS', 'FAIL', 'N/A')),
    excess_amount NUMERIC(18,6), -- Amount over threshold for failed tests
    threshold_source VARCHAR(20) NOT NULL CHECK (threshold_source IN ('deal', 'default', 'template')),
    comments TEXT,
    execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 4. Performance Indexes
-- ========================================
CREATE INDEX idx_deal_thresholds_lookup ON deal_concentration_thresholds(deal_id, test_id, effective_date DESC);
CREATE INDEX idx_deal_thresholds_effective ON deal_concentration_thresholds(effective_date, expiry_date);
CREATE INDEX idx_test_executions_analysis ON concentration_test_executions(deal_id, analysis_date);
CREATE INDEX idx_test_executions_timestamp ON concentration_test_executions(execution_timestamp DESC);
CREATE INDEX idx_test_definitions_number ON concentration_test_definitions(test_number);
CREATE INDEX idx_test_definitions_category ON concentration_test_definitions(test_category);

-- ========================================
-- 5. Seed Master Test Definitions (VBA TestNum Conversion)
-- ========================================
INSERT INTO concentration_test_definitions (test_number, test_name, test_category, result_type, default_threshold, test_description) VALUES
-- Asset Type Concentration Tests
(1, 'Senior Secured Loans Minimum', 'asset_type', 'percentage', 80.0, 'Minimum percentage of senior secured loans'),
(2, 'Non-Senior Secured Loans Maximum', 'asset_type', 'percentage', 20.0, 'Maximum percentage of non-senior secured loans'),
(7, 'Caa-Rated Assets Maximum', 'rating', 'percentage', 7.5, 'Maximum percentage of Caa-rated assets'),
(8, 'Assets Paying Less Than Quarterly Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of assets paying less frequently than quarterly'),
(9, 'Fixed Rate Assets Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of fixed rate assets'),
(10, 'Current Pay Assets Minimum', 'asset_type', 'percentage', 90.0, 'Minimum percentage of current pay assets'),
(11, 'DIP Assets Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of debtor-in-possession assets'),
(12, 'Unfunded Commitments Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of unfunded commitments'),
(13, 'Participation Interest Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of participation interests'),

-- Obligor Concentration Tests  
(3, '6 Largest Obligors Maximum', 'obligor', 'percentage', 10.0, 'Maximum concentration in 6 largest obligors'),
(4, 'Single Obligor Maximum', 'obligor', 'percentage', 2.0, 'Maximum concentration in single obligor'),
(5, 'Single Obligor DIP Maximum', 'obligor', 'percentage', 2.0, 'Maximum concentration in single DIP obligor'),
(6, 'Single Non-Senior Secured Obligor Maximum', 'obligor', 'percentage', 1.0, 'Maximum concentration in single non-senior secured obligor'),

-- Geographic Concentration Tests
(14, 'Non-US Countries Maximum', 'geographic', 'percentage', 20.0, 'Maximum concentration in non-US countries'),
(15, 'Canada and Tax Jurisdictions Maximum', 'geographic', 'percentage', 5.0, 'Maximum concentration in Canada and tax jurisdictions'),
(16, 'Non-US/Canada/UK Countries Maximum', 'geographic', 'percentage', 5.0, 'Maximum concentration outside US/Canada/UK'),
(17, 'Group I Countries Maximum', 'geographic', 'percentage', 15.0, 'Maximum concentration in Group I countries'),
(18, 'Individual Group I Country Maximum', 'geographic', 'percentage', 5.0, 'Maximum concentration in individual Group I country'),
(19, 'Individual Group I Country Maximum (Alt)', 'geographic', 'percentage', 3.0, 'Alternative limit for individual Group I country'),
(20, 'Group II Countries Maximum', 'geographic', 'percentage', 7.5, 'Maximum concentration in Group II countries'),
(21, 'Individual Group II Country Maximum', 'geographic', 'percentage', 2.5, 'Maximum concentration in individual Group II country'),
(22, 'Group III Countries Maximum', 'geographic', 'percentage', 2.5, 'Maximum concentration in Group III countries'),
(23, 'Individual Group III Country Maximum', 'geographic', 'percentage', 1.0, 'Maximum concentration in individual Group III country'),
(24, 'Tax Jurisdictions Maximum', 'geographic', 'percentage', 2.5, 'Maximum concentration in tax jurisdictions'),

-- Industry Concentration Tests
(25, '4 SP Industry Classifications Maximum', 'industry', 'percentage', 60.0, 'Maximum concentration in 4 S&P industry classifications'),
(26, '2 SP Industry Classifications Maximum', 'industry', 'percentage', 35.0, 'Maximum concentration in 2 S&P industry classifications'),
(27, '1 SP Industry Classification Maximum', 'industry', 'percentage', 12.0, 'Maximum concentration in 1 S&P industry classification'),
(49, '1 Moody Industry Maximum', 'industry', 'percentage', 15.0, 'Maximum concentration in 1 Moody industry'),
(50, '2 Moody Industries Maximum', 'industry', 'percentage', 25.0, 'Maximum concentration in 2 Moody industries'),
(51, '3 Moody Industries Maximum', 'industry', 'percentage', 35.0, 'Maximum concentration in 3 Moody industries'),
(52, '4 Moody Industries Maximum', 'industry', 'percentage', 45.0, 'Maximum concentration in 4 Moody industries'),

-- Asset Quality Tests
(28, 'Bridge Loans Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of bridge loans'),
(29, 'Covenant-Lite Assets Maximum', 'covenant', 'percentage', 7.5, 'Maximum percentage of covenant-lite assets'),
(30, 'Deferrable Securities Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of deferrable securities'),
(40, 'CCC-Rated Obligations Maximum', 'rating', 'percentage', 7.5, 'Maximum percentage of CCC-rated obligations'),
(42, 'Letter of Credit Assets Maximum', 'asset_type', 'percentage', 2.5, 'Maximum percentage of letter of credit backed assets'),
(43, 'Long Dated Assets Maximum', 'asset_type', 'percentage', 7.5, 'Maximum percentage of assets with maturity > 6 years'),
(44, 'Unsecured Loans Maximum', 'asset_type', 'percentage', 5.0, 'Maximum percentage of unsecured loans'),

-- Size and Credit Tests
(31, 'Facility Size Maximum (General)', 'facility', 'percentage', 5.0, 'Maximum percentage from facilities under $50M'),
(53, 'Facility Size Maximum (MAG08)', 'facility', 'percentage', 7.5, 'Maximum percentage from facilities under $100M (MAG08)'),
(41, 'Canada Assets Maximum', 'geographic', 'percentage', 5.0, 'Maximum percentage of Canadian assets'),
(45, 'Swap Non-Discount Maximum', 'asset_type', 'percentage', 2.5, 'Maximum percentage of swap non-discount assets'),
(47, 'Non-Emerging Market Obligors Maximum', 'geographic', 'percentage', 5.0, 'Maximum percentage from non-emerging market obligors'),
(48, 'S&P Criteria Assets Maximum', 'rating', 'percentage', 7.5, 'Maximum percentage not meeting S&P criteria'),

-- Portfolio Quality Metrics (Non-percentage thresholds)
(32, 'Weighted Average Spread Minimum', 'portfolio', 'absolute', 4.0, 'Minimum weighted average spread (percentage points)'),
(33, 'Weighted Average Moody Recovery Rate Minimum', 'portfolio', 'absolute', 40.0, 'Minimum weighted average recovery rate (percentage)'),
(34, 'Weighted Average Coupon Minimum', 'portfolio', 'absolute', 7.0, 'Minimum weighted average coupon (percentage)'),
(35, 'Weighted Average Life Maximum', 'portfolio', 'years', 5.0, 'Maximum weighted average life (years)'),
(36, 'Weighted Average Rating Factor Maximum', 'portfolio', 'rating_factor', 2720, 'Maximum weighted average rating factor'),
(37, 'Moodys Diversity Minimum', 'portfolio', 'absolute', 30, 'Minimum Moodys diversity score'),
(38, 'JROC Test Minimum', 'portfolio', 'absolute', 12.0, 'Minimum junior recovery overlap coverage'),

-- MAG-Specific Tests
(39, 'Weighted Average Spread Minimum (MAG14)', 'portfolio', 'absolute', 4.25, 'Minimum weighted average spread for MAG14'),
(46, 'Weighted Average Spread Minimum (MAG06)', 'portfolio', 'absolute', 4.0, 'Minimum weighted average spread for MAG06'),
(54, 'Weighted Average Rating Factor Maximum (MAG14)', 'portfolio', 'rating_factor', 2900, 'Maximum WARF for MAG14');

-- ========================================
-- 6. Create Default Deal Templates (Optional)
-- ========================================
-- This would be populated based on MAG versions and deal vintages
-- For now, we'll rely on the default_threshold in test definitions

-- ========================================
-- 7. Add Foreign Key Constraints to Existing Tables
-- ========================================
-- Note: This assumes users table exists. Adjust if different.
-- ALTER TABLE deal_concentration_thresholds 
-- ADD CONSTRAINT fk_deal_thresholds_user 
-- FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- ========================================
-- 8. Trigger for Updated Timestamp
-- ========================================
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_concentration_test_definitions_modtime 
    BEFORE UPDATE ON concentration_test_definitions 
    FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_deal_concentration_thresholds_modtime 
    BEFORE UPDATE ON deal_concentration_thresholds 
    FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- ========================================
-- Migration Complete
-- ========================================