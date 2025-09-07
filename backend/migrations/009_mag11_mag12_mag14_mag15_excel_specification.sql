-- ===============================================
-- MAG11, MAG12, MAG14, MAG15 Concentration Test Thresholds Migration
-- Migration 009: Four MAG Deals Excel Specifications
-- ===============================================

-- MAG11, MAG12, MAG14, MAG15: All 37 tests each from Excel input sheets
-- Source: TradeHypoPrelimv32.xlsm Excel file

-- ========================================
-- Clear existing data for all four deals
-- ========================================
DELETE FROM deal_concentration_thresholds WHERE deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15');

-- ========================================
-- MAG11 Configuration (37 tests)
-- ========================================
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG11', test_id, default_threshold, '2016-03-23', NULL, 'MAG11', 'MAG11 Excel specification', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38);

-- ========================================
-- MAG12 Configuration (37 tests)
-- ========================================  
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG12', test_id, default_threshold, '2016-03-23', NULL, 'MAG12', 'MAG12 Excel specification', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38);

-- ========================================
-- MAG14 Configuration (37 tests) - Note: uses test 39 instead of 32
-- ========================================
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG14', test_id, default_threshold, '2016-03-23', NULL, 'MAG14', 'MAG14 Excel specification', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,35,36,37,38,39);

-- ========================================
-- MAG15 Configuration (37 tests)
-- ========================================
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG15', test_id, default_threshold, '2016-03-23', NULL, 'MAG15', 'MAG15 Excel specification', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38);

-- ========================================
-- Vintage-Specific Threshold Adjustments
-- ========================================

-- MAG11 (2013-2014 vintage) adjustments
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.60, notes = 'MAG11 2013-2014 vintage - covenant-lite limit (60%)'
WHERE deal_id = 'MAG11' AND test_id = 29;

UPDATE deal_concentration_thresholds 
SET threshold_value = 0.070, notes = 'MAG11 2013-2014 vintage - WAC requirement (7.0%)'
WHERE deal_id = 'MAG11' AND test_id = 34;

-- MAG12 (2014 vintage) adjustments
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.60, notes = 'MAG12 2014 vintage - covenant-lite limit (60%)'
WHERE deal_id = 'MAG12' AND test_id = 29;

UPDATE deal_concentration_thresholds 
SET threshold_value = 0.070, notes = 'MAG12 2014 vintage - WAC requirement (7.0%)'
WHERE deal_id = 'MAG12' AND test_id = 34;

-- MAG14 (2014 vintage) adjustments - uses test 39 for floating spread
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.60, notes = 'MAG14 2014 vintage - covenant-lite limit (60%)'
WHERE deal_id = 'MAG14' AND test_id = 29;

UPDATE deal_concentration_thresholds 
SET threshold_value = 0.070, notes = 'MAG14 2014 vintage - WAC requirement (7.0%)'
WHERE deal_id = 'MAG14' AND test_id = 34;

-- MAG15 (2015 vintage) adjustments
UPDATE deal_concentration_thresholds 
SET threshold_value = 0.60, notes = 'MAG15 2015 vintage - covenant-lite limit (60%)'
WHERE deal_id = 'MAG15' AND test_id = 29;

UPDATE deal_concentration_thresholds 
SET threshold_value = 0.070, notes = 'MAG15 2015 vintage - WAC requirement (7.0%)'
WHERE deal_id = 'MAG15' AND test_id = 34;

-- ========================================
-- Performance Indexes
-- ========================================
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag11_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG11';
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag12_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG12';
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag14_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG14';
CREATE INDEX IF NOT EXISTS idx_deal_concentration_thresholds_mag15_excel ON deal_concentration_thresholds(deal_id) WHERE deal_id = 'MAG15';

-- ========================================
-- Validation Queries
-- ========================================

-- Verify all four deals have exactly 37 tests
SELECT 
    deal_id,
    COUNT(*) as test_count,
    CASE WHEN COUNT(*) = 37 THEN 'PASS' ELSE 'FAIL' END as status
FROM deal_concentration_thresholds
WHERE deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15')
GROUP BY deal_id
ORDER BY deal_id;

-- Show custom thresholds (vintage adjustments)
SELECT 
    dct.deal_id,
    ctd.test_number,
    ctd.test_name,
    ctd.default_threshold as default_value,
    dct.threshold_value as custom_value,
    dct.notes
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15')
  AND dct.threshold_value != ctd.default_threshold
ORDER BY dct.deal_id, ctd.test_number;

-- Test categories breakdown for all four deals
SELECT 
    dct.deal_id,
    ctd.test_category,
    COUNT(*) as test_count
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15')
GROUP BY dct.deal_id, ctd.test_category
ORDER BY dct.deal_id, ctd.test_category;

-- Complete MAG comparison (all Excel-verified deals)
SELECT 
    dct.deal_id,
    COUNT(*) as total_tests,
    COUNT(CASE WHEN dct.threshold_value != ctd.default_threshold THEN 1 END) as custom_thresholds,
    CASE WHEN dct.deal_id IN ('MAG6', 'MAG7', 'MAG8', 'MAG9', 'MAG11', 'MAG12', 'MAG14', 'MAG15') 
         THEN 'Excel Verified' ELSE 'Needs Verification' END as status
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
GROUP BY dct.deal_id
ORDER BY dct.deal_id;

-- Configuration Summary
SELECT 
    'MAG11-15 Configuration' as description,
    'Complete' as status,
    '4 deals updated with Excel specifications' as details
UNION ALL
SELECT 
    'Key Difference',
    'MAG14 Special',
    'MAG14 uses test #39 (not #32) for floating spread'
UNION ALL
SELECT 
    'Vintage Adjustments',
    '2013-2015 vintage',
    'All deals: Cov-lite (60%), WAC (7.0%)'
UNION ALL
SELECT 
    'Excel Verified Total',
    '8 of 10 deals',
    'Only MAG16 and MAG17 remaining'
UNION ALL
SELECT 
    'MAG11 Tests',
    'Excel Verified',
    '1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38'
UNION ALL
SELECT 
    'MAG12 Tests',
    'Excel Verified',
    '1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38'
UNION ALL
SELECT 
    'MAG14 Tests',
    'Excel Verified',
    '1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,35,36,37,38,39'
UNION ALL
SELECT 
    'MAG15 Tests', 
    'Excel Verified',
    '1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38';

COMMIT;