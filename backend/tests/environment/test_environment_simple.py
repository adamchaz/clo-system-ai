#!/usr/bin/env python3
"""
Complete CLO Development Environment Test
Tests all components needed for VBA-to-Python conversion
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import DatabaseManager
import QuantLib as ql
import pandas as pd
import numpy as np


def test_all_components():
    """Test all environment components"""
    print("CLO Development Environment - Complete Test")
    print("=" * 60)
    
    success_count = 0
    total_tests = 5
    
    # Test 1: Configuration
    try:
        print("\n1. Testing Configuration...")
        print(f"   Environment: {settings.environment}")
        print(f"   Database URL: {settings.database_url}")
        print(f"   Redis URL: {settings.redis_url}")
        print("   PASS: Configuration")
        success_count += 1
    except Exception as e:
        print(f"   FAIL: Configuration - {e}")
    
    # Test 2: QuantLib
    try:
        print("\n2. Testing QuantLib...")
        today = ql.Date.todaysDate()
        dc = ql.Actual360()
        year_frac = dc.yearFraction(ql.Date(1,1,2024), ql.Date(1,7,2024))
        print(f"   Today: {today}")
        print(f"   YEARFRAC (6 months): {year_frac:.6f}")
        print("   PASS: QuantLib")
        success_count += 1
    except Exception as e:
        print(f"   FAIL: QuantLib - {e}")
    
    # Test 3: Database
    try:
        print("\n3. Testing Databases...")
        db_ok = DatabaseManager.test_connection()
        redis_ok = DatabaseManager.test_redis()
        print(f"   PostgreSQL: {'Connected' if db_ok else 'Failed'}")
        print(f"   Redis: {'Connected' if redis_ok else 'Failed'}")
        if db_ok and redis_ok:
            print("   PASS: Databases")
            success_count += 1
        else:
            print("   FAIL: Databases")
    except Exception as e:
        print(f"   FAIL: Databases - {e}")
    
    # Test 4: Portfolio calculations
    try:
        print("\n4. Testing Portfolio Calculations...")
        np.random.seed(42)
        n_assets = 100
        par_amounts = np.random.uniform(1e6, 10e6, n_assets)
        coupon_rates = np.random.uniform(0.03, 0.08, n_assets)
        
        total_par = par_amounts.sum()
        weighted_coupon = np.average(coupon_rates, weights=par_amounts)
        
        print(f"   Portfolio: {n_assets} assets")
        print(f"   Total Par: ${total_par:,.0f}")
        print(f"   Weighted Coupon: {weighted_coupon:.4f}")
        print("   PASS: Portfolio Calculations")
        success_count += 1
    except Exception as e:
        print(f"   FAIL: Portfolio Calculations - {e}")
    
    # Test 5: Excel equivalents
    try:
        print("\n5. Testing Excel Equivalents...")
        # YEARFRAC test
        start_date = ql.Date(1, 1, 2024)
        end_date = ql.Date(1, 7, 2024)
        
        actual360 = ql.Actual360().yearFraction(start_date, end_date)
        thirty360 = ql.Thirty360(ql.Thirty360.USA).yearFraction(start_date, end_date)
        
        # PV test
        cash_flows = [1000, 1000, 1000, 101000]
        periods = [0.25, 0.5, 0.75, 1.0]
        rate = 0.05
        pv = sum([cf / ((1 + rate) ** t) for cf, t in zip(cash_flows, periods)])
        
        print(f"   Actual/360: {actual360:.6f}")
        print(f"   30/360: {thirty360:.6f}")
        print(f"   Present Value: ${pv:.2f}")
        print("   PASS: Excel Equivalents")
        success_count += 1
    except Exception as e:
        print(f"   FAIL: Excel Equivalents - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("ENVIRONMENT TEST SUMMARY")
    print("=" * 60)
    print(f"Overall: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("\nSUCCESS: Complete CLO development environment ready!")
        print("All components working for VBA-to-Python conversion:")
        print("  - QuantLib financial mathematics")
        print("  - PostgreSQL + Redis databases")
        print("  - Portfolio calculations")
        print("  - Excel function replacements")
        print("  - Configuration management")
        print("\nReady to begin Asset.cls conversion!")
        return True
    else:
        print(f"\n{total_tests - success_count} test(s) failed")
        print("Check configuration and connections before proceeding")
        return False


if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)