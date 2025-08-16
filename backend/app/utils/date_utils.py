"""
Date and Time Utilities

Provides date manipulation functions for the CLO system including:
- Business day calculations with holiday handling
- Payment date scheduling
- Date arithmetic with various conventions
- Calendar utilities for financial calculations

This complements the date functions in math_utils.py with more specialized
date handling for financial applications.
"""

from typing import List, Optional, Set, Union
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.easter import easter
import holidays
import calendar
import logging

logger = logging.getLogger(__name__)


class DateUtils:
    """Date utility functions for financial calculations"""
    
    def __init__(self, country: str = 'US'):
        """Initialize with holiday calendar for specified country"""
        self.country = country
        self._holidays_cache = {}
        self._load_holidays()
    
    def _load_holidays(self):
        """Load holiday calendar"""
        if self.country.upper() == 'US':
            # US Federal holidays
            self._holiday_calendar = holidays.US()
            # Add custom financial market holidays if needed
            self._add_custom_holidays()
        else:
            # Default to US holidays
            self._holiday_calendar = holidays.US()
    
    def _add_custom_holidays(self):
        """Add custom holidays specific to financial markets"""
        # Add Good Friday (not a federal holiday but markets are closed)
        for year in range(2000, 2051):
            good_friday = easter(year) - timedelta(days=2)
            self._holiday_calendar[good_friday] = "Good Friday"
    
    def is_holiday(self, check_date: date) -> bool:
        """Check if date is a holiday"""
        return check_date in self._holiday_calendar
    
    def is_weekend(self, check_date: date) -> bool:
        """Check if date is weekend (Saturday or Sunday)"""
        return check_date.weekday() in [5, 6]  # Saturday=5, Sunday=6
    
    def is_business_day(self, check_date: date) -> bool:
        """Check if date is a business day (not weekend or holiday)"""
        return not (self.is_weekend(check_date) or self.is_holiday(check_date))
    
    # Business Day Adjustment Methods
    def adjust_date(self, check_date: date, convention: str = "FOLLOWING") -> date:
        """
        Adjust date according to business day convention
        
        Conventions:
        - FOLLOWING: Move to next business day
        - PREVIOUS: Move to previous business day
        - MOD_FOLLOWING: Following, unless it moves to next month, then previous
        - MOD_PREVIOUS: Previous, unless it moves to previous month, then following
        - NONE: No adjustment
        """
        if self.is_business_day(check_date):
            return check_date
        
        convention_upper = convention.upper()
        
        if convention_upper == "FOLLOWING":
            return self.next_business_day(check_date)
        elif convention_upper == "PREVIOUS":
            return self.previous_business_day(check_date)
        elif convention_upper == "MOD_FOLLOWING":
            next_bd = self.next_business_day(check_date)
            # If moved to next month, use previous business day instead
            if next_bd.month != check_date.month:
                return self.previous_business_day(check_date)
            return next_bd
        elif convention_upper == "MOD_PREVIOUS":
            prev_bd = self.previous_business_day(check_date)
            # If moved to previous month, use next business day instead
            if prev_bd.month != check_date.month:
                return self.next_business_day(check_date)
            return prev_bd
        else:  # NONE or unknown
            return check_date
    
    def next_business_day(self, start_date: date, days: int = 0) -> date:
        """Get next business day, optionally adding additional business days"""
        current = start_date
        
        # First move to next business day if current isn't one
        while not self.is_business_day(current):
            current += timedelta(days=1)
        
        # Add additional business days if requested
        business_days_added = 0
        while business_days_added < days:
            current += timedelta(days=1)
            if self.is_business_day(current):
                business_days_added += 1
        
        return current
    
    def previous_business_day(self, start_date: date, days: int = 0) -> date:
        """Get previous business day, optionally subtracting additional business days"""
        current = start_date
        
        # First move to previous business day if current isn't one
        while not self.is_business_day(current):
            current -= timedelta(days=1)
        
        # Subtract additional business days if requested
        business_days_subtracted = 0
        while business_days_subtracted < days:
            current -= timedelta(days=1)
            if self.is_business_day(current):
                business_days_subtracted += 1
        
        return current
    
    def add_business_days(self, start_date: date, days: int) -> date:
        """Add business days to date"""
        if days == 0:
            return start_date
        elif days > 0:
            return self.next_business_day(start_date, days)
        else:
            return self.previous_business_day(start_date, abs(days))
    
    def business_days_between(self, start_date: date, end_date: date) -> int:
        """Count business days between two dates (exclusive of end date)"""
        if start_date >= end_date:
            return 0
        
        count = 0
        current = start_date + timedelta(days=1)
        
        while current < end_date:
            if self.is_business_day(current):
                count += 1
            current += timedelta(days=1)
        
        return count
    
    # Date Arithmetic
    def add_months(self, start_date: date, months: int, 
                   end_of_month: bool = False) -> date:
        """Add months to date with optional end-of-month handling"""
        if months == 0:
            return start_date
        
        new_date = start_date + relativedelta(months=months)
        
        if end_of_month:
            # Move to end of month
            new_date = self.end_of_month(new_date)
        
        return new_date
    
    def add_years(self, start_date: date, years: int) -> date:
        """Add years to date"""
        return start_date + relativedelta(years=years)
    
    def end_of_month(self, check_date: date) -> date:
        """Get last day of month"""
        next_month = check_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    
    def beginning_of_month(self, check_date: date) -> date:
        """Get first day of month"""
        return check_date.replace(day=1)
    
    def is_end_of_month(self, check_date: date) -> bool:
        """Check if date is last day of month"""
        return check_date == self.end_of_month(check_date)
    
    def days_in_month(self, year: int, month: int) -> int:
        """Get number of days in month"""
        return calendar.monthrange(year, month)[1]
    
    def is_leap_year(self, year: int) -> bool:
        """Check if year is leap year"""
        return calendar.isleap(year)
    
    # Payment Scheduling
    def generate_payment_schedule(self, start_date: date, end_date: date,
                                frequency: str, 
                                adjustment_convention: str = "MOD_FOLLOWING",
                                end_of_month: bool = False) -> List[date]:
        """
        Generate payment schedule between start and end dates
        
        Args:
            start_date: First payment date or schedule start
            end_date: Final payment date or schedule end
            frequency: Payment frequency (MONTHLY, QUARTERLY, SEMI_ANNUALLY, ANNUALLY)
            adjustment_convention: Business day adjustment method
            end_of_month: Whether to use end-of-month convention
        
        Returns:
            List of payment dates
        """
        frequency_upper = frequency.upper()
        
        # Determine months between payments
        if frequency_upper == "MONTHLY":
            months_increment = 1
        elif frequency_upper == "QUARTERLY":
            months_increment = 3
        elif frequency_upper in ["SEMI_ANNUALLY", "SEMI-ANNUALLY"]:
            months_increment = 6
        elif frequency_upper == "ANNUALLY":
            months_increment = 12
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")
        
        schedule = []
        current_date = start_date
        
        while current_date <= end_date:
            # Adjust for business day convention
            adjusted_date = self.adjust_date(current_date, adjustment_convention)
            schedule.append(adjusted_date)
            
            # Move to next payment date
            current_date = self.add_months(current_date, months_increment, end_of_month)
        
        return schedule
    
    def generate_quarterly_schedule(self, start_date: date, num_quarters: int,
                                  adjustment_convention: str = "MOD_FOLLOWING") -> List[date]:
        """Generate quarterly payment schedule (common for CLO deals)"""
        schedule = []
        current_date = start_date
        
        for _ in range(num_quarters):
            adjusted_date = self.adjust_date(current_date, adjustment_convention)
            schedule.append(adjusted_date)
            current_date = self.add_months(current_date, 3)
        
        return schedule
    
    # Tenor and Period Calculations
    def parse_tenor(self, tenor_str: str) -> tuple:
        """
        Parse tenor string (e.g., '3M', '1Y', '6M') into number and period
        
        Returns:
            Tuple of (number, period) where period is 'D', 'M', or 'Y'
        """
        tenor_str = tenor_str.upper().strip()
        
        if tenor_str[-1] in ['D', 'M', 'Y']:
            period = tenor_str[-1]
            try:
                number = int(tenor_str[:-1])
                return number, period
            except ValueError:
                raise ValueError(f"Invalid tenor format: {tenor_str}")
        else:
            raise ValueError(f"Tenor must end with D, M, or Y: {tenor_str}")
    
    def add_tenor(self, start_date: date, tenor: str,
                  adjustment_convention: str = "FOLLOWING") -> date:
        """Add tenor to date (e.g., add '3M' for 3 months)"""
        number, period = self.parse_tenor(tenor)
        
        if period == 'D':
            new_date = start_date + timedelta(days=number)
        elif period == 'M':
            new_date = self.add_months(start_date, number)
        elif period == 'Y':
            new_date = self.add_years(start_date, number)
        else:
            raise ValueError(f"Invalid period: {period}")
        
        return self.adjust_date(new_date, adjustment_convention)
    
    # Financial Calendar Utilities
    def get_quarterly_dates(self, year: int) -> List[date]:
        """Get standard quarterly dates for a year (Mar 31, Jun 30, Sep 30, Dec 31)"""
        return [
            date(year, 3, 31),
            date(year, 6, 30),
            date(year, 9, 30),
            date(year, 12, 31)
        ]
    
    def get_semi_annual_dates(self, year: int) -> List[date]:
        """Get standard semi-annual dates for a year (Jun 30, Dec 31)"""
        return [
            date(year, 6, 30),
            date(year, 12, 31)
        ]
    
    def next_quarter_end(self, from_date: date) -> date:
        """Get next quarter end date"""
        year = from_date.year
        if from_date <= date(year, 3, 31):
            return date(year, 3, 31)
        elif from_date <= date(year, 6, 30):
            return date(year, 6, 30)
        elif from_date <= date(year, 9, 30):
            return date(year, 9, 30)
        elif from_date <= date(year, 12, 31):
            return date(year, 12, 31)
        else:
            return date(year + 1, 3, 31)
    
    def previous_quarter_end(self, from_date: date) -> date:
        """Get previous quarter end date"""
        year = from_date.year
        if from_date > date(year, 12, 31):
            return date(year, 12, 31)
        elif from_date > date(year, 9, 30):
            return date(year, 9, 30)
        elif from_date > date(year, 6, 30):
            return date(year, 6, 30)
        elif from_date > date(year, 3, 31):
            return date(year, 3, 31)
        else:
            return date(year - 1, 12, 31)
    
    # Date Validation
    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """Validate that start_date <= end_date"""
        return start_date <= end_date
    
    def validate_payment_date(self, payment_date: date,
                            require_business_day: bool = True) -> bool:
        """Validate payment date"""
        if require_business_day:
            return self.is_business_day(payment_date)
        return True
    
    # Date Formatting and Conversion
    def format_date(self, check_date: date, format_str: str = "%Y-%m-%d") -> str:
        """Format date as string"""
        return check_date.strftime(format_str)
    
    def parse_date(self, date_str: str, format_str: str = "%Y-%m-%d") -> date:
        """Parse date from string"""
        return datetime.strptime(date_str, format_str).date()
    
    def to_excel_date(self, check_date: date) -> int:
        """Convert date to Excel serial number (days since 1900-01-01)"""
        # Excel incorrectly treats 1900 as a leap year, so we adjust
        base_date = date(1899, 12, 30)  # Excel day 0
        return (check_date - base_date).days
    
    def from_excel_date(self, excel_date: int) -> date:
        """Convert Excel serial number to date"""
        base_date = date(1899, 12, 30)  # Excel day 0
        return base_date + timedelta(days=excel_date)


