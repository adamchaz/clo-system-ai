"""
Test suite for Yield Curve and Asset Integration

Tests the complete integration of yield curve system with Asset pricing functionality
to ensure seamless operation and accurate fair value calculations.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.core.database import Base
from app.models.asset import Asset, AssetFlags
from app.models.yield_curve import (
    YieldCurve,
    YieldCurveService,
    YieldCurveModel,
    YieldCurveRateModel,
    ForwardRateModel
)


@pytest.fixture
def integrated_db():
    """Create in-memory database with both asset and yield curve data"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def sample_yield_curves(integrated_db):
    """Create sample yield curves for testing"""
    yield_curve_service = YieldCurveService(integrated_db)
    analysis_date = date(2025, 1, 10)
    
    # Treasury curve
    treasury_rates = {
        1: 0.0450,   # 1 month: 4.50%
        3: 0.0465,   # 3 month: 4.65%
        6: 0.0485,   # 6 month: 4.85%
        12: 0.0520,  # 1 year: 5.20%
        24: 0.0565,  # 2 year: 5.65%
        36: 0.0595,  # 3 year: 5.95%
        60: 0.0625,  # 5 year: 6.25%
        120: 0.0675, # 10 year: 6.75%
        240: 0.0705, # 20 year: 7.05%
        360: 0.0715  # 30 year: 7.15%
    }
    
    # SOFR curve (slightly lower)
    sofr_rates = {k: v - 0.0025 for k, v in treasury_rates.items()}
    
    # Credit curves (higher spreads)
    aaa_credit_rates = {k: v + 0.0050 for k, v in treasury_rates.items()}
    bbb_credit_rates = {k: v + 0.0150 for k, v in treasury_rates.items()}
    
    curves = {}
    
    # Create yield curves
    curves['USD_TREASURY'] = yield_curve_service.create_yield_curve(
        'USD_TREASURY', analysis_date, treasury_rates, 'GOVERNMENT', 'USD'
    )
    
    curves['USD_SOFR'] = yield_curve_service.create_yield_curve(
        'USD_SOFR', analysis_date, sofr_rates, 'INTERBANK', 'USD'
    )
    
    curves['USD_CREDIT_AAA'] = yield_curve_service.create_yield_curve(
        'USD_CREDIT_AAA', analysis_date, aaa_credit_rates, 'CREDIT', 'USD'
    )
    
    curves['USD_CREDIT_BBB'] = yield_curve_service.create_yield_curve(
        'USD_CREDIT_BBB', analysis_date, bbb_credit_rates, 'CREDIT', 'USD'
    )
    
    return curves, yield_curve_service


@pytest.fixture
def sample_assets(integrated_db):
    """Create sample assets for pricing tests"""
    assets_data = [
        {
            'blkrock_id': 'BOND_AAA_001',
            'issue_name': 'High Grade Corp Bond',
            'issuer_name': 'AAA Corp Inc',
            'par_amount': Decimal('5000000'),
            'bond_loan': 'BOND',
            'seniority': 'SENIOR UNSECURED',
            'sp_issuer_rating': 'AA',
            'mdy_issuer_rating': 'Aa2',
            'maturity': date(2028, 6, 15),
            'coupon': Decimal('0.055'),
            'coupon_type': 'FIXED',
            'sector': 'INDUSTRIALS',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        },
        {
            'blkrock_id': 'LOAN_BBB_002',
            'issue_name': 'Term Loan B',
            'issuer_name': 'BBB Company LLC',
            'par_amount': Decimal('3000000'),
            'bond_loan': 'LOAN',
            'seniority': 'SENIOR SECURED',
            'sp_issuer_rating': 'BBB',
            'mdy_issuer_rating': 'Baa2',
            'maturity': date(2029, 12, 1),
            'coupon': Decimal('0.075'),
            'coupon_type': 'FLOATING',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        },
        {
            'blkrock_id': 'HY_BOND_003',
            'issue_name': 'High Yield Bond',
            'issuer_name': 'HY Corp',
            'par_amount': Decimal('2000000'),
            'bond_loan': 'BOND',
            'seniority': 'SENIOR UNSECURED',
            'sp_issuer_rating': 'B+',
            'mdy_issuer_rating': 'B1',
            'maturity': date(2027, 3, 31),
            'coupon': Decimal('0.085'),
            'coupon_type': 'FIXED',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        },
        {
            'blkrock_id': 'GOVT_BOND_004',
            'issue_name': 'Treasury Bond',
            'issuer_name': 'US Government',
            'par_amount': Decimal('1000000'),
            'bond_loan': 'BOND',
            'seniority': 'SENIOR UNSECURED',
            'sp_issuer_rating': 'AAA',
            'maturity': date(2035, 5, 15),
            'coupon': Decimal('0.045'),
            'coupon_type': 'FIXED',
            'sector': 'GOVERNMENT',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        }
    ]
    
    assets = []
    for asset_data in assets_data:
        asset = Asset(**asset_data)
        integrated_db.add(asset)
        assets.append(asset)
    
    integrated_db.commit()
    return assets


