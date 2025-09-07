#!/usr/bin/env python3
"""
Create MAG7 Concentration Test Configuration - Excel Specification
Based on exact test numbers from Excel: 41 tests total
Test numbers: 1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34
"""

# MAG7 Concentration Tests - Exact Excel specification (41 tests)
MAG7_EXCEL_TESTS = [1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34]

# MAG7-specific thresholds (2012 vintage adjustments)
MAG7_THRESHOLDS = {
    # Lower covenant-lite limit for 2012
    29: 0.50,  # Cov-lite 50% (vs 60% in later versions)
    # Lower weighted average coupon for 2012
    34: 0.065,  # WAC 6.5% (vs 7% in later versions) 
    # Lower WARF for 2012
    36: 2850.0,  # WARF 2850 (vs 2900 in later versions)
    # Lower diversity score for 2012
    37: 55.0,  # Diversity 55 (vs 60 in later versions)
    # Other key thresholds can use database defaults
}

def generate_mag7_excel_sql():
    """Generate SQL migration for MAG7 using exact Excel test specification"""
    
    print("=== MAG7 Concentration Tests - Excel Specification ===")
    print(f"Total tests for MAG7: {len(MAG7_EXCEL_TESTS)}")
    print(f"Test numbers: {MAG7_EXCEL_TESTS}")
    print()
    
    # Generate SQL for MAG7 threshold overrides
    sql_overrides = []
    
    for test_num in sorted(MAG7_EXCEL_TESTS):
        # Use custom threshold if specified, otherwise use default
        if test_num in MAG7_THRESHOLDS:
            threshold_value = MAG7_THRESHOLDS[test_num]
            notes = f"MAG7 2012 vintage custom threshold ({threshold_value})"
        else:
            threshold_value = "ctd.default_threshold"
            notes = f"MAG7 using default threshold"
        
        if test_num in MAG7_THRESHOLDS:
            # For custom thresholds, use direct value
            sql_overrides.append(
                f"('MAG7', {test_num}, {threshold_value}, '2016-03-23', NULL, 'MAG7', '{notes}', 1, CURRENT_TIMESTAMP)"
            )
    
    print("=== SQL Migration for MAG7 (Excel Spec) ===")
    print("-- MAG7 Concentration Test Thresholds")
    print("-- Based on exact Excel specification: 41 tests")
    print("-- Test numbers:", MAG7_EXCEL_TESTS)
    print()
    print("-- Clear existing MAG7 data")
    print("DELETE FROM deal_concentration_thresholds WHERE deal_id = 'MAG7';")
    print()
    
    # Insert tests using default thresholds first
    print("-- Insert MAG7 tests using default thresholds")
    print("INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at)")
    print("SELECT 'MAG7', test_id, default_threshold, '2016-03-23', NULL, 'MAG7', 'MAG7 using default threshold', 1, CURRENT_TIMESTAMP")
    print("FROM concentration_test_definitions")
    print(f"WHERE test_number IN ({','.join(map(str, MAG7_EXCEL_TESTS))});")
    print()
    
    # Insert custom threshold overrides
    if sql_overrides:
        print("-- Update MAG7-specific thresholds (2012 vintage adjustments)")
        for test_num in sorted(MAG7_THRESHOLDS.keys()):
            threshold = MAG7_THRESHOLDS[test_num]
            print(f"UPDATE deal_concentration_thresholds SET threshold_value = {threshold}, notes = 'MAG7 2012 vintage custom threshold' WHERE deal_id = 'MAG7' AND test_id = {test_num};")
    
    print()
    print("-- Verification query")
    print("SELECT COUNT(*) as mag7_test_count FROM deal_concentration_thresholds WHERE deal_id = 'MAG7';")
    
    # Analysis
    print(f"\n=== MAG7 Analysis ===")
    print(f"Total tests: {len(MAG7_EXCEL_TESTS)}")
    print(f"Custom thresholds: {len(MAG7_THRESHOLDS)} tests")
    print(f"Default thresholds: {len(MAG7_EXCEL_TESTS) - len(MAG7_THRESHOLDS)} tests")
    
    # Show custom thresholds
    print(f"\nMAG7 Custom Thresholds (2012 vintage):")
    for test_num in sorted(MAG7_THRESHOLDS.keys()):
        threshold = MAG7_THRESHOLDS[test_num]
        if isinstance(threshold, float) and threshold < 1:
            threshold_str = f"{threshold*100:.1f}%"
        else:
            threshold_str = f"{threshold}"
        print(f"  Test #{test_num}: {threshold_str}")
    
    return MAG7_EXCEL_TESTS

if __name__ == "__main__":
    # Generate MAG7 concentration test configuration
    generate_mag7_excel_sql()
    
    print("\n=== Key MAG7 2012 Vintage Characteristics ===")
    print("• 41 total concentration tests (per Excel specification)")
    print("• Lower covenant-lite limit: 50% (vs 60% in later versions)")
    print("• Lower weighted average coupon: 6.5% (vs 7% in later versions)")
    print("• Lower WARF limit: 2850 (vs 2900 in later versions)")
    print("• Lower diversity score: 55 (vs 60 in later versions)")
    print("• All other tests use database default thresholds")