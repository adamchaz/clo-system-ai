#!/usr/bin/env python3
"""
Essential QuantLib Test - Core functionality for CLO VBA conversion
Tests the most critical functions needed to replace Excel VBA calculations
"""

import QuantLib as ql
import numpy as np

def test_core_functionality():
    """Test the essential QuantLib functions for CLO system"""
    print("QuantLib Essential Functions Test")
    print("=" * 50)
    
    # 1. Date handling (essential for CLO calculations)
    print("\n1. Date Handling:")
    today = ql.Date.todaysDate()
    start_date = ql.Date(1, 1, 2024)
    end_date = ql.Date(1, 7, 2024)
    print(f"Today: {today}")
    print(f"Start: {start_date}, End: {end_date}")
    
    # 2. Day count conventions (replaces Excel YEARFRAC)
    print("\n2. Day Count Conventions (Excel YEARFRAC replacements):")
    day_counts = {
        "30/360": ql.Thirty360(ql.Thirty360.USA),
        "Actual/360": ql.Actual360(), 
        "Actual/365": ql.Actual365Fixed(),
        "Act/Act": ql.ActualActual(ql.ActualActual.ISDA)
    }
    
    for name, dc in day_counts.items():
        year_frac = dc.yearFraction(start_date, end_date)
        print(f"{name:12}: {year_frac:.6f}")
    
    # 3. Interest rate calculations
    print("\n3. Interest Rate Calculations:")
    rate = 0.05  # 5%
    dc = ql.Actual360()
    compounding = ql.Compounded
    frequency = ql.Quarterly
    
    interest_rate = ql.InterestRate(rate, dc, compounding, frequency)
    discount_factor = interest_rate.discountFactor(1.0)  # 1 year
    compound_factor = interest_rate.compoundFactor(1.0)
    
    print(f"5% Interest Rate:")
    print(f"Discount Factor (1Y): {discount_factor:.6f}")
    print(f"Compound Factor (1Y): {compound_factor:.6f}")
    
    # 4. Simple Present Value calculations
    print("\n4. Present Value Calculations:")
    cash_flows = [1000, 1000, 1000, 101000]  # Quarterly payments + principal
    periods = [0.25, 0.5, 0.75, 1.0]  # Time to payment
    
    pv = sum([cf * interest_rate.discountFactor(t) for cf, t in zip(cash_flows, periods)])
    print(f"Cash flows: {cash_flows}")
    print(f"Present Value: ${pv:.2f}")
    
    # 5. Date arithmetic (essential for CLO payment schedules)
    print("\n5. Date Arithmetic:")
    quarterly_dates = []
    current_date = ql.Date(1, 1, 2024)
    
    for i in range(4):
        quarterly_dates.append(current_date)
        current_date = current_date + ql.Period(3, ql.Months)
    
    print("Quarterly payment dates:")
    for i, date in enumerate(quarterly_dates, 1):
        print(f"Q{i}: {date}")
    
    return True

def test_numpy_integration():
    """Test NumPy integration for array operations (replaces VBA arrays)"""
    print("\n" + "=" * 50)
    print("NumPy Integration Test")
    print("=" * 50)
    
    # Asset portfolio simulation (1000 assets like the CLO system)
    np.random.seed(42)  # For reproducible results
    
    # Simulate asset data (like Asset.cls in VBA)
    n_assets = 1000
    asset_data = {
        'par_amounts': np.random.uniform(100000, 10000000, n_assets),
        'coupon_rates': np.random.uniform(0.02, 0.12, n_assets),
        'spreads': np.random.uniform(0.001, 0.05, n_assets),
        'ratings': np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB', 'B'], n_assets)
    }
    
    print(f"\n1. Portfolio Statistics ({n_assets} assets):")
    print(f"Total Par Amount: ${asset_data['par_amounts'].sum():,.0f}")
    print(f"Avg Coupon Rate: {asset_data['coupon_rates'].mean():.4f}")
    print(f"Avg Spread: {asset_data['spreads'].mean():.4f}")
    
    # Weighted calculations (common in CLO waterfall logic)
    weights = asset_data['par_amounts'] / asset_data['par_amounts'].sum()
    weighted_coupon = np.sum(asset_data['coupon_rates'] * weights)
    weighted_spread = np.sum(asset_data['spreads'] * weights)
    
    print(f"\n2. Weighted Portfolio Metrics:")
    print(f"Weighted Avg Coupon: {weighted_coupon:.4f}")
    print(f"Weighted Avg Spread: {weighted_spread:.4f}")
    
    # Concentration analysis (like compliance testing in VBA)
    rating_concentrations = {}
    total_par = asset_data['par_amounts'].sum()
    
    for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']:
        mask = asset_data['ratings'] == rating
        concentration = asset_data['par_amounts'][mask].sum() / total_par
        rating_concentrations[rating] = concentration
    
    print(f"\n3. Rating Concentrations:")
    for rating, conc in rating_concentrations.items():
        print(f"{rating}: {conc:.3%}")
    
    return True

def main():
    """Run essential QuantLib tests"""
    print("QuantLib Environment Validation - Essential Features")
    print("Testing core functionality needed for CLO VBA conversion")
    print("=" * 60)
    
    success = True
    
    try:
        success &= test_core_functionality()
        success &= test_numpy_integration()
        
        print("\n" + "=" * 60)
        if success:
            print("SUCCESS: Essential QuantLib functionality is working!")
            print("Environment is ready for CLO system development.")
            print("\nKey capabilities validated:")
            print("- Date handling and arithmetic")
            print("- Day count conventions (Excel YEARFRAC replacement)")
            print("- Interest rate calculations")
            print("- Present value computations")
            print("- NumPy array operations (VBA array replacement)")
            print("- Portfolio analytics and concentration testing")
        else:
            print("PARTIAL: Some tests failed, but core functionality works.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    main()