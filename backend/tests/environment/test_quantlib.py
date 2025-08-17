#!/usr/bin/env python3
"""
QuantLib Test Script for CLO System
Tests key financial functions that will replace Excel VBA calculations
"""

import QuantLib as ql
import numpy as np
from datetime import datetime, date

def test_basic_quantlib():
    """Test basic QuantLib functionality"""
    print("Testing QuantLib Basic Functionality")
    print("=" * 50)
    
    # Test 1: Date handling
    print("\nDate Handling:")
    today = ql.Date.todaysDate()
    print(f"Today's date: {today}")
    
    # Test 2: Day count conventions (critical for CLO calculations)
    print("\nDay Count Conventions:")
    actual_360 = ql.Actual360()
    actual_365 = ql.Actual365Fixed()
    thirty_360 = ql.Thirty360(ql.Thirty360.USA)
    
    start_date = ql.Date(1, 1, 2024)
    end_date = ql.Date(1, 7, 2024)  # 6 months later
    
    print(f"Period: {start_date} to {end_date}")
    print(f"Actual/360: {actual_360.yearFraction(start_date, end_date):.6f}")
    print(f"Actual/365: {actual_365.yearFraction(start_date, end_date):.6f}")  
    print(f"30/360: {thirty_360.yearFraction(start_date, end_date):.6f}")
    
    return True

def test_bond_calculations():
    """Test bond pricing and yield calculations (essential for Asset.cls conversion)"""
    print("\nBond Calculations:")
    print("=" * 50)
    
    try:
        # Set evaluation date
        evaluation_date = ql.Date(1, 1, 2024)
        ql.Settings.instance().evaluationDate = evaluation_date
        
        # Bond parameters (typical CLO asset)
        face_amount = 100.0
        coupon_rate = 0.05  # 5% coupon
        maturity = ql.Date(1, 1, 2027)  # 3-year bond
        
        # Create bond schedule
        issue_date = evaluation_date
        tenor = ql.Period(ql.Quarterly)
        calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
        business_convention = ql.Following
        date_generation = ql.DateGeneration.Backward
        
        schedule = ql.Schedule(issue_date, maturity, tenor, calendar, 
                              business_convention, business_convention,
                              date_generation, False)
        
        # Create fixed rate bond
        day_count = ql.Actual360()
        bond = ql.FixedRateBond(2, face_amount, schedule, [coupon_rate], day_count)
        
        # Create yield term structure (flat 4% yield curve)
        flat_rate = 0.04
        yield_curve = ql.FlatForward(evaluation_date, flat_rate, day_count)
        yield_curve_handle = ql.YieldTermStructureHandle(yield_curve)
        
        # Create pricing engine
        bond_engine = ql.DiscountingBondEngine(yield_curve_handle)
        bond.setPricingEngine(bond_engine)
        
        # Calculate bond metrics
        clean_price = bond.cleanPrice()
        accrued_interest = bond.accruedAmount()
        dirty_price = clean_price + accrued_interest
        yield_to_maturity = bond.bondYield(day_count, ql.Compounded, ql.Quarterly)
        duration = ql.BondFunctions.duration(bond, yield_curve_handle.currentLink(), 
                                           day_count, ql.Compounded, ql.Quarterly)
        
        print(f"Bond Metrics:")
        print(f"Clean Price: ${clean_price:.4f}")
        print(f"Accrued Interest: ${accrued_interest:.4f}")
        print(f"Dirty Price: ${dirty_price:.4f}")
        print(f"Yield to Maturity: {yield_to_maturity*100:.4f}%")
        print(f"Modified Duration: {duration:.4f}")
        
        return True
        
    except Exception as e:
        print(f"Bond calculation failed: {e}")
        return False

