"""
Mathematical Utilities Module

Converted from VBA Math.bas module - provides mathematical calculations,
date utilities, and financial computations for the CLO system.

This module provides VBA-compatible functions for:
- Statistical calculations (mean, median, std dev)
- Business date calculations
- Day count conventions
- Financial calculations (PV, yield, spread)
- Interest rate conversions
"""

from typing import List, Optional, Union, Dict, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal, getcontext
import math
import numpy as np
from enum import IntEnum
import holidays
import logging

logger = logging.getLogger(__name__)

# Set precision for financial calculations
getcontext().prec = 15

class DayCount(IntEnum):
    """Day count conventions matching VBA enum"""
    US30_360 = 0
    ACTUAL_ACTUAL = 1
    ACTUAL_360 = 2
    ACTUAL_365 = 3
    EU30_360 = 4


class MathUtils:
    """Mathematical utility functions converted from VBA Math.bas"""
    
    def __init__(self):
        """Initialize with US federal holidays"""
        self._holidays = holidays.US(years=range(2000, 2050))
    
    # Statistical Functions
    @staticmethod
    def min_array(values: List[Union[int, float]]) -> Union[int, float]:
        """Find minimum value in array"""
        if not values:
            raise ValueError("Array cannot be empty")
        return min(values)
    
    @staticmethod
    def max_array(values: List[Union[int, float]]) -> Union[int, float]:
        """Find maximum value in array"""
        if not values:
            raise ValueError("Array cannot be empty")
        return max(values)
    
    @staticmethod
    def average_array(values: List[Union[int, float]]) -> float:
        """Calculate average of array values"""
        if not values:
            raise ValueError("Array cannot be empty")
        return sum(values) / len(values)
    
    @staticmethod
    def std_array(values: List[Union[int, float]]) -> float:
        """Calculate standard deviation of array values"""
        if not values:
            raise ValueError("Array cannot be empty")
        
        avg = MathUtils.average_array(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    @staticmethod
    def median_array(values: List[Union[int, float]]) -> float:
        """Calculate median of array values"""
        if not values:
            raise ValueError("Array cannot be empty")
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n == 1:
            return sorted_values[0]
        elif n == 2:
            return (sorted_values[0] + sorted_values[1]) / 2
        elif n % 2 == 0:
            # Even number of elements
            mid = n // 2
            return (sorted_values[mid - 1] + sorted_values[mid]) / 2
        else:
            # Odd number of elements
            return sorted_values[n // 2]
    
    # Date Utility Functions
    def check_business_date(self, start_date: date, 
                          payment_adj_method: Optional[str] = None) -> date:
        """Check if date is business day and adjust if necessary"""
        if self._is_business_day(start_date):
            return start_date
        
        if (payment_adj_method and 
            payment_adj_method.upper() == "MOD FOLLOWING" and 
            self._is_month_end(start_date + timedelta(days=1))):
            return self._get_previous_business_date(start_date, 1)
        elif (payment_adj_method and 
              payment_adj_method.upper() == "PREVIOUS"):
            return self._get_previous_business_date(start_date, 1)
        else:
            return self._get_next_business_date(start_date, 1)
    
    def date_add_business(self, interval: str, number: int, start_date: date,
                         payment_adj_method: Optional[str] = None,
                         end_of_month: bool = False) -> date:
        """Add business days/months/years to date with adjustment"""
        if interval.lower() == "m":
            # Add months
            new_date = self._add_months(start_date, number)
        elif interval.lower() == "y":
            # Add years
            new_date = self._add_months(start_date, number * 12)
        elif interval.lower() == "d":
            # Add days
            new_date = start_date + timedelta(days=number)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        if end_of_month:
            # Move to end of month
            next_month = self._add_months(new_date, 1)
            new_date = next_month.replace(day=1) - timedelta(days=1)
        
        # Apply payment adjustment
        if payment_adj_method:
            if (payment_adj_method.upper() == "MOD FOLLOWING" and
                self._is_month_end(new_date + timedelta(days=1))):
                new_date = self._get_previous_business_date(new_date, 0)
            elif payment_adj_method.upper() in ["FOLLOWING", "MOD FOLLOWING"]:
                new_date = self._get_next_business_date(new_date, 0)
            elif payment_adj_method.upper() == "PREVIOUS":
                new_date = self._get_previous_business_date(new_date, 0)
        
        return new_date
    
    def _get_next_business_date(self, start_date: date, num_days: int) -> date:
        """Get next business date"""
        current = start_date
        
        # First, move to next business day if current is not
        while not self._is_business_day(current):
            current += timedelta(days=1)
        
        # Then add the required number of business days
        days_added = 0
        while days_added < num_days:
            current += timedelta(days=1)
            if self._is_business_day(current):
                days_added += 1
        
        return current
    
    def _get_previous_business_date(self, start_date: date, num_days: int) -> date:
        """Get previous business date"""
        current = start_date
        
        # First, move to previous business day if current is not
        while not self._is_business_day(current):
            current -= timedelta(days=1)
        
        # Then subtract the required number of business days
        days_subtracted = 0
        while days_subtracted < num_days:
            current -= timedelta(days=1)
            if self._is_business_day(current):
                days_subtracted += 1
        
        return current
    
    def _is_business_day(self, check_date: date) -> bool:
        """Check if date is a business day (not weekend or holiday)"""
        # Check if weekend (Saturday = 5, Sunday = 6)
        if check_date.weekday() in [5, 6]:
            return False
        
        # Check if holiday
        if check_date in self._holidays:
            return False
        
        return True
    
    def _is_month_end(self, check_date: date) -> bool:
        """Check if date is first day of month (indicating previous was month end)"""
        return check_date.day == 1
    
    def _add_months(self, start_date: date, months: int) -> date:
        """Add months to date"""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, self._days_in_month(year, month))
        return date(year, month, day)
    
    def _days_in_month(self, year: int, month: int) -> int:
        """Get number of days in month"""
        if month == 12:
            return (date(year + 1, 1, 1) - date(year, 12, 1)).days
        else:
            return (date(year, month + 1, 1) - date(year, month, 1)).days
    
    # Day Count Functions
    @staticmethod
    def date_fraction(start_date: date, end_date: date, 
                     daycount: DayCount) -> float:
        """Calculate year fraction between dates using day count convention"""
        return MathUtils.year_frac(start_date, end_date, daycount)
    
    @staticmethod
    def year_frac(date1: date, date2: date, daycount: DayCount) -> float:
        """Calculate year fraction between dates"""
        if daycount == DayCount.US30_360:
            return MathUtils._days_30_360(date1, date2, False) / 360.0
        elif daycount == DayCount.EU30_360:
            return MathUtils._days_30_360(date1, date2, True) / 360.0
        elif daycount == DayCount.ACTUAL_360:
            return (date2 - date1).days / 360.0
        elif daycount == DayCount.ACTUAL_365:
            return (date2 - date1).days / 365.0
        elif daycount == DayCount.ACTUAL_ACTUAL:
            return MathUtils._actual_actual_year_frac(date1, date2)
        else:
            return MathUtils._days_30_360(date1, date2, False) / 360.0
    
    @staticmethod
    def days_between(date1: date, date2: date, daycount: DayCount) -> int:
        """Calculate days between dates using day count convention"""
        if daycount == DayCount.US30_360:
            return MathUtils._days_30_360(date1, date2, False)
        elif daycount == DayCount.EU30_360:
            return MathUtils._days_30_360(date1, date2, True)
        else:
            return (date2 - date1).days
    
    @staticmethod
    def _days_30_360(date1: date, date2: date, european: bool = False) -> int:
        """Calculate days using 30/360 convention"""
        y1, m1, d1 = date1.year, date1.month, date1.day
        y2, m2, d2 = date2.year, date2.month, date2.day
        
        if european:
            # European 30/360
            if d1 == 31:
                d1 = 30
            if d2 == 31:
                d2 = 30
        else:
            # US 30/360
            if d1 == 31:
                d1 = 30
            if d2 == 31 and d1 >= 30:
                d2 = 30
        
        return 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
    
    @staticmethod
    def _actual_actual_year_frac(date1: date, date2: date) -> float:
        """Calculate year fraction using Actual/Actual convention"""
        if date1 == date2:
            return 0.0
        
        if date1 > date2:
            date1, date2 = date2, date1
        
        # Simple approximation - can be enhanced for exact ISDA calculations
        days = (date2 - date1).days
        
        # Check if leap year is involved
        years_spanned = list(range(date1.year, date2.year + 1))
        total_days_in_years = sum(366 if MathUtils._is_leap_year(year) else 365 
                                 for year in years_spanned)
        avg_year_length = total_days_in_years / len(years_spanned)
        
        return days / avg_year_length
    
    @staticmethod
    def _is_leap_year(year: int) -> bool:
        """Check if year is leap year"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    # Financial Calculation Functions
    @staticmethod
    def calc_pv(cashflows: List[float], dates: List[date], 
                settlement_date: date, yield_rate: float,
                daycount: DayCount, pay_per_year: int) -> float:
        """Calculate present value of cashflows"""
        if len(cashflows) != len(dates):
            raise ValueError("Cashflows and dates must have same length")
        
        if not cashflows:
            return 0.0
        
        pv = 0.0
        
        for i, (cf, cf_date) in enumerate(zip(cashflows, dates)):
            if i == 0:
                # First cashflow
                discount = MathUtils.calc_discount(
                    yield_rate, settlement_date, cf_date, 
                    daycount, pay_per_year, True
                )
            else:
                # Subsequent cashflows
                discount *= MathUtils.calc_discount(
                    yield_rate, dates[i-1], cf_date,
                    daycount, pay_per_year, False
                )
            
            pv += cf * discount
        
        return pv
    
    @staticmethod
    def calc_discount(yield_rate: float, date1: date, date2: date,
                     daycount: DayCount, pay_per_year: int, 
                     is_settlement: bool) -> float:
        """Calculate discount factor between dates"""
        compound_factor = MathUtils.calc_compound(
            yield_rate, date1, date2, daycount, pay_per_year, is_settlement
        )
        return 1.0 / compound_factor if compound_factor != 0 else 0.0
    
    @staticmethod
    def calc_compound(yield_rate: float, date1: date, date2: date,
                     daycount: DayCount, pay_per_year: int,
                     is_settlement: bool) -> float:
        """Calculate compounding factor between dates"""
        periods = MathUtils._compounding_periods_between_dates(
            date1, date2, 12 // pay_per_year, daycount, is_settlement
        )
        return (1 + yield_rate / pay_per_year) ** periods
    
    @staticmethod
    def _compounding_periods_between_dates(start_date: date, end_date: date,
                                         months_per_period: int, 
                                         daycount: DayCount,
                                         is_settlement: bool) -> float:
        """Calculate number of compounding periods between dates"""
        if start_date >= end_date:
            return 0.0
        
        total_fraction = 0.0
        current_date = start_date
        
        if is_settlement:
            # Work backwards from end date
            temp_date = end_date
            while True:
                prev_date = MathUtils._add_months(temp_date, -months_per_period)
                if prev_date <= start_date:
                    break
                total_fraction += 1.0
                temp_date = prev_date
            
            # Add fractional period
            if temp_date > start_date:
                period_start = MathUtils._add_months(temp_date, months_per_period)
                total_fraction += (MathUtils.days_between(start_date, period_start, daycount) / 
                                 MathUtils.days_between(temp_date, period_start, daycount))
        else:
            # Work forwards from start date
            while True:
                next_date = MathUtils._add_months(current_date, months_per_period)
                if next_date >= end_date:
                    break
                total_fraction += 1.0
                current_date = next_date
            
            # Add fractional period
            if current_date < end_date:
                next_date = MathUtils._add_months(current_date, months_per_period)
                total_fraction += (MathUtils.days_between(current_date, end_date, daycount) /
                                 MathUtils.days_between(current_date, next_date, daycount))
        
        return total_fraction
    
    @staticmethod
    def _add_months(start_date: date, months: int) -> date:
        """Add months to date (static version)"""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, 
                 [31,29,31,30,31,30,31,31,30,31,30,31][month-1] if month != 2 or 
                 MathUtils._is_leap_year(year) else 28)
        return date(year, month, day)
    
    # Interest Rate Conversion Functions
    @staticmethod
    def convert_annual_rates(annual_rate: float, start_date: date, 
                           end_date: date) -> float:
        """Convert annual rate to period rate"""
        if start_date == end_date:
            return 0.0
        
        try:
            days = MathUtils._days_30_360(start_date, end_date, False)
            divisor = 360.0 / days
            return 1.0 - (1.0 - annual_rate) ** (1.0 / divisor)
        except (ZeroDivisionError, ValueError):
            return 0.0
    
    # Day Count Enum Conversion
    @staticmethod
    def get_daycount_enum(daycount_str: str) -> DayCount:
        """Convert day count string to enum"""
        daycount_upper = daycount_str.upper()
        
        if daycount_upper == "30/360":
            return DayCount.US30_360
        elif daycount_upper == "ACTUAL/ACTUAL":
            return DayCount.ACTUAL_ACTUAL
        elif daycount_upper in ["ACTUAL/365", "ACT365"]:
            return DayCount.ACTUAL_365
        elif daycount_upper in ["ACTUAL/360", "ACT360"]:
            return DayCount.ACTUAL_360
        elif daycount_upper == "30/360EU":
            return DayCount.EU30_360
        else:
            return DayCount.US30_360
    
    # Payment Frequency Utilities
    @staticmethod
    def get_months(frequency_str: str) -> int:
        """Get months per payment from frequency string"""
        freq_upper = frequency_str.upper()
        
        if freq_upper == "ANNUALLY":
            return 12
        elif freq_upper == "SEMI-ANNUALLY":
            return 6
        elif freq_upper == "QUARTERLY":
            return 3
        elif freq_upper == "MONTHLY":
            return 1
        else:
            return 12
    
    @staticmethod
    def get_payments_per_year(frequency_str: str) -> int:
        """Get payments per year from frequency string"""
        freq_upper = frequency_str.upper()
        
        if freq_upper == "ANNUALLY":
            return 1
        elif freq_upper == "SEMI-ANNUALLY":
            return 2
        elif freq_upper == "QUARTERLY":
            return 4
        elif freq_upper == "MONTHLY":
            return 12
        else:
            return 1
    
    # Weighted Average Life Calculation
    @staticmethod
    def wal(cashflows: List[float], periods_per_year: float) -> float:
        """Calculate Weighted Average Life"""
        if not cashflows:
            return 0.0
        
        weighted_sum = 0.0
        total_cf = 0.0
        
        for i, cf in enumerate(cashflows[1:], 1):  # Skip period 0
            weighted_sum += cf * i
            total_cf += cf
        
        if total_cf == 0:
            return 0.0
        
        return (weighted_sum / total_cf) / periods_per_year
    
    # Random Number Generation
    @staticmethod
    def rand() -> float:
        """Generate random number between 0 and 1 (excluding 0)"""
        import random
        x = 0.0
        while x <= 0.0:
            x = random.random()
        return x


# Module-level convenience functions
def min_array(values: List[Union[int, float]]) -> Union[int, float]:
    """Convenience function for min calculation"""
    return MathUtils.min_array(values)

def max_array(values: List[Union[int, float]]) -> Union[int, float]:
    """Convenience function for max calculation"""
    return MathUtils.max_array(values)

def average_array(values: List[Union[int, float]]) -> float:
    """Convenience function for average calculation"""
    return MathUtils.average_array(values)

def std_array(values: List[Union[int, float]]) -> float:
    """Convenience function for standard deviation calculation"""
    return MathUtils.std_array(values)

def median_array(values: List[Union[int, float]]) -> float:
    """Convenience function for median calculation"""
    return MathUtils.median_array(values)

def year_frac(date1: date, date2: date, daycount: DayCount) -> float:
    """Convenience function for year fraction calculation"""
    return MathUtils.year_frac(date1, date2, daycount)