class TestYieldCurveAssetIntegration:
    """Test Asset model integration with yield curve pricing"""
    
    def test_asset_update_fair_value_basic(self, integrated_db, sample_yield_curves, sample_assets):
        """Test basic fair value update functionality"""
        curves, yield_curve_service = sample_yield_curves
        aaa_bond = sample_assets[0]  # BOND_AAA_001
        
        # Update fair value
        pricing_date = date(2025, 1, 10)
        results = aaa_bond.update_fair_value(
            yield_curve_service=yield_curve_service,
            curve_name='USD_CREDIT_AAA',
            credit_spread_bps=75,
            pricing_date=pricing_date
        )
        
        # Verify results structure
        assert results is not None
        assert 'fair_value' in results
        assert 'discount_curve' in results
        assert 'credit_spread_bps' in results
        assert 'pricing_date' in results
        assert 'cash_flow_count' in results
        
        # Verify asset was updated
        assert aaa_bond.fair_value is not None
        assert aaa_bond.fair_value > Decimal('0')
        assert aaa_bond.fair_value_date == pricing_date
        assert aaa_bond.discount_curve_name == 'USD_CREDIT_AAA'
        assert aaa_bond.pricing_spread_bps == 75
        
        # Fair value should be less than par (positive discount rate)
        assert aaa_bond.fair_value < aaa_bond.par_amount
        
        # Verify cash flows were generated
        assert results['cash_flow_count'] > 0
    
    def test_default_curve_selection(self, integrated_db, sample_yield_curves, sample_assets):
        """Test automatic discount curve selection"""
        curves, yield_curve_service = sample_yield_curves
        
        # Test different asset types
        aaa_bond = sample_assets[0]   # AA rated
        bbb_loan = sample_assets[1]   # BBB rated, floating
        hy_bond = sample_assets[2]    # B+ rated
        govt_bond = sample_assets[3]  # Government sector
        
        # Test curve selection
        assert aaa_bond._select_default_discount_curve() == 'USD_CREDIT_AAA'
        assert bbb_loan._select_default_discount_curve() == 'USD_SOFR'  # Floating rate
        assert hy_bond._select_default_discount_curve() == 'USD_CREDIT_BBB'
        assert govt_bond._select_default_discount_curve() == 'USD_TREASURY'  # Government
    
    def test_credit_spread_estimation(self, sample_assets):
        """Test automatic credit spread estimation"""
        aaa_bond = sample_assets[0]   # AA rated
        bbb_loan = sample_assets[1]   # BBB rated, senior secured
        hy_bond = sample_assets[2]    # B+ rated
        
        # Test spread estimation
        aaa_spread = aaa_bond._estimate_credit_spread()
        bbb_spread = bbb_loan._estimate_credit_spread()
        hy_spread = hy_bond._estimate_credit_spread()
        
        # Spreads should increase with risk
        assert aaa_spread < bbb_spread
        assert bbb_spread < hy_spread
        
        # Senior secured should get discount
        assert bbb_spread < 150  # Should be less than base BBB spread due to senior secured
        
        # Reasonable ranges
        assert 50 <= aaa_spread <= 100   # AA range
        assert 100 <= bbb_spread <= 150  # BBB range (discounted)
        assert 400 <= hy_spread <= 600   # B range
    
    def test_cash_flow_generation_bond(self, sample_assets):
        """Test cash flow generation for bond assets"""
        bond = sample_assets[0]  # Semi-annual bond
        pricing_date = date(2025, 1, 10)
        
        cash_flows = bond._generate_cash_flows(pricing_date)
        
        # Should have cash flows
        assert len(cash_flows) > 0
        
        # All cash flows should be after pricing date
        for cf_date, cf_amount in cash_flows:
            assert cf_date > pricing_date
            assert cf_amount > Decimal('0')
        
        # Last cash flow should be at maturity (principal + interest)
        last_cf_date, last_cf_amount = cash_flows[-1]
        assert last_cf_date == bond.maturity
        assert last_cf_amount >= bond.par_amount  # Should include principal
        
        # Should have periodic interest payments
        interest_flows = [cf for cf in cash_flows[:-1]]  # Exclude final payment
        if len(interest_flows) > 0:
            # Interest payments should be consistent
            expected_interest = bond.par_amount * (bond.coupon / 2)  # Semi-annual
            for cf_date, cf_amount in interest_flows:
                # Allow for some variation due to payment scheduling
                assert abs(cf_amount - expected_interest) < expected_interest * Decimal('0.1')
    
    def test_cash_flow_generation_loan(self, sample_assets):
        """Test cash flow generation for loan assets"""
        loan = sample_assets[1]  # Quarterly loan
        pricing_date = date(2025, 1, 10)
        
        cash_flows = loan._generate_cash_flows(pricing_date)
        
        # Should have cash flows
        assert len(cash_flows) > 0
        
        # Last cash flow should be principal at maturity
        last_cf_date, last_cf_amount = cash_flows[-1]
        assert last_cf_date == loan.maturity
        assert last_cf_amount >= loan.par_amount
        
        # Should have quarterly interest payments
        if len(cash_flows) > 1:
            quarterly_interest = loan.par_amount * (loan.coupon / 4)
            interest_flows = cash_flows[:-1]  # Exclude final payment
            
            for cf_date, cf_amount in interest_flows:
                # Check that quarterly interests are reasonable
                assert cf_amount > Decimal('0')
                assert abs(cf_amount - quarterly_interest) < quarterly_interest * Decimal('0.2')
    
    def test_fair_value_calculation_accuracy(self, integrated_db, sample_yield_curves, sample_assets):
        """Test accuracy of fair value calculation"""
        curves, yield_curve_service = sample_yield_curves
        bond = sample_assets[0]
        
        # Test with known parameters
        pricing_date = date(2025, 1, 10)
        curve_name = 'USD_TREASURY'
        spread_bps = 100  # 1%
        
        results = bond.update_fair_value(
            yield_curve_service, curve_name, spread_bps, pricing_date
        )
        
        # Manual verification - generate cash flows and discount
        cash_flows = bond._generate_cash_flows(pricing_date)
        discount_curve = yield_curve_service.load_yield_curve(curve_name, pricing_date)
        
        manual_pv = Decimal('0')
        spread_decimal = Decimal('0.01')  # 100 bps
        
        for cf_date, cf_amount in cash_flows:
            base_rate = discount_curve.zero_rate(pricing_date, cf_date)
            total_rate = base_rate + float(spread_decimal)
            years_to_cf = (cf_date - pricing_date).days / 365.25
            discount_factor = Decimal(str((1 + total_rate) ** -years_to_cf))
            manual_pv += cf_amount * discount_factor
        
        manual_pv = manual_pv.quantize(Decimal('0.01'))
        
        # Should match calculated fair value
        assert abs(bond.fair_value - manual_pv) < Decimal('0.01')
    
    def test_fair_value_sensitivity_to_spreads(self, integrated_db, sample_yield_curves, sample_assets):
        """Test fair value sensitivity to credit spreads"""
        curves, yield_curve_service = sample_yield_curves
        bond = sample_assets[0]
        pricing_date = date(2025, 1, 10)
        
        # Test different spreads
        spreads = [50, 100, 200, 500]  # basis points
        fair_values = []
        
        for spread in spreads:
            bond.update_fair_value(yield_curve_service, 'USD_TREASURY', spread, pricing_date)
            fair_values.append(bond.fair_value)
        
        # Fair values should decrease as spreads increase (higher discount rate)
        for i in range(1, len(fair_values)):
            assert fair_values[i] < fair_values[i-1]
        
        # Reasonable sensitivity - higher spreads should have meaningful impact
        spread_impact = fair_values[0] - fair_values[-1]
        assert spread_impact > bond.par_amount * Decimal('0.05')  # At least 5% impact
    
    def test_fair_value_analytics(self, integrated_db, sample_yield_curves, sample_assets):
        """Test fair value analytics generation"""
        curves, yield_curve_service = sample_yield_curves
        bond = sample_assets[0]
        
        # Update fair value first
        pricing_date = date(2025, 1, 10)
        bond.update_fair_value(yield_curve_service, pricing_date=pricing_date)
        
        # Get analytics
        analytics = bond.get_fair_value_analytics()
        
        # Verify structure
        assert 'asset_id' in analytics
        assert 'current_fair_value' in analytics
        assert 'par_amount' in analytics
        assert 'fair_value_ratio' in analytics
        assert 'pricing_info' in analytics
        assert 'asset_characteristics' in analytics
        
        # Verify content
        assert analytics['asset_id'] == bond.blkrock_id
        assert analytics['current_fair_value'] == float(bond.fair_value)
        assert analytics['par_amount'] == float(bond.par_amount)
        
        # Fair value ratio should be reasonable
        fv_ratio = analytics['fair_value_ratio']
        assert fv_ratio > 0.7  # Should be at least 70% of par
        assert fv_ratio < 1.1  # Should be at most 110% of par
        
        # Verify pricing info
        pricing_info = analytics['pricing_info']
        assert pricing_info['discount_curve'] == bond.discount_curve_name
        assert pricing_info['credit_spread_bps'] == bond.pricing_spread_bps
        assert pricing_info['pricing_date'] == bond.fair_value_date
        
        # Verify asset characteristics
        characteristics = analytics['asset_characteristics']
        assert characteristics['maturity'] == bond.maturity
        assert characteristics['coupon'] == float(bond.coupon)
        assert characteristics['seniority'] == bond.seniority