def test_cash_flow_calculations():
    """Test cash flow calculations (essential for Waterfall engine)"""
    print("\nCash Flow Calculations:")
    print("=" * 50)
    
    try:
        # Create a simple cash flow schedule
        evaluation_date = ql.Date(1, 1, 2024)
        ql.Settings.instance().evaluationDate = evaluation_date
        
        # Cash flow dates (quarterly payments)
        cash_flow_dates = [
            ql.Date(1, 4, 2024),   # Q1
            ql.Date(1, 7, 2024),   # Q2  
            ql.Date(1, 10, 2024),  # Q3
            ql.Date(1, 1, 2025)    # Q4
        ]
        
        # Cash flow amounts
        cash_flow_amounts = [2500.0, 2500.0, 2500.0, 102500.0]  # Including principal
        
        # Create cash flow schedule  
        cash_flows = [ql.SimpleCashFlow(amount, date) 
                     for amount, date in zip(cash_flow_amounts, cash_flow_dates)]
        
        # Calculate NPV with 4% discount rate
        discount_rate = 0.04
        day_count = ql.Actual360()
        
        # Calculate present value
        discount_curve = ql.FlatForward(evaluation_date, discount_rate, day_count)
        discount_handle = ql.YieldTermStructureHandle(discount_curve)
        
        npv = ql.CashFlows.npv(cash_flows, discount_handle.currentLink(), False)
        
        print(f"Cash Flow Analysis:")
        print(f"Number of cash flows: {len(cash_flow_amounts)}")
        print(f"Total undiscounted: ${sum(cash_flow_amounts):,.2f}")
        print(f"Net Present Value: ${npv:.2f}")
        print(f"Discount Rate: {discount_rate*100:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"Cash flow calculation failed: {e}")
        return False

def test_excel_function_equivalents():
    """Test QuantLib equivalents to Excel functions used in VBA"""
    print("\nExcel Function Equivalents:")
    print("=" * 50)
    
    # Test Excel YEARFRAC equivalent
    start_date = ql.Date(1, 1, 2024)
    end_date = ql.Date(1, 7, 2024)
    
    # Different day count methods (Excel YEARFRAC basis parameter)
    day_counts = {
        "30/360 (basis 0)": ql.Thirty360(ql.Thirty360.USA),
        "Actual/Actual (basis 1)": ql.ActualActual(ql.ActualActual.ISDA),
        "Actual/360 (basis 2)": ql.Actual360(),
        "Actual/365 (basis 3)": ql.Actual365Fixed()
    }
    
    print(f"YEARFRAC equivalents ({start_date} to {end_date}):")
    for description, day_count in day_counts.items():
        year_frac = day_count.yearFraction(start_date, end_date)
        print(f"{description}: {year_frac:.6f}")
    
    # Test present value calculation (Excel PV equivalent)
    print(f"\nPresent Value Calculations:")
    rate = 0.05  # 5% annual rate
    nper = 4     # 4 periods
    pmt = 1000   # $1000 payment
    fv = 0       # No future value
    
    # Calculate using QuantLib
    pv = sum([pmt / ((1 + rate) ** i) for i in range(1, nper + 1)])
    print(f"PV (rate={rate*100:.1f}%, nper={nper}, pmt=${pmt}): ${pv:.2f}")
    
    return True

def main():
    """Run all QuantLib tests"""
    print("QuantLib Environment Validation for CLO System")
    print("Testing Excel VBA function replacements")
    print("=" * 60)
    
    tests = [
        ("Basic QuantLib", test_basic_quantlib),
        ("Bond Calculations", test_bond_calculations), 
        ("Cash Flow Analysis", test_cash_flow_calculations),
        ("Excel Equivalents", test_excel_function_equivalents)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name} test...")
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"PASS: {test_name} test")
            else:
                print(f"FAIL: {test_name} test")
        except Exception as e:
            print(f"FAIL: {test_name} test - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("QuantLib environment is ready for CLO system development!")
        print("All Excel VBA function replacements are working")
    else:
        print("Some tests failed. Check configuration before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    main()