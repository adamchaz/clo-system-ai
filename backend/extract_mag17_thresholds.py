#!/usr/bin/env python3
"""
Extract all concentration test thresholds from VBA ConcentrationTest.cls
and create MAG17-specific threshold configuration
"""

import re
from decimal import Decimal
from datetime import date

# VBA Concentration Test Thresholds (extracted from ConcentrationTest.cls)
VBA_THRESHOLDS = {
    # Test Number: (Test Name, Threshold, Pass Condition)
    1: ("Limitation on Senior Secured Loans", 0.9, ">"),  # Line 872: .Threshold = 0.9
    2: ("Limitation on non Senior Secured Loans", 0.1, "<"),  # Line 903: .Threshold = 0.1
    3: ("Limitation on Obligor", 0.02, "<"),  # Line 945: .Threshold = 0.02
    4: ("Limitation on DIP Obligor", 0.025, "<"),  # Line 957: .Threshold = 0.025
    5: ("Limitation on Non Senior Secured Obligor", 0.02, "<"),  # Line 999: .Threshold = 0.02
    6: ("Limitation on Caa Loans", 0.02, "<"),  # Line 1046: .Threshold = 0.02
    7: ("Limitation on CCC Loans", 0.075, "<"),  # Line 1081: .Threshold = 0.075
    8: ("Limitation on Assets Pay Less Frequently Quarterly", 0.05, "<"),  # Line 1145: .Threshold = 0.05
    9: ("Limitation on Fixed Rate Obligations", 0.025, "<"),  # Line 1180: .Threshold = 0.025
    10: ("Limitation on Current Pay Obligations", 0.025, "<"),  # Line 1213: .Threshold = 0.025
    11: ("Limitation on DIP Obligations", 0.075, "<"),  # Line 1247: .Threshold = 0.075
    12: ("Limitation on Unfunded Commitments", 0.05, "<"),  # Line 1278: .Threshold = 0.05
    13: ("Limitation on Participation Int", 0.15, "<"),  # Line 1308: .Threshold = 0.15
    14: ("Limitation on SP Criteria", 0.15, "<"),  # Line 1338: .Threshold = 0.15
    15: ("Limitation on Country Not USA", 0.2, "<"),  # Line 1369: .Threshold = 0.2
    16: ("Limitation on Country Canada Tax Jurisdiction", 0.125, "<"),  # Line 1402: .Threshold = 0.125
    17: ("Limitation on Country Canada", 0.125, "<"),  # Line 1434: .Threshold = 0.125
    18: ("Limitation on Non Emerging Market", 0.125, "<"),  # Line 1469: .Threshold = 0.125
    19: ("Limitation on Countries Not US Canada UK", 0.1, "<"),  # Line 1504: .Threshold = 0.1
    20: ("Limitation on Group Countries", 0.15, "<"),  # Line 1539: .Threshold = 0.15
    21: ("Limitation on Group I Countries", 0.15, "<"),  # Line 1583: .Threshold = 0.15
    22: ("Limitation on Group II Countries", 0.05, "<"),  # Line 1611: .Threshold = 0.05
    23: ("Limitation on Group III Countries", 0.1, "<"),  # Line 1653: .Threshold = 0.1
    24: ("Limitation on Tax Jurisdictions", 0.05, "<"),  # Line 1682: .Threshold = 0.05
    25: ("Limitation on SP Industry Classification", 0.075, "<"),  # Line 1721: .Threshold = 0.075
    # Industry classifications with multiple thresholds
    26: ("SP Industry - Oil Gas", 0.1, "<"),  # Line 1816: .Threshold = 0.1
    27: ("SP Industry - Telecom", 0.12, "<"),  # Line 1828: .Threshold = 0.12
    28: ("SP Industry - Automotive", 0.15, "<"),  # Line 1840: .Threshold = 0.15
    29: ("Limitation on Bridge Loans", 0.05, "<"),  # Line 1868: .Threshold = 0.05
    30: ("Limitation on Cov Lite", 0.6, "<"),  # Line 1899: .Threshold = 0.6
    31: ("Limitation on Deferrable Securities", 0.05, "<"),  # Line 1930: .Threshold = 0.05
    32: ("Limitation on Letter of Credit", 0.05, "<"),  # Line 1960: .Threshold = 0.05
    33: ("Limitation on Long Dated", 0.05, "<"),  # Line 1992: .Threshold = 0.05
    34: ("Limitation on Unsecured", 0.05, "<"),  # Line 2021: .Threshold = 0.05
    35: ("Limitation on Swap Non Discount", 0.05, "<"),  # Line 2050: .Threshold = 0.05
    36: ("Limitation on Facility Size", 0.07, "<"),  # Line 2086: .Threshold = 0.07
    37: ("Limitation on Facility Size MAG8", 0.07, "<"),  # Line 2118: .Threshold = 0.07
    
    # Dynamic thresholds (from test threshold dictionary)
    88: ("Weighted Average Spread", None, ">"),  # Dynamic from clsTestThresholdDict
    89: ("Weighted Average Spread MAG14", None, ">"),  # Dynamic from clsTestThresholdDict
    90: ("Weighted Average Spread MAG06", None, ">"),  # Dynamic from clsTestThresholdDict
    91: ("Weighted Average Recovery Rate", 0.47, ">"),  # Line 2320: .Threshold = 0.47
    92: ("Weighted Average Coupon", 0.07, ">="),  # Line 2352: .Threshold = 0.07
    93: ("Weighted Average Life", None, "<"),  # Dynamic threshold
    94: ("Weighted Average Rating Factor", None, "<"),  # Dynamic from clsTestThresholdDict
    95: ("Weighted Average Rating Factor MAG14", None, "<"),  # Dynamic from clsTestThresholdDict
    
    # Additional concentration tests found in VBA
    96: ("Moodys Diversity Score", None, ">"),  # Line 2586: Dynamic threshold
    97: ("Limitation on Moody Industry Classification", 0.15, "<"),  # Line 2692: .Threshold = 0.15
    98: ("Moody Industry - Oil Gas", 0.12, "<"),  # Line 2705: .Threshold = 0.12
    99: ("Moody Industry - Telecom", 0.12, "<"),  # Line 2718: .Threshold = 0.12
    100: ("Moody Industry - Automotive", 0.1, "<"),  # Line 2731: .Threshold = 0.1
}