class TestYieldCurveServiceIntegration:
    """Test YieldCurveService integration with asset pricing"""
    
    def test_present_value_calculation_service(self, integrated_db, sample_yield_curves):
        """Test present value calculation via service"""
        curves, yield_curve_service = sample_yield_curves
        
        # Test cash flows
        analysis_date = date(2025, 1, 10)
        cash_flows = [
            (date(2026, 1, 10), Decimal('50000')),   # 1 year: $50k interest
            (date(2027, 1, 10), Decimal('50000')),   # 2 years: $50k interest  
            (date(2028, 1, 10), Decimal('1050000')), # 3 years: $50k interest + $1M principal
        ]
        
        # Calculate PV using different curves
        treasury_pv = yield_curve_service.calculate_present_value(
            cash_flows, 'USD_TREASURY', analysis_date
        )
        
        credit_pv = yield_curve_service.calculate_present_value(
            cash_flows, 'USD_CREDIT_BBB', analysis_date
        )
        
        # Both should be positive and less than total cash flows
        total_cf = sum(cf[1] for cf in cash_flows)
        assert treasury_pv > Decimal('0')
        assert credit_pv > Decimal('0')
        assert treasury_pv < total_cf
        assert credit_pv < total_cf
        
        # Credit curve PV should be lower (higher rates)
        assert credit_pv < treasury_pv
    
    def test_bulk_asset_pricing(self, integrated_db, sample_yield_curves, sample_assets):
        """Test bulk asset pricing performance"""
        curves, yield_curve_service = sample_yield_curves
        pricing_date = date(2025, 1, 10)
        
        # Price all assets
        pricing_results = []
        for asset in sample_assets:
            result = asset.update_fair_value(
                yield_curve_service=yield_curve_service,
                pricing_date=pricing_date
            )
            pricing_results.append((asset.blkrock_id, result))
        
        # All assets should have been priced
        successful_pricing = [r for r in pricing_results if r[1] is not None]
        assert len(successful_pricing) == len(sample_assets)
        
        # Verify all assets have fair values
        for asset in sample_assets:
            assert asset.fair_value is not None
            assert asset.fair_value > Decimal('0')
            assert asset.fair_value_date == pricing_date
            assert asset.discount_curve_name is not None


