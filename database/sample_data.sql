-- Sample Data for CLO Portfolio Management System
-- Provides realistic test data for development and validation

-- =============================================================================
-- REFERENCE DATA
-- =============================================================================

-- Rating scales (Moody's and S&P)
INSERT INTO rating_scales (agency, rating_symbol, rating_numeric, warf_factor) VALUES
-- Moody's ratings
('MOODY', 'Aaa', 1, 1),
('MOODY', 'Aa1', 2, 10),
('MOODY', 'Aa2', 3, 20),
('MOODY', 'Aa3', 4, 40),
('MOODY', 'A1', 5, 70),
('MOODY', 'A2', 6, 120),
('MOODY', 'A3', 7, 180),
('MOODY', 'Baa1', 8, 260),
('MOODY', 'Baa2', 9, 360),
('MOODY', 'Baa3', 10, 610),
('MOODY', 'Ba1', 11, 940),
('MOODY', 'Ba2', 12, 1350),
('MOODY', 'Ba3', 13, 1766),
('MOODY', 'B1', 14, 2220),
('MOODY', 'B2', 15, 2720),
('MOODY', 'B3', 16, 3490),
('MOODY', 'Caa1', 17, 4770),
('MOODY', 'Caa2', 18, 6500),
('MOODY', 'Caa3', 19, 8070),
('MOODY', 'Ca', 20, 10000),
('MOODY', 'C', 21, 10000),

-- S&P ratings
('SP', 'AAA', 1, 1),
('SP', 'AA+', 2, 10),
('SP', 'AA', 3, 20),
('SP', 'AA-', 4, 40),
('SP', 'A+', 5, 70),
('SP', 'A', 6, 120),
('SP', 'A-', 7, 180),
('SP', 'BBB+', 8, 260),
('SP', 'BBB', 9, 360),
('SP', 'BBB-', 10, 610),
('SP', 'BB+', 11, 940),
('SP', 'BB', 12, 1350),
('SP', 'BB-', 13, 1766),
('SP', 'B+', 14, 2220),
('SP', 'B', 15, 2720),
('SP', 'B-', 16, 3490),
('SP', 'CCC', 17, 4770),
('SP', 'D', 18, 10000);

-- US Holidays (sample for 2023-2025)
INSERT INTO holidays (holiday_date, holiday_name, country_code) VALUES
('2023-01-01', 'New Years Day', 'US'),
('2023-01-16', 'Martin Luther King Jr. Day', 'US'),
('2023-02-20', 'Presidents Day', 'US'),
('2023-05-29', 'Memorial Day', 'US'),
('2023-07-04', 'Independence Day', 'US'),
('2023-09-04', 'Labor Day', 'US'),
('2023-10-09', 'Columbus Day', 'US'),
('2023-11-23', 'Thanksgiving', 'US'),
('2023-12-25', 'Christmas Day', 'US'),

('2024-01-01', 'New Years Day', 'US'),
('2024-01-15', 'Martin Luther King Jr. Day', 'US'),
('2024-02-19', 'Presidents Day', 'US'),
('2024-05-27', 'Memorial Day', 'US'),
('2024-07-04', 'Independence Day', 'US'),
('2024-09-02', 'Labor Day', 'US'),
('2024-10-14', 'Columbus Day', 'US'),
('2024-11-28', 'Thanksgiving', 'US'),
('2024-12-25', 'Christmas Day', 'US');

-- =============================================================================
-- CLO DEAL STRUCTURE
-- =============================================================================

-- Sample CLO deal
INSERT INTO clo_deals (
    deal_id, deal_name, manager_name, trustee_name,
    pricing_date, closing_date, effective_date, first_payment_date, 
    maturity_date, reinvestment_end_date, no_call_date,
    target_par_amount, ramp_up_period, payment_frequency, deal_status
) VALUES (
    'DEMO-CLO-2023-1', 'Demo CLO 2023-1', 'Demo Asset Management', 'Demo Trust Company',
    '2023-06-01', '2023-06-15', '2023-06-15', '2023-09-15',
    '2030-06-15', '2025-06-15', '2025-06-15',
    400000000.00, 6, 4, 'ACTIVE'
);

-- Sample CLO tranches
INSERT INTO clo_tranches (
    tranche_id, deal_id, tranche_name, initial_balance, current_balance,
    coupon_rate, coupon_type, index_name, margin,
    mdy_rating, sp_rating, seniority_level, payment_rank, interest_deferrable
) VALUES 
('DEMO-CLO-2023-1-A', 'DEMO-CLO-2023-1', 'Class A Notes', 280000000.00, 280000000.00,
 0.0525, 'FLOAT', 'SOFR', 0.0200, 'Aa2', 'AA', 1, 1, FALSE),
 
('DEMO-CLO-2023-1-B', 'DEMO-CLO-2023-1', 'Class B Notes', 45000000.00, 45000000.00,
 0.0650, 'FLOAT', 'SOFR', 0.0325, 'A2', 'A', 2, 2, FALSE),
 
('DEMO-CLO-2023-1-C', 'DEMO-CLO-2023-1', 'Class C Notes', 35000000.00, 35000000.00,
 0.0800, 'FLOAT', 'SOFR', 0.0475, 'Baa3', 'BBB-', 3, 3, FALSE),
 
('DEMO-CLO-2023-1-D', 'DEMO-CLO-2023-1', 'Class D Notes', 20000000.00, 20000000.00,
 0.1200, 'FLOAT', 'SOFR', 0.0875, 'Ba3', 'BB-', 4, 4, FALSE),
 
('DEMO-CLO-2023-1-E', 'DEMO-CLO-2023-1', 'Class E Notes', 20000000.00, 20000000.00,
 0.1500, 'FIXED', NULL, 0.0000, 'B2', 'B', 5, 5, TRUE);

-- =============================================================================
-- COMPLIANCE TESTS
-- =============================================================================

INSERT INTO compliance_tests (
    test_name, test_category, test_formula, threshold_value, threshold_type,
    test_description, regulatory_source, active
) VALUES
-- Concentration limits
('Senior Secured Loans Minimum', 'CONCENTRATION', 
 'SENIORITY = SENIOR SECURED', 0.80, 'MIN',
 'Minimum 80% senior secured loans', 'Indenture Section 12.09(a)', TRUE),

('Single Obligor Maximum', 'CONCENTRATION',
 'ISSUER_NAME = {OBLIGOR}', 0.02, 'MAX', 
 'Maximum 2% exposure to single obligor', 'Indenture Section 12.09(b)', TRUE),

('CCC Assets Maximum', 'QUALITY',
 "MOODY'S RATING >= Caa1 OR S&P RATING >= CCC", 0.075, 'MAX',
 'Maximum 7.5% CCC-rated assets', 'Indenture Section 12.09(c)', TRUE),

-- Quality tests  
('Weighted Average Rating Factor', 'QUALITY',
 'WEIGHTED_AVERAGE(WARF_FACTOR)', 2720, 'MAX',
 'Weighted Average Rating Factor maximum', 'Indenture Section 12.09(d)', TRUE),

('Weighted Average Spread', 'QUALITY', 
 'WEIGHTED_AVERAGE(SPREAD)', 0.0325, 'MIN',
 'Minimum weighted average spread', 'Indenture Section 12.09(e)', TRUE),

-- Diversity
('Moody Diversity Score', 'DIVERSITY',
 'MOODYS_DIVERSITY_SCORE()', 18, 'MIN',
 'Minimum Moody diversity score', 'Indenture Section 12.09(f)', TRUE),

-- Geographic/Industry limits
('Non-US Assets Maximum', 'GEOGRAPHIC',
 'COUNTRY != US', 0.20, 'MAX',
 'Maximum 20% non-US assets', 'Indenture Section 12.09(g)', TRUE),

('Single Industry Maximum', 'INDUSTRY', 
 "MOODY'S INDUSTRY = {INDUSTRY}", 0.12, 'MAX',
 'Maximum 12% single industry exposure', 'Indenture Section 12.09(h)', TRUE);

-- =============================================================================
-- SAMPLE ASSETS
-- =============================================================================

-- Sample corporate loans and bonds
INSERT INTO assets (
    blkrock_id, issue_name, issuer_name, issuer_id, bond_loan,
    par_amount, market_value, currency,
    maturity, dated_date, first_payment_date,
    coupon, coupon_type, index_name, cpn_spread, payment_freq,
    day_count, business_day_conv, amortization_type,
    mdy_rating, sp_rating, mdy_industry, sp_industry, country, seniority,
    facility_size, flags,
    created_at, updated_at
) VALUES
-- Software/Technology sector
('MSFT001', 'Microsoft Corp Term Loan B', 'Microsoft Corporation', 'MSFT', 'LOAN',
 5000000.00, 1.0150, 'USD',
 '2028-03-15', '2023-03-15', '2023-06-15',
 0.0575, 'FLOAT', 'SOFR', 0.0325, 4,
 'ACTUAL/360', 'MODIFIED FOLLOWING', 'BULLET',
 'A1', 'A+', 'Software', 'Technology', 'US', 'Senior Secured',
 2500000000.00, '{"pik_asset": false, "cov_lite": true, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('AAPL002', 'Apple Inc Senior Notes', 'Apple Inc.', 'AAPL', 'BOND',
 3000000.00, 0.9850, 'USD',
 '2027-09-12', '2022-09-12', '2023-03-12',
 0.0425, 'FIXED', NULL, 0.0000, 2,
 '30/360', 'FOLLOWING', 'BULLET', 
 'Aaa', 'AAA', 'Technology Hardware', 'Technology', 'US', 'Senior Unsecured',
 5000000000.00, '{"pik_asset": false, "cov_lite": false, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Healthcare sector
('JNJ003', 'Johnson & Johnson Term Loan', 'Johnson & Johnson', 'JNJ', 'LOAN',
 4500000.00, 1.0225, 'USD',
 '2029-01-20', '2023-01-20', '2023-04-20',
 0.0650, 'FLOAT', 'SOFR', 0.0400, 4,
 'ACTUAL/360', 'MODIFIED FOLLOWING', 'BULLET',
 'Aa3', 'AA-', 'Healthcare', 'Healthcare', 'US', 'Senior Secured',
 1800000000.00, '{"pik_asset": false, "cov_lite": false, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Energy sector  
('XOM004', 'Exxon Mobil Corp Bond', 'Exxon Mobil Corporation', 'XOM', 'BOND',
 2500000.00, 0.9650, 'USD',
 '2026-11-08', '2021-11-08', '2022-05-08',
 0.0520, 'FIXED', NULL, 0.0000, 2,
 '30/360', 'FOLLOWING', 'BULLET',
 'Baa1', 'BBB+', 'Oil & Gas', 'Energy', 'US', 'Senior Unsecured',
 3200000000.00, '{"pik_asset": false, "cov_lite": false, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Financial Services
('JPM005', 'JPMorgan Chase Term Loan B', 'JPMorgan Chase & Co.', 'JPM', 'LOAN',
 6000000.00, 1.0075, 'USD',
 '2028-07-15', '2023-07-15', '2023-10-15',
 0.0525, 'FLOAT', 'SOFR', 0.0275, 4,
 'ACTUAL/360', 'MODIFIED FOLLOWING', 'BULLET',
 'A2', 'A', 'Banking', 'Financials', 'US', 'Senior Secured',
 4500000000.00, '{"pik_asset": false, "cov_lite": true, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Retail sector (lower rated)
('TGT006', 'Target Corp Leveraged Loan', 'Target Corporation', 'TGT', 'LOAN',
 3500000.00, 0.9850, 'USD',
 '2027-12-30', '2022-12-30', '2023-03-30',
 0.0875, 'FLOAT', 'SOFR', 0.0625, 4,
 'ACTUAL/360', 'MODIFIED FOLLOWING', 'AMORTIZING',
 'Ba2', 'BB', 'Retail', 'Consumer Discretionary', 'US', 'Senior Secured',
 1200000000.00, '{"pik_asset": false, "cov_lite": true, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- International exposure (Canada)
('RY007', 'Royal Bank of Canada TLB', 'Royal Bank of Canada', 'RY', 'LOAN',
 2000000.00, 1.0125, 'CAD',
 '2028-05-22', '2023-05-22', '2023-08-22',
 0.0675, 'FLOAT', 'CDOR', 0.0425, 4,
 'ACTUAL/365', 'MODIFIED FOLLOWING', 'BULLET',
 'Aa2', 'AA-', 'Banking', 'Financials', 'CA', 'Senior Secured',
 3000000000.00, '{"pik_asset": false, "cov_lite": false, "current_pay": true}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- High-yield/distressed (CCC rated)
('DIST008', 'Distressed Retail Corp', 'Distressed Retail Corp', 'DIST', 'LOAN',
 1500000.00, 0.7500, 'USD',
 '2025-08-15', '2022-08-15', '2022-11-15',
 0.1250, 'FLOAT', 'SOFR', 0.1000, 4,
 'ACTUAL/360', 'MODIFIED FOLLOWING', 'BULLET',
 'Caa2', 'CCC', 'Retail', 'Consumer Discretionary', 'US', 'Senior Secured',
 500000000.00, '{"pik_asset": true, "cov_lite": true, "current_pay": false, "default_asset": false}',
 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- =============================================================================
-- DEAL ASSET POSITIONS
-- =============================================================================

-- Map assets to the demo deal
INSERT INTO deal_assets (
    deal_id, blkrock_id, par_amount, purchase_price, purchase_date, position_status
) VALUES
('DEMO-CLO-2023-1', 'MSFT001', 5000000.00, 1.0000, '2023-06-15', 'ACTIVE'),
('DEMO-CLO-2023-1', 'AAPL002', 3000000.00, 0.9900, '2023-06-15', 'ACTIVE'),
('DEMO-CLO-2023-1', 'JNJ003', 4500000.00, 1.0100, '2023-06-20', 'ACTIVE'),
('DEMO-CLO-2023-1', 'XOM004', 2500000.00, 0.9700, '2023-06-20', 'ACTIVE'),
('DEMO-CLO-2023-1', 'JPM005', 6000000.00, 1.0000, '2023-07-01', 'ACTIVE'),
('DEMO-CLO-2023-1', 'TGT006', 3500000.00, 0.9800, '2023-07-05', 'ACTIVE'),
('DEMO-CLO-2023-1', 'RY007', 2000000.00, 1.0150, '2023-07-10', 'ACTIVE'),
('DEMO-CLO-2023-1', 'DIST008', 1500000.00, 0.7500, '2023-07-15', 'ACTIVE');

-- =============================================================================
-- SAMPLE CASH FLOWS (First Quarter Only)
-- =============================================================================

-- Microsoft Term Loan B cash flows
INSERT INTO asset_cash_flows (
    blkrock_id, period_number, payment_date, accrual_start_date, accrual_end_date,
    beginning_balance, interest_payment, scheduled_principal, unscheduled_principal,
    ending_balance, total_cash_flow
) VALUES
('MSFT001', 1, '2023-09-15', '2023-06-15', '2023-09-15', 
 5000000.00, 71875.00, 0.00, 125000.00, 4875000.00, 196875.00),
('MSFT001', 2, '2023-12-15', '2023-09-15', '2023-12-15',
 4875000.00, 69843.75, 0.00, 121875.00, 4753125.00, 191718.75);

-- Apple Notes cash flows  
INSERT INTO asset_cash_flows (
    blkrock_id, period_number, payment_date, accrual_start_date, accrual_end_date,
    beginning_balance, interest_payment, scheduled_principal, unscheduled_principal,
    ending_balance, total_cash_flow
) VALUES
('AAPL002', 1, '2023-09-12', '2023-03-12', '2023-09-12',
 3000000.00, 63750.00, 0.00, 0.00, 3000000.00, 63750.00),
('AAPL002', 2, '2024-03-12', '2023-09-12', '2024-03-12',
 3000000.00, 63750.00, 0.00, 0.00, 3000000.00, 63750.00);

-- =============================================================================
-- SAMPLE COMPLIANCE TEST RESULTS
-- =============================================================================

-- Compliance test results for demo deal (as of 2023-09-15)
INSERT INTO compliance_test_results (
    deal_id, test_id, test_date, calculated_value, threshold_value, pass_fail,
    numerator, denominator, test_comments
) VALUES
-- Senior secured test (passing)
('DEMO-CLO-2023-1', 1, '2023-09-15', 0.8571, 0.8000, TRUE,
 24000000.00, 28000000.00, 'Portfolio 85.71% senior secured vs 80% minimum'),

-- CCC assets test (passing)  
('DEMO-CLO-2023-1', 3, '2023-09-15', 0.0536, 0.0750, TRUE,
 1500000.00, 28000000.00, 'CCC assets 5.36% vs 7.5% maximum'),

-- Weighted average spread (passing)
('DEMO-CLO-2023-1', 5, '2023-09-15', 0.0425, 0.0325, TRUE,
 NULL, NULL, 'Weighted average spread 425bps vs 325bps minimum'),

-- Non-US assets (passing)
('DEMO-CLO-2023-1', 7, '2023-09-15', 0.0714, 0.2000, TRUE,
 2000000.00, 28000000.00, 'Non-US exposure 7.14% vs 20% maximum');

-- =============================================================================
-- ASSET HISTORY (RATING CHANGES)
-- =============================================================================

-- Sample rating history for Target (rating downgrade)
INSERT INTO asset_history (blkrock_id, history_date, property_name, property_value) VALUES
('TGT006', '2023-06-01', 'mdy_rating', 'Ba1'),
('TGT006', '2023-08-15', 'mdy_rating', 'Ba2'), -- Current rating
('TGT006', '2023-06-01', 'sp_rating', 'BB+'),
('TGT006', '2023-08-15', 'sp_rating', 'BB'); -- Current rating