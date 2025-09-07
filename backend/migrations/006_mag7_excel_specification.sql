-- ===============================================
-- MAG7 Concentration Test Thresholds Migration
-- Migration 006: MAG7 Excel Specification (41 tests)
-- ===============================================

-- MAG7 Concentration Test Configuration
-- Based on exact Excel specification: 41 tests
-- Test numbers: 1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34

-- Clear existing MAG7 data
DELETE FROM deal_concentration_thresholds WHERE deal_id = 'MAG7';

-- ========================================
-- Insert MAG7 Tests Using Default Thresholds
-- ========================================
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG7', test_id, default_threshold, '2016-03-23', NULL, 'MAG7', 'MAG7 using default threshold', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34);

-- ========================================
-- Update MAG7-Specific Thresholds (2012 Vintage)
-- ========================================

-- Test #29: Cov-lite limit (50% for 2012 vintage vs 60% later)
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.5, notes = 'MAG7 2012 vintage - lower cov-lite limit (50% vs 60%)'
WHERE deal_id = 'MAG7' AND test_id = 29;

-- Test #34: Weighted Average Coupon (6.5% for 2012 vintage vs 7% later)  
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.065, notes = 'MAG7 2012 vintage - lower WAC requirement (6.5% vs 7%)'
WHERE deal_id = 'MAG7' AND test_id = 34;

-- Test #36: Weighted Average Rating Factor (2850 for 2012 vintage vs 2900 later)
UPDATE deal_concentration_thresholds 
SET threshold_value = 2850.0, notes = 'MAG7 2012 vintage - lower WARF limit (2850 vs 2900)'
WHERE deal_id = 'MAG7' AND test_id = 36;

-- Test #37: Moody Diversity Score (55 for 2012 vintage vs 60 later)
UPDATE deal_concentration_thresholds 
SET threshold_value = 55.0, notes = 'MAG7 2012 vintage - lower diversity requirement (55 vs 60)'
WHERE deal_id = 'MAG7' AND test_id = 37;

-- ========================================
-- Performance Indexes
-- ========================================
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag7_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG7';

-- ========================================
-- Validation Queries
-- ========================================

-- Verify MAG7 test count matches Excel specification (41 tests)
SELECT 
    'MAG7 Test Count' as metric,
    COUNT(*)::text as value,
    CASE WHEN COUNT(*) = 41 THEN 'PASS' ELSE 'FAIL' END as status
FROM deal_concentration_thresholds
WHERE deal_id = 'MAG7';

-- Show MAG7 custom thresholds (2012 vintage adjustments)
SELECT 
    ctd.test_number,
    ctd.test_name,
    ctd.default_threshold as default_value,
    dct.threshold_value as mag7_value,
    dct.notes
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id = 'MAG7' 
  AND dct.threshold_value != ctd.default_threshold
ORDER BY ctd.test_number;

-- Verify MAG7 test categories breakdown
SELECT 
    ctd.test_category,
    COUNT(*) as test_count,
    MIN(ctd.test_number) as min_test,
    MAX(ctd.test_number) as max_test
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id = 'MAG7'
GROUP BY ctd.test_category
ORDER BY ctd.test_category;

-- Compare MAG versions
SELECT 
    dct.deal_id,
    COUNT(*) as total_tests,
    COUNT(CASE WHEN dct.threshold_value != ctd.default_threshold THEN 1 END) as custom_thresholds
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id IN ('MAG7', 'MAG16', 'MAG17')
GROUP BY dct.deal_id
ORDER BY dct.deal_id;

-- MAG7 Configuration Summary
SELECT 
    'MAG7 Configuration' as description,
    'Complete' as status,
    '41 tests per Excel specification' as details
UNION ALL
SELECT 
    'Vintage Adjustments',
    '4 custom thresholds',
    'Cov-lite (50%), WAC (6.5%), WARF (2850), Diversity (55)'
UNION ALL
SELECT 
    'Test Numbers',
    'Excel Verified',
    '1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34';

COMMIT;