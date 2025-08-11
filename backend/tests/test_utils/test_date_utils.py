"""
Test suite for date_utils module

Tests date and time utility functions for financial calculations
"""

import pytest
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from app.utils.date_utils import DateUtils, default_date_utils


class TestDateUtils:
    """Test date utility functions"""
    
    def test_initialization(self):
        """Test DateUtils initialization"""
        utils = DateUtils()
        assert utils.country == 'US'
        
        utils_uk = DateUtils('UK')
        assert utils_uk.country == 'UK'
    
    def test_holiday_detection(self):
        """Test holiday detection"""
        utils = DateUtils()
        
        # New Year's Day 2024
        new_years = date(2024, 1, 1)
        assert utils.is_holiday(new_years)
        
        # Independence Day 2024
        july_4th = date(2024, 7, 4)
        assert utils.is_holiday(july_4th)
        
        # Regular business day (not a holiday)
        regular_day = date(2024, 1, 16)  # Tuesday (MLK Day is Jan 15)
        assert not utils.is_holiday(regular_day)
    
    def test_weekend_detection(self):
        """Test weekend detection"""
        utils = DateUtils()
        
        # Saturday
        saturday = date(2024, 1, 13)
        assert utils.is_weekend(saturday)
        
        # Sunday
        sunday = date(2024, 1, 14)
        assert utils.is_weekend(sunday)
        
        # Monday
        monday = date(2024, 1, 15)
        assert not utils.is_weekend(monday)
    
    def test_business_day_detection(self):
        """Test business day detection"""
        utils = DateUtils()
        
        # Regular Tuesday (not a holiday)
        tuesday = date(2024, 1, 16)
        assert utils.is_business_day(tuesday)
        
        # Weekend
        saturday = date(2024, 1, 13)
        assert not utils.is_business_day(saturday)
        
        # Holiday (New Year's Day 2024)
        new_years = date(2024, 1, 1)
        assert not utils.is_business_day(new_years)
    
    def test_date_adjustment_conventions(self):
        """Test business day adjustment conventions"""
        utils = DateUtils()
        
        # Test with Saturday (should move forward to Monday)
        saturday = date(2024, 1, 13)
        
        following = utils.adjust_date(saturday, "FOLLOWING")
        assert utils.is_business_day(following)
        assert following > saturday
        
        previous = utils.adjust_date(saturday, "PREVIOUS")
        assert utils.is_business_day(previous)
        assert previous < saturday
        
        # Test Modified Following
        # Use a date where following would cross month boundary
        month_end_saturday = date(2024, 3, 30)  # Last Saturday of March
        mod_following = utils.adjust_date(month_end_saturday, "MOD_FOLLOWING")
        assert utils.is_business_day(mod_following)
        # Should go to previous business day if following crosses month
        if mod_following.month != month_end_saturday.month:
            # Moved to next month, so should have gone to previous instead
            assert mod_following < month_end_saturday
    
    def test_next_business_day(self):
        """Test next business day calculation"""
        utils = DateUtils()
        
        # From Friday, add 1 business day should be Tuesday (since Monday Jan 15 is MLK Day)
        friday = date(2024, 1, 12)
        next_bd = utils.next_business_day(friday, 1)  # Add 1 business day
        assert next_bd == date(2024, 1, 16)  # Tuesday (skipping MLK Day Monday)
        assert utils.is_business_day(next_bd)
        
        # Add additional business days
        next_bd_plus_2 = utils.next_business_day(friday, 2)
        assert utils.is_business_day(next_bd_plus_2)
        assert next_bd_plus_2 > next_bd
    
    def test_previous_business_day(self):
        """Test previous business day calculation"""
        utils = DateUtils()
        
        # From Monday, previous business day should be Friday
        monday = date(2024, 1, 15)
        prev_bd = utils.previous_business_day(monday)
        assert prev_bd == date(2024, 1, 12)  # Friday
        assert utils.is_business_day(prev_bd)
        
        # Subtract additional business days
        prev_bd_minus_2 = utils.previous_business_day(monday, 2)
        assert utils.is_business_day(prev_bd_minus_2)
        assert prev_bd_minus_2 < prev_bd
    
    def test_add_business_days(self):
        """Test adding/subtracting business days"""
        utils = DateUtils()
        
        start = date(2024, 1, 16)  # Tuesday (not MLK Day)
        
        # Add 5 business days 
        result = utils.add_business_days(start, 5)
        # Should be next Tuesday (skip weekend)
        assert result == date(2024, 1, 23)
        assert utils.is_business_day(result)
        
        # Subtract 5 business days (should be previous Monday)
        result = utils.add_business_days(start, -5)
        assert result == date(2024, 1, 8)
        assert utils.is_business_day(result)
    
    def test_business_days_between(self):
        """Test counting business days between dates"""
        utils = DateUtils()
        
        # Monday to Friday (same week)
        monday = date(2024, 1, 15)
        friday = date(2024, 1, 19)
        
        count = utils.business_days_between(monday, friday)
        assert count == 3  # Tue, Wed, Thu (exclusive of end date)
        
        # Across weekend
        friday_start = date(2024, 1, 12)
        monday_end = date(2024, 1, 15)
        count = utils.business_days_between(friday_start, monday_end)
        assert count == 0  # Weekend in between, Monday is end date (exclusive)
    
    def test_add_months(self):
        """Test month addition"""
        utils = DateUtils()
        
        start = date(2024, 1, 15)
        
        # Add 3 months
        result = utils.add_months(start, 3)
        assert result == date(2024, 4, 15)
        
        # Test end of month handling
        jan_31 = date(2024, 1, 31)
        result = utils.add_months(jan_31, 1, end_of_month=True)
        assert result == date(2024, 2, 29)  # End of February (leap year)
        
        # Test month overflow (Jan 31 + 1 month normally)
        result = utils.add_months(jan_31, 1, end_of_month=False)
        assert result == date(2024, 2, 29)  # Adjusted to valid date
    
    def test_add_years(self):
        """Test year addition"""
        utils = DateUtils()
        
        start = date(2024, 2, 29)  # Leap year date
        result = utils.add_years(start, 1)
        assert result == date(2025, 2, 28)  # Adjusted for non-leap year
    
    def test_month_boundary_utilities(self):
        """Test month boundary utility functions"""
        utils = DateUtils()
        
        # Test end of month
        feb_15 = date(2024, 2, 15)
        eom = utils.end_of_month(feb_15)
        assert eom == date(2024, 2, 29)  # Leap year
        
        # Test beginning of month
        bom = utils.beginning_of_month(feb_15)
        assert bom == date(2024, 2, 1)
        
        # Test is_end_of_month
        assert utils.is_end_of_month(date(2024, 2, 29))
        assert not utils.is_end_of_month(date(2024, 2, 28))
    
    def test_days_in_month(self):
        """Test days in month calculation"""
        utils = DateUtils()
        
        assert utils.days_in_month(2024, 2) == 29  # Leap year February
        assert utils.days_in_month(2023, 2) == 28  # Non-leap year February
        assert utils.days_in_month(2024, 4) == 30  # April
        assert utils.days_in_month(2024, 1) == 31  # January
    
    def test_leap_year_detection(self):
        """Test leap year detection"""
        utils = DateUtils()
        
        assert utils.is_leap_year(2024)  # Leap year
        assert not utils.is_leap_year(2023)  # Not leap year
        assert utils.is_leap_year(2000)  # Century year divisible by 400
        assert not utils.is_leap_year(1900)  # Century year not divisible by 400
    
    def test_payment_schedule_generation(self):
        """Test payment schedule generation"""
        utils = DateUtils()
        
        start_date = date(2024, 1, 16)  # Tuesday (not MLK Day)
        end_date = date(2024, 12, 16)
        
        # Quarterly payments
        schedule = utils.generate_payment_schedule(
            start_date, end_date, "QUARTERLY"
        )
        
        assert len(schedule) == 4  # 4 quarters
        # First payment date should be start date (already a business day)
        assert schedule[0] == start_date
        assert schedule[1] == date(2024, 4, 16)  # 3 months from Jan 16
        assert schedule[2] == date(2024, 7, 16)  # 6 months from Jan 16
        assert schedule[3] == date(2024, 10, 16)  # 9 months from Jan 16
        
        # All dates should be business days (after adjustment)
        for payment_date in schedule:
            assert utils.is_business_day(payment_date)
    
    def test_quarterly_schedule_generation(self):
        """Test specific quarterly schedule generation"""
        utils = DateUtils()
        
        start_date = date(2024, 3, 15)
        schedule = utils.generate_quarterly_schedule(start_date, 4)
        
        assert len(schedule) == 4
        expected_dates = [
            date(2024, 3, 15),
            date(2024, 6, 15),  # Will be adjusted if weekend/holiday
            date(2024, 9, 15),  # Will be adjusted if weekend/holiday
            date(2024, 12, 15)  # Will be adjusted if weekend/holiday
        ]
        
        # Check that all dates are business days
        for payment_date in schedule:
            assert utils.is_business_day(payment_date)
    
    def test_tenor_parsing(self):
        """Test tenor string parsing"""
        utils = DateUtils()
        
        # Test valid tenors
        assert utils.parse_tenor("3M") == (3, "M")
        assert utils.parse_tenor("1Y") == (1, "Y")
        assert utils.parse_tenor("30D") == (30, "D")
        assert utils.parse_tenor("6m") == (6, "M")  # Case insensitive
        
        # Test invalid tenors
        with pytest.raises(ValueError):
            utils.parse_tenor("3X")  # Invalid period
        
        with pytest.raises(ValueError):
            utils.parse_tenor("ABC")  # No number
    
    def test_add_tenor(self):
        """Test tenor addition to dates"""
        utils = DateUtils()
        
        start_date = date(2024, 1, 15)
        
        # Add 3 months
        result = utils.add_tenor(start_date, "3M")
        assert result == date(2024, 4, 15)
        
        # Add 1 year
        result = utils.add_tenor(start_date, "1Y")
        assert result == date(2025, 1, 15)
        
        # Add 30 days
        result = utils.add_tenor(start_date, "30D")
        assert result == start_date + timedelta(days=30)
    
    def test_financial_calendar_utilities(self):
        """Test financial calendar utilities"""
        utils = DateUtils()
        
        # Test quarterly dates
        q_dates = utils.get_quarterly_dates(2024)
        expected = [
            date(2024, 3, 31),
            date(2024, 6, 30),
            date(2024, 9, 30),
            date(2024, 12, 31)
        ]
        assert q_dates == expected
        
        # Test semi-annual dates
        sa_dates = utils.get_semi_annual_dates(2024)
        expected = [date(2024, 6, 30), date(2024, 12, 31)]
        assert sa_dates == expected
    
    def test_quarter_end_navigation(self):
        """Test quarter end date navigation"""
        utils = DateUtils()
        
        # Test next quarter end
        jan_15 = date(2024, 1, 15)
        next_qe = utils.next_quarter_end(jan_15)
        assert next_qe == date(2024, 3, 31)
        
        may_15 = date(2024, 5, 15)
        next_qe = utils.next_quarter_end(may_15)
        assert next_qe == date(2024, 6, 30)
        
        # Test previous quarter end
        apr_15 = date(2024, 4, 15)
        prev_qe = utils.previous_quarter_end(apr_15)
        assert prev_qe == date(2024, 3, 31)
    
    def test_date_validation(self):
        """Test date validation utilities"""
        utils = DateUtils()
        
        # Test date range validation
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        assert utils.validate_date_range(start, end)
        assert not utils.validate_date_range(end, start)
        
        # Test payment date validation
        business_day = date(2024, 1, 16)  # Tuesday (not MLK Day)
        weekend = date(2024, 1, 13)  # Saturday
        
        assert utils.validate_payment_date(business_day, require_business_day=True)
        assert not utils.validate_payment_date(weekend, require_business_day=True)
        assert utils.validate_payment_date(weekend, require_business_day=False)
    
    def test_date_formatting(self):
        """Test date formatting and parsing"""
        utils = DateUtils()
        
        test_date = date(2024, 1, 15)
        
        # Test formatting
        formatted = utils.format_date(test_date, "%Y-%m-%d")
        assert formatted == "2024-01-15"
        
        formatted = utils.format_date(test_date, "%m/%d/%Y")
        assert formatted == "01/15/2024"
        
        # Test parsing
        parsed = utils.parse_date("2024-01-15", "%Y-%m-%d")
        assert parsed == test_date
    
    def test_excel_date_conversion(self):
        """Test Excel date serial number conversion"""
        utils = DateUtils()
        
        # Excel day 1 is 1900-01-01 (but Excel has leap year bug)
        test_date = date(2024, 1, 1)
        excel_serial = utils.to_excel_date(test_date)
        
        # Convert back
        converted_back = utils.from_excel_date(excel_serial)
        assert converted_back == test_date
    
    def test_convenience_functions(self):
        """Test module-level convenience functions"""
        from app.utils.date_utils import (is_business_day, next_business_day, 
                                        adjust_date, add_months)
        
        tuesday = date(2024, 1, 16)  # Tuesday (not MLK Day)
        
        # Test convenience functions work the same as methods
        assert is_business_day(tuesday)
        
        next_bd = next_business_day(tuesday, 1)
        assert is_business_day(next_bd)
        assert next_bd > tuesday
        
        adjusted = adjust_date(date(2024, 1, 13))  # Saturday
        assert is_business_day(adjusted)
        
        future_date = add_months(tuesday, 3)
        assert future_date == date(2024, 4, 16)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        utils = DateUtils()
        
        # Test with leap year edge cases
        leap_day = date(2024, 2, 29)
        next_year = utils.add_years(leap_day, 1)
        assert next_year == date(2025, 2, 28)  # Adjusted for non-leap year
        
        # Test month addition across year boundary
        dec_31 = date(2023, 12, 31)
        jan_result = utils.add_months(dec_31, 1)
        assert jan_result == date(2024, 1, 31)
        
        # Test February edge case
        jan_31 = date(2024, 1, 31)
        feb_result = utils.add_months(jan_31, 1)
        assert feb_result == date(2024, 2, 29)  # Adjusted for February
        
        # Test business days with holidays
        # If a holiday falls on a weekend, it should still be handled correctly
        # This tests the interaction between weekend and holiday detection