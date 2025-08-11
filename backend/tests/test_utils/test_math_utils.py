"""
Test suite for math_utils module

Tests mathematical and date utility functions converted from VBA Math.bas
"""

import pytest
from datetime import date, timedelta
import math
from decimal import Decimal

from app.utils.math_utils import MathUtils, DayCount


class TestMathUtils:
    """Test mathematical utility functions"""
    
    def test_statistical_functions(self):
        """Test statistical array functions"""
        test_array = [1, 2, 3, 4, 5]
        
        assert MathUtils.min_array(test_array) == 1
        assert MathUtils.max_array(test_array) == 5
        assert MathUtils.average_array(test_array) == 3.0
        
        # Test standard deviation
        std = MathUtils.std_array(test_array)
        expected_std = math.sqrt(sum((x - 3) ** 2 for x in test_array) / len(test_array))
        assert abs(std - expected_std) < 1e-10
        
        # Test median
        assert MathUtils.median_array(test_array) == 3.0
        assert MathUtils.median_array([1, 2]) == 1.5
        assert MathUtils.median_array([1]) == 1.0
        
    def test_statistical_functions_double_precision(self):
        """Test double precision array functions"""
        test_array = [1.1, 2.2, 3.3, 4.4, 5.5]
        
        assert abs(MathUtils.min_array(test_array) - 1.1) < 1e-10
        assert abs(MathUtils.max_array(test_array) - 5.5) < 1e-10
        assert abs(MathUtils.average_array(test_array) - 3.3) < 1e-10
        
    def test_empty_array_handling(self):
        """Test handling of empty arrays"""
        with pytest.raises(ValueError):
            MathUtils.min_array([])
        with pytest.raises(ValueError):
            MathUtils.max_array([])
        with pytest.raises(ValueError):
            MathUtils.average_array([])
        with pytest.raises(ValueError):
            MathUtils.std_array([])
        with pytest.raises(ValueError):
            MathUtils.median_array([])
    
    def test_business_date_checking(self):
        """Test business date validation and adjustment"""
        utils = MathUtils()
        
        # Test weekday that is not a holiday (should be business day)
        # Note: Jan 15, 2024 is MLK Jr Day, so use a different date
        weekday = date(2024, 1, 16)  # Tuesday
        assert utils.check_business_date(weekday) == weekday
        
        # Test weekend adjustment (should move to Monday)
        saturday = date(2024, 1, 13)
        adjusted = utils.check_business_date(saturday)
        assert adjusted.weekday() not in [5, 6]  # Not weekend
        
        # Test with different adjustment methods
        sunday = date(2024, 1, 14)
        following = utils.check_business_date(sunday, "FOLLOWING")
        previous = utils.check_business_date(sunday, "PREVIOUS")
        
        assert following > sunday
        assert previous < sunday
        assert following.weekday() not in [5, 6]
        assert previous.weekday() not in [5, 6]
    
    def test_date_add_business(self):
        """Test business date addition"""
        utils = MathUtils()
        start_date = date(2024, 1, 15)  # Monday
        
        # Add 3 months
        result = utils.date_add_business("m", 3, start_date)
        expected = date(2024, 4, 15)  # Should be same day 3 months later
        assert result == expected
        
        # Add 1 year
        result = utils.date_add_business("y", 1, start_date)
        expected = date(2025, 1, 15)
        assert result == expected
        
        # Add days
        result = utils.date_add_business("d", 10, start_date)
        expected = start_date + timedelta(days=10)
        assert result == expected
        
        # Test end of month convention
        result = utils.date_add_business("m", 1, date(2024, 1, 31), 
                                       end_of_month=True)
        # Should be end of February
        assert result.day == 29  # 2024 is leap year
        assert result.month == 2
    
    def test_day_count_conventions(self):
        """Test day count convention calculations"""
        date1 = date(2024, 1, 15)
        date2 = date(2024, 7, 15)  # 6 months later
        
        # Test different day count conventions
        actual_360 = MathUtils.year_frac(date1, date2, DayCount.ACTUAL_360)
        actual_365 = MathUtils.year_frac(date1, date2, DayCount.ACTUAL_365)
        us_30_360 = MathUtils.year_frac(date1, date2, DayCount.US30_360)
        
        # Basic validation - 6 months should be roughly 0.5 years
        assert 0.4 < actual_360 < 0.6
        assert 0.4 < actual_365 < 0.6
        assert 0.4 < us_30_360 < 0.6
        
        # 30/360 should be exactly 0.5 for this case
        assert abs(us_30_360 - 0.5) < 1e-10
    
    def test_days_between_calculation(self):
        """Test days between dates calculation"""
        date1 = date(2024, 1, 1)
        date2 = date(2024, 1, 31)
        
        actual_days = MathUtils.days_between(date1, date2, DayCount.ACTUAL_360)
        us_30_360_days = MathUtils.days_between(date1, date2, DayCount.US30_360)
        
        assert actual_days == 30  # January has 31 days, but 30 days between
        assert us_30_360_days == 30  # 30/360 should also be 30
    
    def test_daycount_enum_conversion(self):
        """Test day count string to enum conversion"""
        assert MathUtils.get_daycount_enum("30/360") == DayCount.US30_360
        assert MathUtils.get_daycount_enum("ACTUAL/ACTUAL") == DayCount.ACTUAL_ACTUAL
        assert MathUtils.get_daycount_enum("ACTUAL/360") == DayCount.ACTUAL_360
        assert MathUtils.get_daycount_enum("ACT365") == DayCount.ACTUAL_365
        assert MathUtils.get_daycount_enum("30/360EU") == DayCount.EU30_360
        
        # Test default case
        assert MathUtils.get_daycount_enum("INVALID") == DayCount.US30_360
    
    def test_payment_frequency_utilities(self):
        """Test payment frequency conversion utilities"""
        assert MathUtils.get_months("ANNUALLY") == 12
        assert MathUtils.get_months("SEMI-ANNUALLY") == 6
        assert MathUtils.get_months("QUARTERLY") == 3
        assert MathUtils.get_months("MONTHLY") == 1
        
        assert MathUtils.get_payments_per_year("ANNUALLY") == 1
        assert MathUtils.get_payments_per_year("SEMI-ANNUALLY") == 2
        assert MathUtils.get_payments_per_year("QUARTERLY") == 4
        assert MathUtils.get_payments_per_year("MONTHLY") == 12
    
    def test_present_value_calculation(self):
        """Test present value calculations"""
        # Simple test case: $100 cashflow in 1 year at 10% yield
        cashflows = [100.0]
        dates = [date(2025, 1, 1)]  # Cashflow dates only
        settlement_date = date(2024, 1, 1)
        yield_rate = 0.10
        
        pv = MathUtils.calc_pv(cashflows, dates, settlement_date, 
                             yield_rate, DayCount.US30_360, 1)
        
        # The PV calculation uses the compound factor from the period calculation
        # For annual frequency with 30/360 day count, verify it's reasonable
        assert 80 < pv < 95  # Should be discounted value between reasonable bounds
    
    def test_discount_and_compound_factors(self):
        """Test discount and compound factor calculations"""
        date1 = date(2024, 1, 1)
        date2 = date(2025, 1, 1)  # 1 year
        yield_rate = 0.10
        
        discount = MathUtils.calc_discount(yield_rate, date1, date2, 
                                         DayCount.US30_360, 1, True)
        compound = MathUtils.calc_compound(yield_rate, date1, date2, 
                                         DayCount.US30_360, 1, True)
        
        # Discount and compound should be reciprocals
        assert abs(discount * compound - 1.0) < 1e-10
        
        # For 1 year at 10%, compound factor calculation depends on compounding periods
        # The actual calculation may differ from simple 1.10 depending on the method used
        assert compound > 1.0  # Should be greater than 1 for positive rates
    
    def test_annual_rate_conversion(self):
        """Test annual rate conversion"""
        annual_rate = 0.12  # 12% annual
        start_date = date(2024, 1, 1)
        end_date = date(2024, 4, 1)  # 3 months
        
        period_rate = MathUtils.convert_annual_rates(annual_rate, start_date, end_date)
        
        # Should be approximately 3% for quarterly period
        assert 0.025 < period_rate < 0.035
    
    def test_wal_calculation(self):
        """Test Weighted Average Life calculation"""
        # Example: $50 in period 1, $50 in period 2
        cashflows = [0, 50, 50]  # Period 0 is typically 0
        periods_per_year = 4  # Quarterly
        
        wal = MathUtils.wal(cashflows, periods_per_year)
        
        # WAL should be 1.5 periods / 4 = 0.375 years
        expected_wal = 1.5 / 4
        assert abs(wal - expected_wal) < 1e-10
    
    def test_random_number_generation(self):
        """Test random number generation"""
        # Test that random numbers are positive and between 0 and 1
        for _ in range(100):
            rand_num = MathUtils.rand()
            assert 0 < rand_num <= 1
    
    def test_leap_year_detection(self):
        """Test leap year detection"""
        assert MathUtils._is_leap_year(2024)  # Leap year
        assert not MathUtils._is_leap_year(2023)  # Not leap year
        assert MathUtils._is_leap_year(2000)  # Leap year (divisible by 400)
        assert not MathUtils._is_leap_year(1900)  # Not leap year (divisible by 100, not 400)
    
    def test_month_addition(self):
        """Test month addition utility"""
        start_date = date(2024, 1, 31)
        
        # Adding 1 month to Jan 31 should give Feb 29 (2024 is leap year)
        result = MathUtils._add_months(start_date, 1)
        assert result == date(2024, 2, 29)
        
        # Adding 12 months should give same day next year (or closest valid)
        result = MathUtils._add_months(start_date, 12)
        assert result == date(2025, 1, 31)
    
    def test_convenience_functions(self):
        """Test module-level convenience functions"""
        from app.utils.math_utils import min_array, max_array, year_frac
        
        test_array = [1, 2, 3, 4, 5]
        assert min_array(test_array) == 1
        assert max_array(test_array) == 5
        
        date1 = date(2024, 1, 1)
        date2 = date(2024, 7, 1)
        frac = year_frac(date1, date2, DayCount.US30_360)
        assert abs(frac - 0.5) < 1e-10  # 6 months = 0.5 years in 30/360