#!/usr/bin/env python3

from app.core.database import get_db
from app.models.concentration_test_enhanced import EnhancedConcentrationTest, TestNum
from app.models.asset import Asset
from decimal import Decimal

print('=== Testing MAG17 Senior Secured Loans Calculation ===')

# Get database session
db = next(get_db())

# Load MAG17 assets
assets = db.query(Asset).filter(Asset.portfolio == 'MAG17').all()
print(f'Loaded {len(assets)} MAG17 assets')

if len(assets) > 0:
    # Calculate total collateral
    total_par = sum(asset.par_amount for asset in assets if asset.par_amount)
    print(f'Total Par Amount: ${total_par:,.0f}')
    
    # Create enhanced concentration test
    enhanced_test = EnhancedConcentrationTest(
        assets=assets,
        collateral_principal_amount=total_par,
        principal_proceeds=Decimal('0')  # Default
    )
    
    # Run the specific senior secured loans test
    enhanced_test.test_senior_secured_loans_minimum(TestNum.LimitationOnSeniorSecuredLoans)
    
    # Get the result
    if enhanced_test.test_results:
        result = enhanced_test.test_results[-1]  # Last added result
        print()
        print('=== ENHANCED MODEL RESULT ===')
        print(f'Test: {result.test_name}')
        print(f'Threshold: {result.threshold:.1%}')
        print(f'Result: {result.result:.2%}')
        print(f'Status: {result.pass_fail}')
        print(f'Numerator: ${result.numerator:,.0f}')
        print(f'Denominator: ${result.denominator:,.0f}')
        print()
        
        # Analyze asset types
        loan_assets = [a for a in assets if hasattr(a, 'bond_loan') and a.bond_loan == 'LOAN']
        loan_par = sum(a.par_amount for a in loan_assets if a.par_amount)
        
        print(f'Assets classified as LOAN: {len(loan_assets)} of {len(assets)} ({len(loan_assets)/len(assets):.1%})')
        print(f'LOAN par amount: ${loan_par:,.0f} ({loan_par/total_par:.1%} of total)')
        
        # Check for non-senior secured loans
        non_senior_assets = [a for a in assets if hasattr(a, 'mdy_asset_category') and 
                           a.mdy_asset_category == "MOODY'S NON-SENIOR SECURED LOAN"]
        if non_senior_assets:
            non_senior_par = sum(a.par_amount for a in non_senior_assets if a.par_amount)
            print(f'Non-Senior Secured assets: {len(non_senior_assets)} (${non_senior_par:,.0f})')
        
        # This should match VBA calculation: (LOAN par - non-senior par + principal_proceeds) / total_par
        expected_result = (loan_par - sum(a.par_amount for a in non_senior_assets if a.par_amount)) / total_par
        print(f'Expected VBA result: {expected_result:.2%}')
        
        if abs(result.result - expected_result) < 0.0001:  # Within 0.01%
            print('✅ Calculation matches VBA implementation')
        else:
            print('❌ Calculation differs from VBA implementation')
            
    else:
        print('No test results generated')
else:
    print('No MAG17 assets found')