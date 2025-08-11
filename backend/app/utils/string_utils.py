"""
String and Formatting Utilities

Provides string manipulation and formatting functions for the CLO system including:
- Text parsing and validation
- Number formatting for financial display
- Data type conversions
- String utilities for asset and deal processing
- Excel-compatible formatting functions

This supports the data processing and display requirements of the CLO system.
"""

from typing import Any, List, Optional, Union, Dict, Tuple
import re
import decimal
from decimal import Decimal
import datetime
from datetime import date
import logging

logger = logging.getLogger(__name__)


class StringUtils:
    """String manipulation and formatting utilities"""
    
    # Text Parsing and Validation
    @staticmethod
    def is_numeric(value: str) -> bool:
        """Check if string represents a numeric value"""
        if not isinstance(value, str):
            return False
        
        try:
            float(value.replace(',', '').strip())
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def parse_numeric(value: str, default: float = 0.0) -> float:
        """Parse string to numeric value with fallback"""
        if not isinstance(value, str):
            if isinstance(value, (int, float)):
                return float(value)
            return default
        
        try:
            # Remove common formatting characters including currency symbols
            cleaned = value.replace(',', '').replace('$', '').replace('€', '').replace('£', '').replace('%', '').strip()
            
            # Handle percentage
            if '%' in value:
                return float(cleaned) / 100.0
            
            return float(cleaned)
        except (ValueError, TypeError):
            logger.debug(f"Could not parse numeric value: {value}")
            return default
    
    @staticmethod
    def parse_integer(value: str, default: int = 0) -> int:
        """Parse string to integer with fallback"""
        if not isinstance(value, str):
            if isinstance(value, (int, float)):
                return int(value)
            return default
        
        try:
            cleaned = value.replace(',', '').strip()
            return int(float(cleaned))  # Handle "100.0" -> 100
        except (ValueError, TypeError):
            logger.debug(f"Could not parse integer value: {value}")
            return default
    
    @staticmethod
    def is_valid_rating(rating: str) -> bool:
        """Validate credit rating format"""
        if not isinstance(rating, str):
            return False
        
        rating = rating.strip().upper()
        
        # Moody's ratings
        moody_pattern = r'^(AAA|AA[123]?|A[123]?|BAA[123]?|BA[123]?|B[123]?|CAA[123]?|CA|C)$'
        
        # S&P/Fitch ratings
        sp_pattern = r'^(AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC[+-]?|CC|C|D)$'
        
        return bool(re.match(moody_pattern, rating) or re.match(sp_pattern, rating))
    
    @staticmethod
    def standardize_rating(rating: str) -> str:
        """Standardize rating format"""
        if not isinstance(rating, str):
            return "NR"
        
        rating = rating.strip().upper()
        
        if not StringUtils.is_valid_rating(rating):
            return "NR"  # Not Rated
        
        return rating
    
    # Financial Formatting
    @staticmethod
    def format_currency(amount: Union[float, int, Decimal], 
                       currency_symbol: str = "$",
                       decimal_places: int = 2,
                       thousands_separator: bool = True) -> str:
        """Format number as currency"""
        try:
            if amount is None:
                return f"{currency_symbol}0.00"
            
            amount_decimal = Decimal(str(amount))
            
            if thousands_separator:
                formatted = f"{amount_decimal:,.{decimal_places}f}"
            else:
                formatted = f"{amount_decimal:.{decimal_places}f}"
            
            return f"{currency_symbol}{formatted}"
            
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not format currency: {amount}")
            return f"{currency_symbol}0.00"
    
    @staticmethod
    def format_percentage(value: Union[float, int, Decimal],
                         decimal_places: int = 4,
                         multiply_by_100: bool = True) -> str:
        """Format number as percentage"""
        try:
            if value is None:
                return "0.0000%"
            
            decimal_value = Decimal(str(value))
            
            if multiply_by_100:
                decimal_value *= 100
            
            formatted = f"{decimal_value:.{decimal_places}f}"
            return f"{formatted}%"
            
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not format percentage: {value}")
            return "0.0000%"
    
    @staticmethod
    def format_basis_points(value: Union[float, int, Decimal],
                          decimal_places: int = 0) -> str:
        """Format number as basis points (multiply by 10,000)"""
        try:
            if value is None:
                return "0 bps"
            
            decimal_value = Decimal(str(value)) * 10000
            formatted = f"{decimal_value:.{decimal_places}f}"
            return f"{formatted} bps"
            
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not format basis points: {value}")
            return "0 bps"
    
    @staticmethod
    def format_millions(amount: Union[float, int, Decimal],
                       decimal_places: int = 2,
                       currency_symbol: str = "$") -> str:
        """Format large numbers in millions"""
        try:
            if amount is None:
                return f"{currency_symbol}0.00M"
            
            millions = Decimal(str(amount)) / 1_000_000
            formatted = f"{millions:.{decimal_places}f}"
            return f"{currency_symbol}{formatted}M"
            
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not format millions: {amount}")
            return f"{currency_symbol}0.00M"
    
    @staticmethod
    def format_number(value: Union[float, int, Decimal],
                     decimal_places: int = 2,
                     thousands_separator: bool = True) -> str:
        """Format number with specified decimal places"""
        try:
            if value is None:
                return "0.00"
            
            decimal_value = Decimal(str(value))
            
            if thousands_separator:
                return f"{decimal_value:,.{decimal_places}f}"
            else:
                return f"{decimal_value:.{decimal_places}f}"
                
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not format number: {value}")
            return "0.00"
    
    # Text Utilities
    @staticmethod
    def clean_string(text: str, remove_extra_spaces: bool = True) -> str:
        """Clean and normalize string"""
        if text is None:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        # Remove leading/trailing whitespace
        cleaned = text.strip()
        
        # Remove extra spaces
        if remove_extra_spaces:
            cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    @staticmethod
    def truncate_string(text: str, max_length: int, 
                       suffix: str = "...") -> str:
        """Truncate string to maximum length with suffix"""
        if text is None:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        if len(suffix) >= max_length:
            return text[:max_length]
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def pad_string(text: str, length: int, 
                  char: str = " ", align: str = "left") -> str:
        """Pad string to specified length"""
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) >= length:
            return text
        
        padding = char * (length - len(text))
        
        if align.lower() == "right":
            return padding + text
        elif align.lower() == "center":
            left_pad = len(padding) // 2
            right_pad = len(padding) - left_pad
            return char * left_pad + text + char * right_pad
        else:  # left
            return text + padding
    
    @staticmethod
    def camel_case_to_title(text: str) -> str:
        """Convert camelCase to Title Case"""
        if not isinstance(text, str):
            return ""
        
        # Insert spaces before uppercase letters but preserve consecutive capitals
        # First handle sequences of capitals followed by lowercase
        spaced = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
        # Then handle lowercase followed by uppercase
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', spaced)
        
        # Capitalize first letter if needed
        if spaced and spaced[0].islower():
            spaced = spaced[0].upper() + spaced[1:]
        
        return spaced
    
    @staticmethod
    def snake_case_to_title(text: str) -> str:
        """Convert snake_case to Title Case"""
        if not isinstance(text, str):
            return ""
        
        return text.replace('_', ' ').title()
    
    # Data Validation
    @staticmethod
    def validate_cusip(cusip: str) -> bool:
        """Validate CUSIP format and check digit"""
        if not isinstance(cusip, str):
            return False
        
        cusip = cusip.strip().upper()
        
        if len(cusip) != 9:
            return False
        
        if not re.match(r'^[0-9A-Z]{8}[0-9]$', cusip):
            return False
        
        # CUSIP check digit validation
        try:
            check_sum = 0
            for i, char in enumerate(cusip[:8]):
                if char.isdigit():
                    value = int(char)
                else:
                    # A=10, B=11, ..., Z=35
                    value = ord(char) - ord('A') + 10
                
                if i % 2 == 1:  # Odd positions (1-indexed)
                    value *= 2
                
                check_sum += value // 10 + value % 10
            
            check_digit = (10 - (check_sum % 10)) % 10
            return str(check_digit) == cusip[8]
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_isin(isin: str) -> bool:
        """Validate ISIN format and check digit"""
        if not isinstance(isin, str):
            return False
        
        isin = isin.strip().upper()
        
        if len(isin) != 12:
            return False
        
        if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin):
            return False
        
        # ISIN check digit validation using Luhn algorithm
        try:
            # Convert letters to numbers (A=10, B=11, etc.)
            numeric_string = ""
            for char in isin[:-1]:  # Exclude check digit
                if char.isdigit():
                    numeric_string += char
                else:
                    numeric_string += str(ord(char) - ord('A') + 10)
            
            # Apply Luhn algorithm
            check_sum = 0
            reverse_digits = numeric_string[::-1]
            
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:  # Every second digit from right
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                check_sum += n
            
            check_digit = (10 - (check_sum % 10)) % 10
            return str(check_digit) == isin[-1]
            
        except (ValueError, TypeError):
            return False
    
    # Array and List Utilities
    @staticmethod
    def join_non_empty(items: List[Any], separator: str = ", ") -> str:
        """Join list items, excluding None and empty strings"""
        if not items:
            return ""
        
        non_empty = [str(item) for item in items 
                    if item is not None and str(item).strip() != ""]
        
        return separator.join(non_empty)
    
    @staticmethod
    def split_and_clean(text: str, separator: str = ",") -> List[str]:
        """Split string and clean each part"""
        if not isinstance(text, str):
            return []
        
        parts = text.split(separator)
        return [StringUtils.clean_string(part) for part in parts 
                if StringUtils.clean_string(part)]
    
    # Date Formatting
    @staticmethod
    def format_date(date_value: Union[date, datetime.datetime, str],
                   format_string: str = "%Y-%m-%d") -> str:
        """Format date with fallback handling"""
        try:
            if date_value is None:
                return ""
            
            if isinstance(date_value, str):
                # Try to parse common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"]:
                    try:
                        parsed_date = datetime.datetime.strptime(date_value, fmt).date()
                        return parsed_date.strftime(format_string)
                    except ValueError:
                        continue
                return date_value  # Return original if can't parse
            
            elif isinstance(date_value, datetime.datetime):
                return date_value.strftime(format_string)
            
            elif isinstance(date_value, date):
                return date_value.strftime(format_string)
            
            else:
                return str(date_value)
                
        except (ValueError, TypeError, AttributeError):
            logger.debug(f"Could not format date: {date_value}")
            return str(date_value) if date_value is not None else ""
    
    # Excel Compatibility
    @staticmethod
    def to_excel_column(col_number: int) -> str:
        """Convert column number to Excel column letter(s)"""
        if col_number < 1:
            raise ValueError("Column number must be >= 1")
        
        result = ""
        while col_number > 0:
            col_number -= 1
            result = chr(col_number % 26 + ord('A')) + result
            col_number //= 26
        
        return result
    
    @staticmethod
    def from_excel_column(col_letters: str) -> int:
        """Convert Excel column letter(s) to number"""
        if not isinstance(col_letters, str):
            raise ValueError("Column letters must be a string")
        
        col_letters = col_letters.upper()
        result = 0
        
        for char in col_letters:
            if not 'A' <= char <= 'Z':
                raise ValueError(f"Invalid column letter: {char}")
            result = result * 26 + (ord(char) - ord('A') + 1)
        
        return result
    
    # Data Type Conversion
    @staticmethod
    def safe_convert(value: Any, target_type: type, default: Any = None):
        """Safely convert value to target type with default fallback"""
        if value is None:
            return default
        
        try:
            if target_type == str:
                return str(value)
            elif target_type == int:
                if isinstance(value, str):
                    cleaned = value.replace(',', '').strip()
                    return int(float(cleaned))  # Handle "100.0" -> 100
                return int(value)
            elif target_type == float:
                if isinstance(value, str):
                    cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
                    return float(cleaned)
                return float(value)
            elif target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'y', 'on']
                return bool(value)
            elif target_type == Decimal:
                if isinstance(value, str):
                    cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
                    return Decimal(cleaned)
                return Decimal(str(value))
            else:
                return target_type(value)
        except (ValueError, TypeError, decimal.InvalidOperation):
            logger.debug(f"Could not convert {value} to {target_type.__name__}")
            return default


# Module-level convenience functions
def format_currency(amount: Union[float, int, Decimal], currency_symbol: str = "$") -> str:
    """Convenience function for currency formatting"""
    return StringUtils.format_currency(amount, currency_symbol)

def format_percentage(value: Union[float, int, Decimal], decimal_places: int = 4) -> str:
    """Convenience function for percentage formatting"""
    return StringUtils.format_percentage(value, decimal_places)

def format_basis_points(value: Union[float, int, Decimal]) -> str:
    """Convenience function for basis points formatting"""
    return StringUtils.format_basis_points(value)

def is_numeric(value: str) -> bool:
    """Convenience function for numeric validation"""
    return StringUtils.is_numeric(value)

def parse_numeric(value: str, default: float = 0.0) -> float:
    """Convenience function for numeric parsing"""
    return StringUtils.parse_numeric(value, default)

def clean_string(text: str) -> str:
    """Convenience function for string cleaning"""
    return StringUtils.clean_string(text)

def validate_cusip(cusip: str) -> bool:
    """Convenience function for CUSIP validation"""
    return StringUtils.validate_cusip(cusip)