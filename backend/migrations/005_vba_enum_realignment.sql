-- VBA TestNum Enum Realignment Migration
-- This migration realigns the database test numbers to match the original VBA TestNum enum
-- Critical for maintaining compatibility with the original Excel/VBA system

BEGIN TRANSACTION;

-- First, backup existing data
CREATE TABLE IF NOT EXISTS concentration_test_definitions_backup AS 
SELECT * FROM concentration_test_definitions;

CREATE TABLE IF NOT EXISTS deal_concentration_thresholds_backup AS 
SELECT * FROM deal_concentration_thresholds;

-- Clear existing data to avoid conflicts
DELETE FROM deal_concentration_thresholds;
DELETE FROM concentration_test_definitions;

-- Reset the sequence to start from 1
ALTER SEQUENCE concentration_test_definitions_test_id_seq RESTART WITH 1;

-- Insert all VBA TestNum enum tests with correct numbering
-- This matches the VBA enum from UDTandEnum.bas lines 36-91

INSERT INTO concentration_test_definitions (test_number, test_name, test_description, test_category, result_type, default_threshold, calculation_method, is_active) VALUES

-- Asset Quality Tests (VBA enum 1-13, 28-31, 40-48)
(1, 'Limitation on Senior Secured Loans', 'Maximum percentage of senior secured loans', 'asset_quality', 'percentage', 0.90, 'sum_by_criteria', true),
(2, 'Limitation on non Senior Secured Loans', 'Maximum percentage of non-senior secured loans', 'asset_quality', 'percentage', 0.10, 'sum_by_criteria', true),
(3, 'Limitation on 6th Largest Obligor', 'Maximum exposure to 6th largest obligor', 'asset_quality', 'percentage', 0.02, 'largest_obligor', true),
(4, 'Limitation on 1st Largest Obligor', 'Maximum exposure to largest obligor', 'asset_quality', 'percentage', 0.025, 'largest_obligor', true),
(5, 'Limitation on DIP Obligor', 'Maximum exposure to DIP obligor', 'asset_quality', 'percentage', 0.02, 'largest_obligor', true),
(6, 'Limitation on Non Senior Secured Obligor', 'Maximum exposure to non-senior secured obligor', 'asset_quality', 'percentage', 0.02, 'largest_obligor', true),
(7, 'Limitation on Caa Loans', 'Maximum percentage of Caa rated loans', 'asset_quality', 'percentage', 0.075, 'sum_by_criteria', true),
(8, 'Limitation on Assets Pay Less Frequently than Quarterly', 'Maximum percentage of assets paying less than quarterly', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(9, 'Limitation on Fixed Rate Obligations', 'Maximum percentage of fixed rate obligations', 'asset_quality', 'percentage', 0.025, 'sum_by_criteria', true),
(10, 'Limitation on Current Pay Obligations', 'Maximum percentage of current pay obligations', 'asset_quality', 'percentage', 0.025, 'sum_by_criteria', true),
(11, 'Limitation on DIP Obligations', 'Maximum percentage of DIP obligations', 'asset_quality', 'percentage', 0.075, 'sum_by_criteria', true),
(12, 'Limitation on Unfunded Commitments', 'Maximum percentage of unfunded commitments', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(13, 'Limitation on Participation Interest', 'Maximum percentage of participation interests', 'asset_quality', 'percentage', 0.15, 'sum_by_criteria', true),
(28, 'Limitation on Bridge Loans', 'Maximum percentage of bridge loans', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(29, 'Limitation on Cov Lite Loans', 'Maximum percentage of covenant lite loans', 'asset_quality', 'percentage', 0.60, 'sum_by_criteria', true),
(30, 'Limitation on Deferrable Securities', 'Maximum percentage of deferrable securities', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(31, 'Limitation on Facility Size', 'Maximum facility size concentration', 'asset_quality', 'percentage', 0.07, 'sum_by_criteria', true),
(40, 'Limitation on CCC Loans', 'Maximum percentage of CCC rated loans', 'asset_quality', 'percentage', 0.075, 'sum_by_criteria', true),
(41, 'Limitation on Canada', 'Maximum exposure to Canadian obligors', 'geographic', 'percentage', 0.125, 'sum_by_criteria', true),
(42, 'Limitation on Letter of Credit', 'Maximum percentage of letter of credit facilities', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(43, 'Limitation on Long Dated', 'Maximum percentage of long dated obligations', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(44, 'Limitation on Unsecured Loans', 'Maximum percentage of unsecured loans', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(45, 'Limitation on Swap Non Discount', 'Maximum percentage of swap non-discount obligations', 'asset_quality', 'percentage', 0.05, 'sum_by_criteria', true),
(47, 'Limitation on Non-Emerging Market Obligors', 'Maximum exposure to non-emerging market obligors', 'geographic', 'percentage', 0.125, 'sum_by_criteria', true),
(48, 'Limitation on SP Criteria', 'Maximum exposure based on S&P criteria', 'asset_quality', 'percentage', 0.15, 'sum_by_criteria', true),
(53, 'Limitation on Facility Size MAG08', 'Maximum facility size (MAG08 version)', 'asset_quality', 'percentage', 0.07, 'sum_by_criteria', true),

-- Geographic Tests (VBA enum 14-24)
(14, 'Limitation on Countries Not US', 'Maximum exposure to non-US countries', 'geographic', 'percentage', 0.20, 'sum_by_criteria', true),
(15, 'Limitation on Countries Canada and Tax Jurisdictions', 'Maximum exposure to Canada and tax jurisdictions', 'geographic', 'percentage', 0.125, 'sum_by_criteria', true),
(16, 'Limitation on Countries Not US Canada UK', 'Maximum exposure to countries other than US, Canada, UK', 'geographic', 'percentage', 0.10, 'sum_by_criteria', true),
(17, 'Limitation on Group Countries', 'Maximum exposure to group countries', 'geographic', 'percentage', 0.15, 'sum_by_criteria', true),
(18, 'Limitation on Group I Countries', 'Maximum exposure to Group I countries', 'geographic', 'percentage', 0.15, 'sum_by_criteria', true),
(19, 'Limitation on Individual Group I Countries', 'Maximum exposure to individual Group I countries', 'geographic', 'percentage', 0.05, 'sum_by_criteria', true),
(20, 'Limitation on Group II Countries', 'Maximum exposure to Group II countries', 'geographic', 'percentage', 0.10, 'sum_by_criteria', true),
(21, 'Limitation on Individual Group II Countries', 'Maximum exposure to individual Group II countries', 'geographic', 'percentage', 0.05, 'sum_by_criteria', true),
(22, 'Limitation on Group III Countries', 'Maximum exposure to Group III countries', 'geographic', 'percentage', 0.075, 'sum_by_criteria', true),
(23, 'Limitation on Individual Group III Countries', 'Maximum exposure to individual Group III countries', 'geographic', 'percentage', 0.05, 'sum_by_criteria', true),
(24, 'Limitation on Tax Jurisdictions', 'Maximum exposure to tax jurisdictions', 'geographic', 'percentage', 0.075, 'sum_by_criteria', true),

-- Industry Tests (VBA enum 25-27, 49-52)
(25, 'Limitation on 4th Largest SP Industry Classification', 'Maximum exposure to 4th largest S&P industry', 'industry', 'percentage', 0.075, 'industry_concentration', true),
(26, 'Limitation on 2nd Largest SP Classification', 'Maximum exposure to 2nd largest S&P industry', 'industry', 'percentage', 0.12, 'industry_concentration', true),
(27, 'Limitation on 1st Largest SP Classification', 'Maximum exposure to largest S&P industry', 'industry', 'percentage', 0.15, 'industry_concentration', true),
(49, 'Limitation on 1st Largest Moody Industry', 'Maximum exposure to largest Moody industry', 'industry', 'percentage', 0.15, 'industry_concentration', true),
(50, 'Limitation on 2nd Largest Moody Industry', 'Maximum exposure to 2nd largest Moody industry', 'industry', 'percentage', 0.12, 'industry_concentration', true),
(51, 'Limitation on 3rd Largest Moody Industry', 'Maximum exposure to 3rd largest Moody industry', 'industry', 'percentage', 0.12, 'industry_concentration', true),
(52, 'Limitation on 4th Largest Moody Industry', 'Maximum exposure to 4th largest Moody industry', 'industry', 'percentage', 0.10, 'industry_concentration', true),

-- Portfolio Metrics Tests (VBA enum 32-36, 39, 46, 54)
(32, 'Weighted Average Spread', 'Minimum weighted average spread test', 'portfolio_metrics', 'basis_points', 425.0, 'weighted_average', true),
(33, 'Weighted Average Recovery Rate', 'Minimum weighted average Moody recovery rate', 'portfolio_metrics', 'percentage', 0.47, 'weighted_average', true),
(34, 'Weighted Average Coupon', 'Minimum weighted average coupon test', 'portfolio_metrics', 'percentage', 0.07, 'weighted_average', true),
(35, 'Weighted Average Life', 'Maximum weighted average life test', 'portfolio_metrics', 'years', 6.0, 'weighted_average', true),
(36, 'Weighted Average Rating Factor', 'Maximum weighted average rating factor', 'portfolio_metrics', 'factor', 2900.0, 'weighted_average', true),
(39, 'Weighted Average Spread MAG14', 'Minimum weighted average spread (MAG14)', 'portfolio_metrics', 'basis_points', 425.0, 'weighted_average', true),
(46, 'Weighted Average Spread MAG06', 'Minimum weighted average spread (MAG06)', 'portfolio_metrics', 'basis_points', 400.0, 'weighted_average', true),
(54, 'Weighted Average Rating Factor MAG14', 'Maximum weighted average rating factor (MAG14)', 'portfolio_metrics', 'factor', 2900.0, 'weighted_average', true),

-- Special Tests (VBA enum 37-38)
(37, 'Moody Diversity Test', 'Minimum Moody diversity score', 'portfolio_metrics', 'score', 10.0, 'diversity_calculation', true),
(38, 'JROC Test', 'Junior OC test calculation', 'portfolio_metrics', 'percentage', 1.0, 'coverage_ratio', true);

-- Now restore the MAG17 overrides with corrected test IDs
-- These need to be mapped to the correct VBA enum test numbers

INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, notes, created_by)
SELECT 
    'MAG17',
    (SELECT test_id FROM concentration_test_definitions WHERE test_number = vba_test_number),
    threshold_value,
    effective_date::date,
    notes || ' - REALIGNED TO VBA ENUM',
    created_by
FROM (VALUES
    -- Map existing MAG17 overrides to correct VBA test numbers
    (1, 0.90, '2016-03-23', 'Senior Secured Loans - VBA verified 90% - CRITICAL FIX', 1),
    (2, 0.10, '2016-03-23', 'Non-Senior Secured Loans maximum 10%', 1),
    (3, 0.02, '2016-03-23', 'Single obligor maximum 2%', 1),
    (5, 0.025, '2016-03-23', 'DIP obligor maximum 2.5%', 1),
    (6, 0.02, '2016-03-23', 'Non-senior secured obligor maximum 2%', 1),
    (7, 0.02, '2016-03-23', 'Caa loans maximum 2%', 1),
    (40, 0.075, '2016-03-23', 'CCC loans maximum 7.5% - matches existing system', 1),
    (8, 0.05, '2016-03-23', 'Assets paying less than quarterly maximum 5%', 1),
    (14, 0.20, '2016-03-23', 'Non-USA country exposure maximum 20%', 1),
    (29, 0.60, '2016-03-23', 'Covenant lite maximum 60%', 1),
    (33, 0.47, '2016-03-23', 'Weighted average recovery rate minimum 47%', 1),
    (34, 0.07, '2016-03-23', 'Weighted average coupon minimum 7%', 1)
) AS overrides(vba_test_number, threshold_value, effective_date, notes, created_by)
WHERE (SELECT test_id FROM concentration_test_definitions WHERE test_number = vba_test_number) IS NOT NULL;

COMMIT;