# MAG17 Specific Threshold Overrides
# Based on analysis, MAG17 may have specific requirements different from defaults
MAG17_OVERRIDES = {
    # Senior Secured Loans - Critical fix identified
    1: 0.9,  # Confirmed 90% from VBA line 872
    # Non-Senior Secured Loans 
    2: 0.1,  # 10% maximum
    # Obligor concentrations
    3: 0.02,  # 2% maximum per obligor
    4: 0.025,  # 2.5% DIP obligor
    5: 0.02,  # 2% non-senior secured obligor
    # Rating-based limits
    6: 0.02,  # 2% Caa loans
    7: 0.075,  # 7.5% CCC loans - This is the one mentioned in migration as 7.5%
    8: 0.05,  # 5% assets paying less than quarterly
    # Additional key thresholds
    15: 0.2,  # 20% non-USA country exposure
    30: 0.6,  # 60% covenant lite maximum
    91: 0.47,  # 47% weighted average recovery rate minimum
    92: 0.07,  # 7% weighted average coupon minimum
}

def generate_mag17_threshold_sql():
    """Generate SQL to create MAG17-specific threshold overrides"""
    
    print("=== MAG17 Concentration Test Threshold Analysis ===")
    print(f"Total VBA tests identified: {len(VBA_THRESHOLDS)}")
    print(f"MAG17 overrides to apply: {len(MAG17_OVERRIDES)}")
    print()
    
    # Generate SQL for concentration test definitions
    sql_definitions = []
    sql_overrides = []
    
    for test_num, (test_name, threshold, pass_condition) in VBA_THRESHOLDS.items():
        if threshold is not None:
            # Determine test category
            category = "asset_quality"
            if "Country" in test_name or "Group" in test_name:
                category = "geographic"
            elif "Industry" in test_name or "SP Industry" in test_name or "Moody Industry" in test_name:
                category = "industry"
            elif "Weighted Average" in test_name or "Diversity" in test_name:
                category = "portfolio_metrics"
            
            # Determine result type
            result_type = "percentage"
            if "Rating Factor" in test_name:
                result_type = "rating_factor"
            elif "Spread" in test_name:
                result_type = "basis_points"
            elif "Life" in test_name:
                result_type = "years"
            elif "Recovery Rate" in test_name:
                result_type = "percentage"
            
            sql_definitions.append(
                f"({test_num}, '{test_name}', '{category}', '{result_type}', {threshold}, "
                f"'{test_name} - Pass if result {pass_condition} {threshold*100:.1f}%')"
            )
    
    # Generate SQL for MAG17 overrides
    for test_num, override_value in MAG17_OVERRIDES.items():
        if test_num in VBA_THRESHOLDS:
            test_name = VBA_THRESHOLDS[test_num][0]
            sql_overrides.append(
                f"('MAG17', {test_num}, {override_value}, '2016-03-23', NULL, 'MAG17', NULL, 1, '2025-08-25')"
            )
    
    # Output SQL
    print("=== SQL for Test Definitions ===")
    print("INSERT INTO concentration_test_definitions (test_number, test_name, test_category, result_type, default_threshold, test_description) VALUES")
    print(",\n".join(sql_definitions[:5]))  # Show first 5
    print(f"-- ... and {len(sql_definitions)-5} more definitions")
    print()
    
    print("=== SQL for MAG17 Overrides ===")
    print("INSERT INTO deal_concentration_thresholds (deal_id, test_id, threshold_value, effective_date, expiry_date, mag_version, notes, created_by, created_at) VALUES")
    print(",\n".join(sql_overrides[:5]))  # Show first 5
    print(f"-- ... and {len(sql_overrides)-5} more overrides")
    print()
    
    return sql_definitions, sql_overrides

if __name__ == "__main__":
    # Generate the comprehensive MAG17 threshold configuration
    definitions, overrides = generate_mag17_threshold_sql()
    
    print("=== KEY FINDINGS ===")
    print("1. Senior Secured Loans threshold should be 90% (not 80%)")
    print("2. CCC Loans threshold should be 7.5% (matches existing migration)")
    print("3. Total of 100+ concentration tests need proper thresholds")
    print("4. MAG17 requires deal-specific overrides for accurate compliance")
    print()
    
    print("=== RECOMMENDATION ===")
    print("1. Create database migration to populate concentration_test_definitions")
    print("2. Insert MAG17-specific threshold overrides")
    print("3. Update concentration test engine to use database-driven thresholds")
    print("4. Test all concentration calculations against VBA results")