class TestYieldCurveEdgeCasesIntegration:
    """Test edge cases in yield curve and asset integration"""
    
    def test_asset_with_missing_maturity(self, integrated_db, sample_yield_curves):
        """Test asset pricing with missing maturity date"""
        curves, yield_curve_service = sample_yield_curves
        
        # Asset with no maturity
        asset = Asset(
            blkrock_id='NO_MATURITY_001',
            issue_name='Perpetual Bond',
            issuer_name='Test Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            coupon=Decimal('0.05')
        )
        
        # Should handle gracefully
        result = asset.update_fair_value(yield_curve_service)
        
        # Should return None due to no cash flows
        assert result is None
        assert asset.fair_value is None
    
    def test_asset_with_past_maturity(self, integrated_db, sample_yield_curves):
        """Test asset pricing with maturity in the past"""
        curves, yield_curve_service = sample_yield_curves
        
        # Asset with past maturity
        asset = Asset(
            blkrock_id='PAST_MAT_001',
            issue_name='Expired Bond',
            issuer_name='Test Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            maturity=date(2020, 1, 1),  # Past maturity
            coupon=Decimal('0.05')
        )
        
        # Should handle gracefully
        result = asset.update_fair_value(yield_curve_service)
        
        # Should return None due to no future cash flows
        assert result is None
    
    def test_asset_pricing_with_missing_curve(self, integrated_db, sample_yield_curves):
        """Test asset pricing with non-existent yield curve"""
        curves, yield_curve_service = sample_yield_curves
        
        asset = Asset(
            blkrock_id='MISSING_CURVE_001',
            issue_name='Test Bond',
            issuer_name='Test Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            maturity=date(2028, 1, 1),
            coupon=Decimal('0.05')
        )
        
        # Try to use non-existent curve
        result = asset.update_fair_value(
            yield_curve_service,
            curve_name='NONEXISTENT_CURVE'
        )
        
        # Should return None gracefully
        assert result is None
        assert asset.fair_value is None
    
    def test_zero_coupon_asset_pricing(self, integrated_db, sample_yield_curves):
        """Test pricing of zero-coupon assets"""
        curves, yield_curve_service = sample_yield_curves
        
        # Zero coupon bond
        zero_coupon_bond = Asset(
            blkrock_id='ZERO_COUPON_001',
            issue_name='Zero Coupon Bond',
            issuer_name='Test Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            seniority='SENIOR UNSECURED',
            maturity=date(2030, 1, 1),
            coupon=Decimal('0'),  # Zero coupon
            sp_issuer_rating='BBB'
        )
        
        integrated_db.add(zero_coupon_bond)
        integrated_db.commit()
        
        result = zero_coupon_bond.update_fair_value(yield_curve_service)
        
        # Should still work - only principal payment at maturity
        assert result is not None
        assert zero_coupon_bond.fair_value is not None
        assert zero_coupon_bond.fair_value > Decimal('0')
        
        # Should be significantly discounted
        assert zero_coupon_bond.fair_value < zero_coupon_bond.par_amount * Decimal('0.8')


