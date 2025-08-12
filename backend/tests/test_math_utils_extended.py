"""
Extended Tests for Math Utils Module

Additional comprehensive test suite for mathematical utility functions
converted from VBA Math.bas, focusing on financial calculations and edge cases.

Author: Claude
Date: 2025-01-12
"""

import pytest
import numpy as np
from datetime import date, timedelta
from decimal import Decimal

from app.utils.math_utils import MathUtils, DayCount


class TestFinancialCalculations:
    """Test financial calculation functions"""
    
    @pytest.fixture
    def math_utils(self):
        """Create MathUtils instance"""
        return MathUtils()
    
    def test_calc_pv_simple(self, math_utils):
        """Test present value calculation with simple cashflows"""
        cashflows = [100, 100, 100, 100]  # 4 payments of 100
        dates = [
            date(2024, 1, 1),
            date(2024, 4, 1),
            date(2024, 7, 1),
            date(2024, 10, 1),
            date(2025, 1, 1)
        ]
        settlement_date = date(2024, 1, 1)
        yield_rate = 0.05  # 5%
        
        pv = math_utils.calc_pv(cashflows, dates, settlement_date, 
                               yield_rate, DayCount.ACTUAL_365, 4)
        
        assert pv > 0
        assert pv < sum(cashflows)  # PV should be less than face value
    
    def test_calc_pv_zero_yield(self, math_utils):
        """Test PV calculation with zero yield"""
        cashflows = [100, 100, 100]
        dates = [date(2024, 1, 1), date(2024, 7, 1), date(2025, 1, 1)]
        settlement_date = date(2024, 1, 1)
        
        pv = math_utils.calc_pv(cashflows, dates, settlement_date,
                               0.0, DayCount.ACTUAL_365, 2)
        
        assert abs(pv - sum(cashflows)) < 0.01  # Should equal sum when yield is 0
    
    def test_calc_discount_factor(self, math_utils):
        """Test discount factor calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 7, 1)  # 6 months
        
        discount = math_utils.calc_discount(0.10, start_date, end_date,
                                          DayCount.ACTUAL_365, 2, True)
        
        assert 0 < discount < 1  # Discount factor should be between 0 and 1
        assert discount < 1.0  # Should be less than 1 for positive rates
    
    def test_calc_compound_factor(self, math_utils):
        """Test compound factor calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2025, 1, 1)  # 1 year
        
        compound = math_utils.calc_compound(0.05, start_date, end_date,
                                          DayCount.ACTUAL_365, 1, False)
        
        assert compound > 1.0  # Should be greater than 1 for positive rates
        assert abs(compound - 1.05) < 0.01  # Should be close to 1.05 for 5% annual
    
    def test_compounding_periods_settlement(self, math_utils):
        """Test compounding periods calculation from settlement"""
        start_date = date(2024, 1, 1)
        end_date = date(2026, 1, 1)  # 2 years
        
        periods = math_utils._compounding_periods_between_dates(
            start_date, end_date, 6, DayCount.ACTUAL_365, True
        )
        
        assert abs(periods - 4.0) < 0.1  # Should be approximately 4 semi-annual periods
    
    def test_compounding_periods_forward(self, math_utils):
        """Test compounding periods calculation forward"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 10, 1)  # 9 months
        
        periods = math_utils._compounding_periods_between_dates(
            start_date, end_date, 3, DayCount.ACTUAL_365, False
        )
        
        assert abs(periods - 3.0) < 0.1  # Should be approximately 3 quarterly periods


class TestDayCountConventions:
    """Test day count convention calculations"""
    
    @pytest.fixture
    def math_utils(self):
        return MathUtils()
    
    def test_year_frac_30_360(self, math_utils):
        """Test 30/360 year fraction calculation"""
        start_date = date(2024, 1, 31)
        end_date = date(2024, 2, 29)  # Leap year
        
        year_frac = math_utils.year_frac(start_date, end_date, DayCount.US30_360)
        
        # 30/360: Should treat Feb 29 as Feb 30, so 30 days / 360 = 1/12
        expected = 30 / 360
        assert abs(year_frac - expected) < 0.001
    
    def test_year_frac_actual_365(self, math_utils):
        """Test Actual/365 year fraction calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 7, 1)  # 6 months
        
        year_frac = math_utils.year_frac(start_date, end_date, DayCount.ACTUAL_365)
        
        actual_days = (end_date - start_date).days
        expected = actual_days / 365.0
        assert abs(year_frac - expected) < 0.001
    
    def test_year_frac_actual_360(self, math_utils):
        """Test Actual/360 year fraction calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 4, 1)  # 3 months
        
        year_frac = math_utils.year_frac(start_date, end_date, DayCount.ACTUAL_360)
        
        actual_days = (end_date - start_date).days
        expected = actual_days / 360.0
        assert abs(year_frac - expected) < 0.001
    
    def test_year_frac_actual_actual(self, math_utils):
        """Test Actual/Actual year fraction calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2025, 1, 1)  # Exactly 1 year
        
        year_frac = math_utils.year_frac(start_date, end_date, DayCount.ACTUAL_ACTUAL)
        
        assert abs(year_frac - 1.0) < 0.01  # Should be close to 1.0
    
    def test_days_between_30_360(self, math_utils):
        """Test days calculation using 30/360"""
        start_date = date(2024, 1, 31)
        end_date = date(2024, 3, 31)
        
        days = math_utils.days_between(start_date, end_date, DayCount.US30_360)
        
        # 30/360: Jan 31 -> Jan 30, Mar 31 -> Mar 30
        # So 30 (Feb) + 30 (Mar) = 60 days
        assert days == 60
    
    def test_days_between_actual(self, math_utils):
        """Test days calculation using actual"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        days = math_utils.days_between(start_date, end_date, DayCount.ACTUAL_365)
        
        assert days == 30  # Actual days in January (31 - 1)


class TestBusinessDateCalculations:
    """Test business date calculation functions"""
    
    @pytest.fixture
    def math_utils(self):
        return MathUtils()
    
    def test_is_business_day_weekend(self, math_utils):
        """Test weekend detection"""
        saturday = date(2024, 1, 6)  # Saturday
        sunday = date(2024, 1, 7)    # Sunday
        monday = date(2024, 1, 8)    # Monday
        
        assert not math_utils._is_business_day(saturday)
        assert not math_utils._is_business_day(sunday)
        assert math_utils._is_business_day(monday)
    
    def test_is_business_day_holiday(self, math_utils):
        """Test holiday detection"""
        new_years = date(2024, 1, 1)  # New Year's Day
        christmas = date(2024, 12, 25)  # Christmas
        
        assert not math_utils._is_business_day(new_years)
        assert not math_utils._is_business_day(christmas)
    
    def test_get_next_business_date_weekend(self, math_utils):
        """Test getting next business date from weekend"""
        friday = date(2024, 1, 5)     # Friday
        saturday = date(2024, 1, 6)   # Saturday
        expected_monday = date(2024, 1, 8)  # Monday
        
        next_from_friday = math_utils._get_next_business_date(friday, 0)
        next_from_saturday = math_utils._get_next_business_date(saturday, 0)
        
        assert next_from_friday == friday  # Friday is already business day
        assert next_from_saturday == expected_monday
    
    def test_get_previous_business_date_weekend(self, math_utils):
        """Test getting previous business date from weekend"""
        monday = date(2024, 1, 8)     # Monday
        sunday = date(2024, 1, 7)     # Sunday
        expected_friday = date(2024, 1, 5)  # Friday
        
        prev_from_monday = math_utils._get_previous_business_date(monday, 0)
        prev_from_sunday = math_utils._get_previous_business_date(sunday, 0)
        
        assert prev_from_monday == monday  # Monday is already business day
        assert prev_from_sunday == expected_friday
    
    def test_check_business_date_mod_following(self, math_utils):
        """Test modified following business date adjustment"""
        # Test date that would roll to next month
        jan_31 = date(2024, 1, 31)  # Wednesday, but test the logic
        
        adjusted = math_utils.check_business_date(jan_31, "MOD FOLLOWING")
        
        # Should return a business date (exact behavior depends on holidays)
        assert math_utils._is_business_day(adjusted)
    
    def test_date_add_business_months(self, math_utils):
        """Test adding months with business day adjustment"""
        start_date = date(2024, 1, 15)
        
        result = math_utils.date_add_business("M", 3, start_date, "FOLLOWING")
        
        expected = date(2024, 4, 15)
        # Result should be close to expected, adjusted for business days
        assert abs((result - expected).days) <= 3
        assert math_utils._is_business_day(result)
    
    def test_date_add_business_end_of_month(self, math_utils):
        """Test adding with end of month flag"""
        start_date = date(2024, 1, 15)
        
        result = math_utils.date_add_business("M", 1, start_date, end_of_month=True)
        
        # Should be end of February 2024 (leap year)
        assert result.month == 2
        assert result.day == 29  # Feb 29 in leap year
    
    def test_add_months_leap_year(self, math_utils):
        """Test month addition with leap year handling"""
        jan_31 = date(2024, 1, 31)  # January 31 in leap year
        
        result = math_utils._add_months(jan_31, 1)
        
        # Should be February 29 (leap year)
        assert result == date(2024, 2, 29)
    
    def test_add_months_non_leap_year(self, math_utils):
        """Test month addition with non-leap year"""
        jan_31 = date(2023, 1, 31)  # January 31 in non-leap year
        
        result = math_utils._add_months(jan_31, 1)
        
        # Should be February 28 (non-leap year)
        assert result == date(2023, 2, 28)


class TestStatisticalFunctions:
    """Test statistical utility functions"""
    
    def test_statistical_functions_empty_array(self):
        """Test statistical functions with empty arrays"""
        with pytest.raises(ValueError):
            MathUtils.min_array([])
        
        with pytest.raises(ValueError):
            MathUtils.max_array([])
        
        with pytest.raises(ValueError):
            MathUtils.average_array([])
    
    def test_statistical_functions_single_element(self):
        """Test statistical functions with single element"""
        single_element = [42.5]
        
        assert MathUtils.min_array(single_element) == 42.5
        assert MathUtils.max_array(single_element) == 42.5
        assert MathUtils.average_array(single_element) == 42.5
        assert MathUtils.std_array(single_element) == 0.0
        assert MathUtils.median_array(single_element) == 42.5
    
    def test_statistical_functions_multiple_elements(self):
        """Test statistical functions with multiple elements"""
        values = [1, 2, 3, 4, 5]
        
        assert MathUtils.min_array(values) == 1
        assert MathUtils.max_array(values) == 5
        assert MathUtils.average_array(values) == 3.0
        assert MathUtils.median_array(values) == 3.0
        
        # Standard deviation should be > 0
        std_dev = MathUtils.std_array(values)
        assert std_dev > 0
        assert abs(std_dev - np.std(values)) < 0.01
    
    def test_median_even_number_elements(self):
        """Test median with even number of elements"""
        values = [1, 2, 3, 4]
        
        median = MathUtils.median_array(values)
        assert median == 2.5  # (2 + 3) / 2
    
    def test_median_odd_number_elements(self):
        """Test median with odd number of elements"""
        values = [1, 2, 3, 4, 5]
        
        median = MathUtils.median_array(values)
        assert median == 3.0


class TestUtilityFunctions:
    """Test utility and conversion functions"""
    
    def test_get_daycount_enum(self):
        """Test day count string to enum conversion"""
        assert MathUtils.get_daycount_enum("30/360") == DayCount.US30_360
        assert MathUtils.get_daycount_enum("ACTUAL/ACTUAL") == DayCount.ACTUAL_ACTUAL
        assert MathUtils.get_daycount_enum("ACT365") == DayCount.ACTUAL_365
        assert MathUtils.get_daycount_enum("ACT360") == DayCount.ACTUAL_360
        assert MathUtils.get_daycount_enum("30/360EU") == DayCount.EU30_360
        
        # Test default case
        assert MathUtils.get_daycount_enum("UNKNOWN") == DayCount.US30_360
    
    def test_get_months(self):
        """Test frequency to months conversion"""
        assert MathUtils.get_months("ANNUALLY") == 12
        assert MathUtils.get_months("SEMI-ANNUALLY") == 6
        assert MathUtils.get_months("QUARTERLY") == 3
        assert MathUtils.get_months("MONTHLY") == 1
        
        # Test default case
        assert MathUtils.get_months("UNKNOWN") == 12
    
    def test_get_payments_per_year(self):
        """Test frequency to payments per year conversion"""
        assert MathUtils.get_payments_per_year("ANNUALLY") == 1
        assert MathUtils.get_payments_per_year("SEMI-ANNUALLY") == 2
        assert MathUtils.get_payments_per_year("QUARTERLY") == 4
        assert MathUtils.get_payments_per_year("MONTHLY") == 12
        
        # Test default case
        assert MathUtils.get_payments_per_year("UNKNOWN") == 1
    
    def test_convert_annual_rates(self):
        """Test annual rate conversion"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 4, 1)  # 3 months
        annual_rate = 0.12  # 12% annual
        
        period_rate = MathUtils.convert_annual_rates(annual_rate, start_date, end_date)
        
        assert 0 < period_rate < annual_rate  # Period rate should be less than annual
        assert period_rate > 0
    
    def test_convert_annual_rates_same_date(self):
        """Test annual rate conversion with same dates"""
        same_date = date(2024, 1, 1)
        
        period_rate = MathUtils.convert_annual_rates(0.12, same_date, same_date)
        
        assert period_rate == 0.0
    
    def test_wal_calculation(self):
        """Test Weighted Average Life calculation"""
        cashflows = [0, 100, 200, 300, 400]  # Period 0 has 0, then increasing
        periods_per_year = 4  # Quarterly
        
        wal = MathUtils.wal(cashflows, periods_per_year)
        
        assert wal > 0
        # Manual calculation: (100*1 + 200*2 + 300*3 + 400*4) / (100+200+300+400) / 4
        expected = (100*1 + 200*2 + 300*3 + 400*4) / (100+200+300+400) / 4
        assert abs(wal - expected) < 0.01
    
    def test_wal_zero_cashflows(self):
        """Test WAL with zero cashflows"""
        cashflows = [0, 0, 0, 0]
        
        wal = MathUtils.wal(cashflows, 4)
        
        assert wal == 0.0
    
    def test_rand_function(self):
        """Test random number generation"""
        # Generate multiple random numbers
        randoms = [MathUtils.rand() for _ in range(100)]
        
        # All should be between 0 and 1
        assert all(0 < r < 1 for r in randoms)
        
        # Should have some variance (not all the same)
        assert len(set(randoms)) > 1


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling"""
    
    def test_leap_year_detection(self):
        """Test leap year detection"""
        assert MathUtils._is_leap_year(2024)  # Divisible by 4
        assert not MathUtils._is_leap_year(2023)  # Not divisible by 4
        assert not MathUtils._is_leap_year(1900)  # Divisible by 100, not 400
        assert MathUtils._is_leap_year(2000)  # Divisible by 400
    
    def test_days_in_month(self, math_utils=MathUtils()):
        """Test days in month calculation"""
        assert math_utils._days_in_month(2024, 1) == 31  # January
        assert math_utils._days_in_month(2024, 2) == 29  # February leap year
        assert math_utils._days_in_month(2023, 2) == 28  # February non-leap year
        assert math_utils._days_in_month(2024, 4) == 30  # April
        assert math_utils._days_in_month(2024, 12) == 31  # December
    
    def test_negative_cashflows(self):
        """Test handling of negative cashflows"""
        cashflows = [-100, 50, 50, 50]
        dates = [date(2024, 1, 1), date(2024, 4, 1), date(2024, 7, 1), date(2024, 10, 1)]
        math_utils = MathUtils()
        
        # Should not raise error
        pv = math_utils.calc_pv(cashflows, dates, dates[0], 0.05, DayCount.ACTUAL_365, 4)
        assert isinstance(pv, (int, float))
    
    def test_very_high_yield_rates(self):
        """Test with very high yield rates"""
        cashflows = [100, 100, 100]
        dates = [date(2024, 1, 1), date(2024, 7, 1), date(2025, 1, 1)]
        math_utils = MathUtils()
        
        # Very high yield rate
        pv = math_utils.calc_pv(cashflows, dates, dates[0], 2.0, DayCount.ACTUAL_365, 2)
        
        assert pv > 0  # Should still be positive
        assert pv < sum(cashflows)  # But much smaller than face value
    
    def test_future_settlement_date(self):
        """Test with settlement date in the future"""
        cashflows = [100, 100, 100]
        dates = [date(2025, 1, 1), date(2025, 7, 1), date(2026, 1, 1)]
        settlement_date = date(2024, 1, 1)  # Before first cashflow date
        math_utils = MathUtils()
        
        # Should handle future settlement
        pv = math_utils.calc_pv(cashflows, dates, settlement_date, 0.05, DayCount.ACTUAL_365, 2)
        assert pv > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])