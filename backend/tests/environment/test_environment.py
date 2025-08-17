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


def test_configuration():
    """Test configuration loading"""
    print("Testing Configuration...")
    print(f"✅ Environment: {settings.environment}")
    print(f"✅ Database URL: {settings.database_url}")
    print(f"✅ Redis URL: {settings.redis_url}")
    print(f"✅ Max Assets: {settings.max_assets}")
    print(f"✅ QuantLib Auto Date: {settings.quantlib_date_today_auto}")
    return True


def test_quantlib_integration():
    """Test QuantLib with configuration"""
    print("\nTesting QuantLib Integration...")
    
    # Test day count from config
    day_count = settings.default_day_count
    print(f"✅ Default Day Count: {day_count}")
    
    # Test date handling
    today = ql.Date.todaysDate()
    print(f"✅ Today's Date: {today}")
    
    # Test financial calculations
    rate = 0.05
    dc = ql.Actual360()
    compound_factor = (1 + rate * dc.yearFraction(ql.Date(1,1,2024), ql.Date(1,1,2025)))
    print(f"✅ Compound Factor (5%): {compound_factor:.6f}")
    
    return True


def test_database_connections():
    """Test all database connections"""
    print("\nTesting Database Connections...")
    
    # Test PostgreSQL
    if DatabaseManager.test_connection():
        print("✅ PostgreSQL: Connected")
    else:
        print("❌ PostgreSQL: Failed")
        return False
    
    # Test Redis
    if DatabaseManager.test_redis():
        print("✅ Redis: Connected")
    else:
        print("❌ Redis: Failed") 
        return False
    
    return True


def test_clo_calculations():
    """Test CLO-specific calculations"""
    print("\nTesting CLO Calculations...")
    
    # Simulate CLO asset portfolio (like VBA Asset.cls)
    np.random.seed(42)
    n_assets = 100  # Smaller test set
    
    assets = pd.DataFrame({
        'asset_id': [f'ASSET_{i:03d}' for i in range(n_assets)],
        'par_amount': np.random.uniform(1e6, 10e6, n_assets),
        'coupon_rate': np.random.uniform(0.03, 0.08, n_assets),
        'spread': np.random.uniform(0.01, 0.04, n_assets),
        'rating': np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB'], n_assets)
    })
    
    # Portfolio-level calculations
    total_par = assets['par_amount'].sum()
    weighted_coupon = np.average(assets['coupon_rate'], weights=assets['par_amount'])
    weighted_spread = np.average(assets['spread'], weights=assets['par_amount'])
    
    print(f"✅ Portfolio Size: {n_assets} assets")
    print(f"✅ Total Par: ${total_par:,.0f}")
    print(f"✅ Weighted Coupon: {weighted_coupon:.4f}")
    print(f"✅ Weighted Spread: {weighted_spread:.4f}")
    
    # Rating concentration (like compliance tests)
    rating_conc = assets.groupby('rating')['par_amount'].sum() / total_par
    print("✅ Rating Concentrations:")
    for rating, conc in rating_conc.items():
        print(f"   {rating}: {conc:.3%}")
    
    return True


def test_excel_equivalents():
    """Test Excel function equivalents"""
    print("\nTesting Excel Function Equivalents...")
    
    # YEARFRAC equivalent
    start_date = ql.Date(1, 1, 2024)
    end_date = ql.Date(1, 7, 2024)
    
    day_counts = {
        "Actual/360": ql.Actual360(),
        "30/360": ql.Thirty360(ql.Thirty360.USA),
        "Actual/365": ql.Actual365Fixed()
    }
    
    print("✅ YEARFRAC Equivalents:")
    for name, dc in day_counts.items():
        year_frac = dc.yearFraction(start_date, end_date)
        print(f"   {name}: {year_frac:.6f}")
    
    # Present Value calculation
    cash_flows = [1000, 1000, 1000, 101000]
    periods = [0.25, 0.5, 0.75, 1.0]
    rate = 0.05
    
    pv = sum([cf / ((1 + rate) ** t) for cf, t in zip(cash_flows, periods)])
    print(f"✅ Present Value: ${pv:.2f}")
    
    return True


def main():
    """Run complete environment test"""
    print("CLO Development Environment - Complete Test")
    print("=" * 60)
    print("Testing sophisticated Excel/VBA to Python conversion environment")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("QuantLib Integration", test_quantlib_integration),
        ("Database Connections", test_database_connections),
        ("CLO Calculations", test_clo_calculations),
        ("Excel Equivalents", test_excel_equivalents)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 ENVIRONMENT TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 SUCCESS: Complete CLO development environment ready!")
        print("🔥 All components working for VBA-to-Python conversion:")
        print("   - QuantLib financial mathematics")
        print("   - PostgreSQL + Redis databases")  
        print("   - Portfolio calculations")
        print("   - Excel function replacements")
        print("   - Configuration management")
        print("\n🚀 Ready to begin Asset.cls conversion!")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed")
        print("   Check configuration and connections before proceeding")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)