class TestVBAYieldCurveComparison:
    """Test VBA comparison for yield curve calculations"""
    
    def test_vba_forward_rate_accuracy_in_pricing(self, integrated_db, sample_yield_curves, sample_assets):
        """Test that VBA-accurate forward rates produce correct pricing"""
        curves, yield_curve_service = sample_yield_curves
        bond = sample_assets[0]
        
        # Get the treasury curve (has VBA-exact forward rates)
        treasury_curve = curves['USD_TREASURY']
        
        # Verify forward rates are calculated using VBA formula
        assert treasury_curve._is_setup
        assert len(treasury_curve.forward_dict) > 0
        
        # Test that forward rates are used correctly in zero rate calculation
        test_date_start = treasury_curve.analysis_date
        test_date_end = test_date_start + relativedelta(months=18)
        
        zero_rate = treasury_curve.zero_rate(test_date_start, test_date_end)
        
        # Should be reasonable rate
        assert 0.04 < zero_rate < 0.08
        
        # Use in asset pricing
        result = bond.update_fair_value(
            yield_curve_service, 'USD_TREASURY', 
            credit_spread_bps=100, 
            pricing_date=test_date_start
        )
        
        # Should produce reasonable fair value
        assert result is not None
        assert bond.fair_value > bond.par_amount * Decimal('0.7')
        assert bond.fair_value < bond.par_amount * Decimal('1.1')
    
    def test_interpolation_accuracy_in_asset_pricing(self, integrated_db, sample_yield_curves):
        """Test VBA-accurate interpolation affects pricing correctly"""
        curves, yield_curve_service = sample_yield_curves
        
        # Create asset with maturity between curve points
        test_asset = Asset(
            blkrock_id='INTERP_TEST_001',
            issue_name='Interpolation Test Bond',
            issuer_name='Test Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            maturity=date(2026, 7, 15),  # 18 months from Jan 2025
            coupon=Decimal('0.055'),
            sp_issuer_rating='A'
        )
        integrated_db.add(test_asset)
        integrated_db.commit()
        
        # Price the asset
        pricing_date = date(2025, 1, 10)
        result = test_asset.update_fair_value(
            yield_curve_service, 'USD_TREASURY', pricing_date=pricing_date
        )
        
        # Should work correctly with interpolated rates
        assert result is not None
        assert test_asset.fair_value > Decimal('0')
        
        # Verify the calculation uses proper interpolation
        treasury_curve = curves['USD_TREASURY']
        
        # 18-month zero rate should be interpolated between 12 and 24 month rates
        rate_18m = treasury_curve.zero_rate(pricing_date, date(2026, 7, 10))
        rate_12m = treasury_curve.spot_rate(pricing_date, 12)
        rate_24m = treasury_curve.spot_rate(pricing_date, 24)
        
        # 18-month rate should be between 12 and 24 month rates
        assert min(rate_12m, rate_24m) <= rate_18m <= max(rate_12m, rate_24m)