# Global instance for convenience
default_date_utils = DateUtils()

# Module-level convenience functions
def is_business_day(check_date: date) -> bool:
    """Check if date is a business day"""
    return default_date_utils.is_business_day(check_date)

def next_business_day(start_date: date, days: int = 0) -> date:
    """Get next business day"""
    return default_date_utils.next_business_day(start_date, days)

def previous_business_day(start_date: date, days: int = 0) -> date:
    """Get previous business day"""
    return default_date_utils.previous_business_day(start_date, days)

def adjust_date(check_date: date, convention: str = "FOLLOWING") -> date:
    """Adjust date for business day convention"""
    return default_date_utils.adjust_date(check_date, convention)

def add_months(start_date: date, months: int, end_of_month: bool = False) -> date:
    """Add months to date"""
    return default_date_utils.add_months(start_date, months, end_of_month)

def generate_payment_schedule(start_date: date, end_date: date, frequency: str) -> List[date]:
    """Generate payment schedule"""
    return default_date_utils.generate_payment_schedule(start_date, end_date, frequency)

def add_tenor(start_date: date, tenor: str) -> date:
    """Add tenor to date"""
    return default_date_utils.add_tenor(start_date, tenor)

def get_analysis_date(analysis_date_str: Optional[str] = None) -> date:
    """
    Get analysis date - either from parameter or default to March 23, 2016
    
    Args:
        analysis_date_str: Optional date string in YYYY-MM-DD format
        
    Returns:
        Date object for analysis
    """
    if analysis_date_str:
        try:
            return datetime.strptime(analysis_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {analysis_date_str}")
    return date(2016, 3, 23)  # Default analysis date: March 23, 2016

def validate_analysis_date(analysis_date_str: str) -> bool:
    """
    Validate analysis date string format and reasonable bounds
    
    Args:
        analysis_date_str: Date string in YYYY-MM-DD format
        
    Returns:
        True if valid, False otherwise
    """
    try:
        parsed_date = datetime.strptime(analysis_date_str, "%Y-%m-%d").date()
        
        # Check reasonable bounds (not too far in past/future)
        min_date = date(2010, 1, 1)  # Allow dates back to 2010
        max_date = date.today() + timedelta(days=365)  # Allow 1 year in future
        
        return min_date <= parsed_date <= max_date
    except ValueError:
        return False