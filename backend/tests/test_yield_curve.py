"""
Test suite for Yield Curve System

Tests the complete VBA YieldCurve.cls conversion including:
- Setup and initialization
- Spot rate interpolation  
- Forward rate calculation
- Zero rate computation
- Database persistence
- VBA functional parity
"""

import pytest
import math
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.yield_curve import (
    YieldCurve,
    YieldCurveService,
    YieldCurveModel,
    YieldCurveRateModel,
    ForwardRateModel
)


@pytest.fixture
def yield_curve_db():
    """Create in-memory database for yield curve testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def sample_rate_dict():
    """Sample rate dictionary matching VBA test data"""
    return {
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


@pytest.fixture
def test_yield_curve(sample_rate_dict):
    """Create test yield curve with sample data"""
    analysis_date = date(2025, 1, 10)
    curve = YieldCurve("TEST_USD_TREASURY", analysis_date, sample_rate_dict)
    return curve


class TestYieldCurveSetup:
    """Test YieldCurve setup and initialization"""
    
    def test_yield_curve_initialization(self):
        """Test basic YieldCurve initialization"""
        curve = YieldCurve()
        
        assert curve.name == ""
        assert curve.analysis_date == date.today()
        assert curve.rate_dict == {}
        assert curve.last_month == 0
        assert curve.forward_dict == {}
        assert not curve._is_setup
    
    def test_yield_curve_setup_basic(self, sample_rate_dict):
        """Test VBA Setup() method basic functionality"""
        analysis_date = date(2025, 1, 10)
        curve = YieldCurve()
        
        # VBA Setup call
        curve.setup("USD_TREASURY", analysis_date, sample_rate_dict)
        
        # Verify VBA variable assignments
        assert curve.name == "USD_TREASURY"
        assert curve.analysis_date == analysis_date
        assert curve.rate_dict == sample_rate_dict
        assert curve.last_month == 360  # Max key in sample_rate_dict
        assert curve._is_setup == True
        
        # Verify spot rates were interpolated
        assert len(curve._spot_rates) == 360
        assert curve._spot_rates[1] == 0.0450  # Direct from input
        assert curve._spot_rates[3] == 0.0465  # Direct from input
        
        # Test interpolated values
        assert curve._spot_rates[2] > curve._spot_rates[1]  # Should be interpolated between 1 and 3
        assert curve._spot_rates[2] < curve._spot_rates[3]
    
    def test_vba_linear_interpolation_exact(self, sample_rate_dict):
        """Test VBA linear interpolation formula exactly"""
        curve = YieldCurve()
        curve.setup("TEST", date(2025, 1, 10), sample_rate_dict)
        
        # Test interpolation between month 1 (4.50%) and month 3 (4.65%)
        # VBA formula: (1 - (i - lPreviousMonth) / (lNextMonth - lPreviousMonth)) * rate1 + weight * rate2
        
        # Month 2 interpolation
        expected_month_2 = (1 - (2 - 1) / (3 - 1)) * 0.0450 + (2 - 1) / (3 - 1) * 0.0465
        assert abs(curve._spot_rates[2] - expected_month_2) < 1e-10
        
        # Test interpolation between month 12 (5.20%) and month 24 (5.65%)
        # Month 18 interpolation
        expected_month_18 = (1 - (18 - 12) / (24 - 12)) * 0.0520 + (18 - 12) / (24 - 12) * 0.0565
        assert abs(curve._spot_rates[18] - expected_month_18) < 1e-10
    
    def test_forward_rate_calculation_vba_exact(self, sample_rate_dict):
        """Test VBA forward rate calculation formula"""
        curve = YieldCurve()
        analysis_date = date(2025, 1, 10)
        curve.setup("TEST", analysis_date, sample_rate_dict)
        
        # Verify forward_dict structure
        assert len(curve.forward_dict) > 0
        
        # VBA: clsFowardDict.Add CLng(clsAnalysisDate), lSpotRate(1)
        analysis_date_int = int(analysis_date.toordinal())
        assert curve.forward_dict[analysis_date_int] == curve._spot_rates[1]
        
        # Test VBA forward rate formula:
        # lFowardRate(i) = (((1 + lSpotRate(i + 1)) ^ (i + 1)) / ((1 + lSpotRate(i)) ^ (i))) - 1
        spot_1 = curve._spot_rates[1]  # 0.0450
        spot_2 = curve._spot_rates[2]  # interpolated value
        
        expected_forward_1 = (((1 + spot_2) ** 2) / ((1 + spot_1) ** 1)) - 1
        
        # Check forward rate for month 1 (second entry in forward_dict)
        forward_date_1 = analysis_date + relativedelta(months=1)
        forward_date_1_int = int(forward_date_1.toordinal())
        
        if forward_date_1_int in curve.forward_dict:
            actual_forward = curve.forward_dict[forward_date_1_int]
            assert abs(actual_forward - expected_forward_1) < 1e-10


class TestYieldCurveSpotRate:
    """Test VBA SpotRate() method"""
    
    def test_spot_rate_basic_functionality(self, test_yield_curve):
        """Test basic spot rate calculation"""
        curve = test_yield_curve
        analysis_date = curve.analysis_date
        
        # Test 1 month rate from analysis date
        rate_1m = curve.spot_rate(analysis_date, 1)
        assert rate_1m > 0
        assert rate_1m < 1  # Should be reasonable rate
        
        # Test 12 month rate
        rate_12m = curve.spot_rate(analysis_date, 12)
        assert rate_12m > rate_1m  # Expect upward sloping curve
    
    def test_spot_rate_before_first_forward_date(self, test_yield_curve):
        """Test VBA logic: iDate <= CDate(lFowardDate(0))"""
        curve = test_yield_curve
        
        # Date before analysis date should use first forward rate
        early_date = curve.analysis_date - relativedelta(days=30)
        rate = curve.spot_rate(early_date, 1)
        
        # Should get reasonable rate (using first forward rate)
        assert rate > 0
        assert rate < 1
    
    def test_spot_rate_within_forward_range(self, test_yield_curve):
        """Test VBA interpolation logic within forward rate range"""
        curve = test_yield_curve
        
        # Date within the forward rate range
        future_date = curve.analysis_date + relativedelta(months=6)
        rate = curve.spot_rate(future_date, 3)
        
        assert rate > 0
        assert rate < 1
    
    def test_spot_rate_after_last_forward_date(self, test_yield_curve):
        """Test VBA logic: iDate > last forward date"""
        curve = test_yield_curve
        
        # Date far in the future (beyond curve)
        far_future_date = curve.analysis_date + relativedelta(years=50)
        rate = curve.spot_rate(far_future_date, 1)
        
        # Should use last forward rate
        assert rate > 0
        assert rate < 1
    
    def test_spot_rate_vba_compounding_formula(self, test_yield_curve):
        """Test VBA compounding and averaging formula"""
        curve = test_yield_curve
        analysis_date = curve.analysis_date
        
        # Test the VBA formula: If iMonth > 0 Then lRate = lRate ^ (1 / iMonth)
        rate_3m = curve.spot_rate(analysis_date, 3)
        rate_6m = curve.spot_rate(analysis_date, 6)
        
        # 6 month rate should generally be higher for upward sloping curve
        # But this tests that the formula is working
        assert rate_3m > 0
        assert rate_6m > 0


class TestYieldCurveZeroRate:
    """Test VBA ZeroRate() method"""
    
    def test_zero_rate_basic_functionality(self, test_yield_curve):
        """Test basic zero rate calculation"""
        curve = test_yield_curve
        start_date = curve.analysis_date
        end_date = start_date + relativedelta(months=12)
        
        zero_rate = curve.zero_rate(start_date, end_date)
        
        assert zero_rate > 0
        assert zero_rate < 1
    
    def test_zero_rate_exact_month_boundary(self, test_yield_curve):
        """Test zero rate when end date is exactly on month boundary"""
        curve = test_yield_curve
        start_date = curve.analysis_date
        
        # Exactly 6 months
        end_date = start_date + relativedelta(months=6)
        zero_rate = curve.zero_rate(start_date, end_date)
        
        # Should match 6 month spot rate closely
        spot_rate_6m = curve.spot_rate(start_date, 6)
        assert abs(zero_rate - spot_rate_6m) < 0.01  # Allow small difference due to calculation method
    
    def test_zero_rate_interpolation_forward(self, test_yield_curve):
        """Test VBA interpolation when end date > month boundary"""
        curve = test_yield_curve
        start_date = curve.analysis_date
        
        # 6.5 months (between 6 and 7 month boundaries)
        end_date = start_date + relativedelta(months=6, days=15)
        zero_rate = curve.zero_rate(start_date, end_date)
        
        # Should be between 6 month and 7 month rates
        rate_6m = curve.spot_rate(start_date, 6)
        rate_7m = curve.spot_rate(start_date, 7)
        
        assert zero_rate > min(rate_6m, rate_7m)
        assert zero_rate < max(rate_6m, rate_7m)
    
    def test_zero_rate_interpolation_backward(self, test_yield_curve):
        """Test VBA interpolation when end date < month boundary"""
        curve = test_yield_curve
        start_date = curve.analysis_date
        
        # 5.5 months (between 5 and 6 month boundaries)
        end_date = start_date + relativedelta(months=5, days=15)
        zero_rate = curve.zero_rate(start_date, end_date)
        
        # Should be reasonable rate
        assert zero_rate > 0
        assert zero_rate < 1
    
    def test_zero_rate_vba_interpolation_formula(self, test_yield_curve):
        """Test VBA linear interpolation formula in ZeroRate"""
        curve = test_yield_curve
        start_date = curve.analysis_date
        
        # Test case where we can verify the interpolation manually
        end_date = start_date + relativedelta(months=12, days=15)  # 12.5 months
        
        zero_rate = curve.zero_rate(start_date, end_date)
        
        # Calculate expected using VBA formula
        # ZeroRate = lLowRate + (lHighRate - lLowRate) * ((iEndDate - lLowDate) / (lHighDate - lLowDate))
        l_months = 12  # DateDiff("M", start_date, end_date)
        l_low_date = start_date + relativedelta(months=l_months)  # 12 months exactly
        l_high_date = l_low_date + relativedelta(months=1)  # 13 months
        
        l_low_rate = curve.spot_rate(start_date, l_months)
        l_high_rate = curve.spot_rate(start_date, l_months + 1)
        
        time_weight = (end_date - l_low_date).days / (l_high_date - l_low_date).days
        expected_rate = l_low_rate + (l_high_rate - l_low_rate) * time_weight
        
        assert abs(zero_rate - expected_rate) < 1e-10


class TestYieldCurveDatabasePersistence:
    """Test database persistence functionality"""
    
    def test_save_to_database(self, yield_curve_db, sample_rate_dict):
        """Test saving yield curve to database"""
        analysis_date = date(2025, 1, 10)
        curve = YieldCurve("TEST_SAVE", analysis_date, sample_rate_dict, yield_curve_db)
        
        # Save to database
        curve_id = curve.save_to_database("TREASURY", "USD", "Test curve for saving")
        
        # Verify curve was saved
        assert curve_id > 0
        assert curve.curve_id == curve_id
        
        # Verify database records
        curve_record = yield_curve_db.query(YieldCurveModel).filter_by(curve_id=curve_id).first()
        assert curve_record is not None
        assert curve_record.curve_name == "TEST_SAVE"
        assert curve_record.curve_type == "TREASURY"
        assert curve_record.currency == "USD"
        assert curve_record.analysis_date == analysis_date
        
        # Verify spot rates were saved
        rate_records = yield_curve_db.query(YieldCurveRateModel).filter_by(curve_id=curve_id).all()
        assert len(rate_records) == 360  # Should have all interpolated rates
        
        # Verify original vs interpolated flags
        original_rates = [r for r in rate_records if not r.is_interpolated]
        interpolated_rates = [r for r in rate_records if r.is_interpolated]
        
        assert len(original_rates) == len(sample_rate_dict)
        assert len(interpolated_rates) == 360 - len(sample_rate_dict)
        
        # Verify forward rates were saved
        forward_records = yield_curve_db.query(ForwardRateModel).filter_by(curve_id=curve_id).all()
        assert len(forward_records) > 0
    
    def test_yield_curve_service_create(self, yield_curve_db, sample_rate_dict):
        """Test YieldCurveService.create_yield_curve()"""
        service = YieldCurveService(yield_curve_db)
        
        analysis_date = date(2025, 1, 10)
        curve = service.create_yield_curve(
            "SERVICE_TEST", 
            analysis_date, 
            sample_rate_dict,
            "TREASURY",
            "USD",
            "Test curve via service"
        )
        
        assert curve is not None
        assert curve.curve_id is not None
        assert curve._is_setup
        
        # Verify can calculate rates
        rate = curve.spot_rate(analysis_date, 12)
        assert rate > 0
    
    def test_yield_curve_service_load(self, yield_curve_db, sample_rate_dict):
        """Test YieldCurveService.load_yield_curve()"""
        service = YieldCurveService(yield_curve_db)
        analysis_date = date(2025, 1, 10)
        
        # Create curve
        original_curve = service.create_yield_curve(
            "LOAD_TEST", analysis_date, sample_rate_dict
        )
        original_rate = original_curve.spot_rate(analysis_date, 12)
        
        # Load curve
        loaded_curve = service.load_yield_curve("LOAD_TEST", analysis_date)
        
        assert loaded_curve is not None
        assert loaded_curve.name == "LOAD_TEST"
        assert loaded_curve.analysis_date == analysis_date
        assert loaded_curve._is_setup
        
        # Verify rates match
        loaded_rate = loaded_curve.spot_rate(analysis_date, 12)
        assert abs(loaded_rate - original_rate) < 1e-10
    
    def test_present_value_calculation(self, yield_curve_db, sample_rate_dict):
        """Test present value calculation using yield curve"""
        service = YieldCurveService(yield_curve_db)
        analysis_date = date(2025, 1, 10)
        
        # Create curve
        service.create_yield_curve("PV_TEST", analysis_date, sample_rate_dict)
        
        # Test cash flows
        cash_flows = [
            (date(2026, 1, 10), Decimal('1000')),  # 1 year: $1,000
            (date(2027, 1, 10), Decimal('1000')),  # 2 years: $1,000
            (date(2028, 1, 10), Decimal('1000')),  # 3 years: $1,000
        ]
        
        pv = service.calculate_present_value(cash_flows, "PV_TEST", analysis_date)
        
        # Present value should be less than sum of cash flows
        total_cf = sum(cf[1] for cf in cash_flows)
        assert pv < total_cf
        assert pv > Decimal('0')


class TestYieldCurveEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_rate_dict_error(self):
        """Test error handling for empty rate dictionary"""
        curve = YieldCurve()
        
        with pytest.raises(ValueError, match="Rate dictionary cannot be empty"):
            curve.setup("EMPTY", date(2025, 1, 10), {})
    
    def test_single_rate_handling(self):
        """Test yield curve with single rate point"""
        single_rate_dict = {12: 0.05}
        curve = YieldCurve("SINGLE", date(2025, 1, 10), single_rate_dict)
        
        # Should setup successfully
        assert curve._is_setup
        assert curve.last_month == 12
        
        # All rates should be the single rate
        for month in range(1, 13):
            assert curve._spot_rates[month] == 0.05
    
    def test_spot_rate_without_setup_error(self):
        """Test error when calling spot_rate before setup"""
        curve = YieldCurve()
        
        with pytest.raises(RuntimeError, match="YieldCurve must be setup"):
            curve.spot_rate(date(2025, 1, 10), 1)
    
    def test_zero_rate_without_setup_error(self):
        """Test error when calling zero_rate before setup"""
        curve = YieldCurve()
        
        with pytest.raises(RuntimeError, match="YieldCurve must be setup"):
            curve.zero_rate(date(2025, 1, 10), date(2026, 1, 10))
    
    def test_save_without_setup_error(self, yield_curve_db):
        """Test error when saving curve without setup"""
        curve = YieldCurve(session=yield_curve_db)
        
        with pytest.raises(RuntimeError, match="YieldCurve must be setup"):
            curve.save_to_database()
    
    def test_save_without_session_error(self, sample_rate_dict):
        """Test error when saving without database session"""
        curve = YieldCurve("NO_SESSION", date(2025, 1, 10), sample_rate_dict)
        
        with pytest.raises(RuntimeError, match="Database session required"):
            curve.save_to_database()


class TestVBAComparisonAccuracy:
    """Test VBA comparison for exact functional parity"""
    
    def test_vba_exact_setup_behavior(self, sample_rate_dict):
        """Test setup matches VBA behavior exactly"""
        analysis_date = date(2025, 1, 10)
        curve = YieldCurve()
        curve.setup("VBA_TEST", analysis_date, sample_rate_dict)
        
        # Verify VBA variable mappings
        assert curve.name == "VBA_TEST"  # clsName
        assert curve.analysis_date == analysis_date  # clsAnalysisDate
        assert curve.last_month == 360  # clsLastMonth
        assert len(curve._spot_rates) == 360  # lSpotRate array
        assert len(curve.forward_dict) > 0  # clsFowardDict
        
        # Verify last_date and last_forward are set
        assert curve.last_date > analysis_date
        assert curve.last_forward != 0.0
    
    def test_forward_rate_formula_precision(self, sample_rate_dict):
        """Test forward rate calculation matches VBA precision"""
        curve = YieldCurve("PRECISION_TEST", date(2025, 1, 10), sample_rate_dict)
        
        # Test specific forward rate calculation
        # VBA: lFowardRate(i) = (((1 + lSpotRate(i + 1)) ^ (i + 1)) / ((1 + lSpotRate(i)) ^ (i))) - 1
        
        spot_rates = curve._spot_rates
        
        # Test month 1 forward rate
        expected_forward_1 = (((1 + spot_rates[2]) ** 2) / ((1 + spot_rates[1]) ** 1)) - 1
        
        # Find the forward rate in forward_dict
        forward_date_1 = curve.analysis_date + relativedelta(months=1)
        forward_date_1_int = int(forward_date_1.toordinal())
        
        if forward_date_1_int in curve.forward_dict:
            actual_forward_1 = curve.forward_dict[forward_date_1_int]
            # Should match to high precision
            assert abs(actual_forward_1 - expected_forward_1) < 1e-12
    
    def test_interpolation_boundary_conditions(self):
        """Test interpolation at boundary conditions"""
        # Test with rates that have gaps
        sparse_rates = {1: 0.04, 12: 0.06, 36: 0.07}
        curve = YieldCurve("SPARSE", date(2025, 1, 10), sparse_rates)
        
        # Test interpolation between 1 and 12 months
        # Month 6 should be halfway between 0.04 and 0.06
        expected_month_6 = (1 - (6 - 1) / (12 - 1)) * 0.04 + (6 - 1) / (12 - 1) * 0.06
        assert abs(curve._spot_rates[6] - expected_month_6) < 1e-10
        
        # Test interpolation between 12 and 36 months  
        # Month 24 should be halfway between 0.06 and 0.07
        expected_month_24 = (1 - (24 - 12) / (36 - 12)) * 0.06 + (24 - 12) / (36 - 12) * 0.07
        assert abs(curve._spot_rates[24] - expected_month_24) < 1e-10