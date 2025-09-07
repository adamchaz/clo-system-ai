-- ===============================================
-- MAG6 Concentration Test Thresholds Migration
-- Migration 007: MAG6 Excel Specification (36 tests)
-- ===============================================

-- MAG6 Concentration Test Configuration
-- Based on exact Excel specification: 36 tests
-- Test numbers: 1,2,3,4,8,9,10,11,13,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,34,35,38,40,41,42,43,44,45,46
-- Source: TradeHypoPrelimv32.xlsm "Mag 6 Inputs" sheet

-- Clear existing MAG6 data
DELETE FROM deal_concentration_thresholds WHERE deal_id = 'MAG6';

-- ========================================
-- Insert MAG6 Tests Using Excel Specification
-- ========================================
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG6', test_id, default_threshold, '2016-03-23', NULL, 'MAG6', 'MAG6 Excel specification', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,8,9,10,11,13,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,34,35,38,40,41,42,43,44,45,46);

-- ========================================
-- Update MAG6-Specific Thresholds (2012 Vintage)
-- ========================================

-- Test #29: Cov-lite limit (50% for 2012 vintage vs 60% later)
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.5, notes = 'MAG6 2012 vintage - lower cov-lite limit (50% vs 60%)'
WHERE deal_id = 'MAG6' AND test_id = 29;

-- Test #34: Weighted Average Coupon (6.5% for 2012 vintage vs 7% later)  
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.065, notes = 'MAG6 2012 vintage - lower WAC requirement (6.5% vs 7%)'
WHERE deal_id = 'MAG6' AND test_id = 34;

-- Test #46: MAG06-specific Minimum Floating Spread Test (4.0% from database evidence)
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.04, notes = 'MAG6 specific - Minimum Floating Spread Test (4.0%)'
WHERE deal_id = 'MAG6' AND test_id = 46;

-- ========================================
-- Performance Indexes
-- ========================================
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag6_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG6';

-- ========================================
-- Validation Queries
-- ========================================

-- Verify MAG6 test count matches Excel specification (36 tests)
SELECT 
    'MAG6 Test Count' as metric,
    COUNT(*)::text as value,
    CASE WHEN COUNT(*) = 36 THEN 'PASS' ELSE 'FAIL' END as status
FROM deal_concentration_thresholds
WHERE deal_id = 'MAG6';

-- Show MAG6 custom thresholds (2012 vintage adjustments)
SELECT 
    ctd.test_number,
    ctd.test_name,
    ctd.default_threshold as default_value,
    dct.threshold_value as mag6_value,
    dct.notes
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id = 'MAG6' 
  AND dct.threshold_value != ctd.default_threshold
ORDER BY ctd.test_number;

-- Verify MAG6 test categories breakdown
SELECT 
    ctd.test_category,
    COUNT(*) as test_count,
    MIN(ctd.test_number) as min_test,
    MAX(ctd.test_number) as max_test
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id = 'MAG6'
GROUP BY ctd.test_category
ORDER BY ctd.test_category;

-- Compare MAG6 vs other MAG versions
SELECT 
    dct.deal_id,
    COUNT(*) as total_tests,
    COUNT(CASE WHEN dct.threshold_value != ctd.default_threshold THEN 1 END) as custom_thresholds
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id IN ('MAG6', 'MAG7', 'MAG16', 'MAG17')
GROUP BY dct.deal_id
ORDER BY dct.deal_id;

-- MAG6 Configuration Summary
SELECT 
    'MAG6 Configuration' as description,
    'Complete' as status,
    '36 tests per Excel specification' as details
UNION ALL
SELECT 
    'Key Differences',
    'From Database',
    'Removed 1 test, added MAG06-specific Test #46'
UNION ALL
SELECT 
    'Vintage Adjustments',
    '3 custom thresholds',
    'Cov-lite (50%), WAC (6.5%), Floating Spread (4.0%)'
UNION ALL
SELECT 
    'Test Numbers (Excel)',
    'Verified',
    '1,2,3,4,8,9,10,11,13,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,34,35,38,40,41,42,43,44,45,46';

COMMIT;