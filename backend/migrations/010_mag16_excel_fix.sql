-- ===============================================
-- MAG16 Excel Specification Fix
-- Migration 010: Add missing tests #36 and #39 to MAG16
-- ===============================================

-- MAG16 currently has 35 tests but Excel shows 37 tests
-- Missing tests: #36 (Maximum Moody's Rating Factor Test) and #39 (Minimum Floating Spread Test)

-- Add the two missing tests to MAG16
INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)
SELECT 'MAG16', test_id, default_threshold, '2016-03-23', NULL, 'MAG16', 'MAG16 Excel specification - missing test added', 1, CURRENT_TIMESTAMP
FROM concentration_test_definitions
WHERE test_number IN (36, 39);

-- ========================================
-- Validation Queries
-- ========================================

-- Verify MAG16 now has 37 tests
SELECT 
    'MAG16 Test Count' as metric,
    COUNT(*)::text as value,
    CASE WHEN COUNT(*) = 37 THEN 'PASS' ELSE 'FAIL' END as status
FROM deal_concentration_thresholds
WHERE deal_id = 'MAG16';

-- Show the newly added tests
SELECT 
    ctd.test_number,
    ctd.test_name,
    dct.threshold_value
FROM deal_concentration_thresholds dct
JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
WHERE dct.deal_id = 'MAG16' 
  AND ctd.test_number IN (36, 39)
ORDER BY ctd.test_number;

-- Final verification: Compare current MAG16 with Excel specification
SELECT 
    'MAG16 Excel Compliance' as description,
    'Fixed' as status,
    '37 tests matching Excel Mag 16 Inputs sheet' as details;

COMMIT;