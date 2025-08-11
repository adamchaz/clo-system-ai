"""
Utility modules for the CLO Management System

This package provides essential utility functions for:
- Mathematical calculations and statistics
- Matrix operations and linear algebra
- Date and time handling for financial calculations
- Advanced financial computations (IRR, XIRR, spreads, etc.)
- String manipulation and formatting

All utilities are converted from the original VBA codebase with enhanced
functionality and Python best practices.
"""

from .math_utils import (
    MathUtils, 
    DayCount,
    min_array,
    max_array,
    average_array,
    std_array,
    median_array,
    year_frac
)

from .matrix_utils import (
    MatrixUtils,
    matrix_multiply,
    matrix_inverse,
    matrix_cholesky,
    matrix_sqrt,
    regularize_correlation_matrix
)

from .date_utils import (
    DateUtils,
    default_date_utils,
    is_business_day,
    next_business_day,
    previous_business_day,
    adjust_date,
    add_months,
    generate_payment_schedule,
    add_tenor
)

from .financial_utils import (
    FinancialUtils,
    xirr,
    irr,
    value_at_risk,
    sharpe_ratio
)

from .string_utils import (
    StringUtils,
    format_currency,
    format_percentage,
    format_basis_points,
    is_numeric,
    parse_numeric,
    clean_string,
    validate_cusip
)

__all__ = [
    # Math utilities
    'MathUtils',
    'DayCount',
    'min_array',
    'max_array',
    'average_array',
    'std_array',
    'median_array',
    'year_frac',
    
    # Matrix utilities
    'MatrixUtils',
    'matrix_multiply',
    'matrix_inverse',
    'matrix_cholesky',
    'matrix_sqrt',
    'regularize_correlation_matrix',
    
    # Date utilities
    'DateUtils',
    'default_date_utils',
    'is_business_day',
    'next_business_day',
    'previous_business_day',
    'adjust_date',
    'add_months',
    'generate_payment_schedule',
    'add_tenor',
    
    # Financial utilities
    'FinancialUtils',
    'xirr',
    'irr',
    'value_at_risk',
    'sharpe_ratio',
    
    # String utilities
    'StringUtils',
    'format_currency',
    'format_percentage',
    'format_basis_points',
    'is_numeric',
    'parse_numeric',
    'clean_string',
    'validate_cusip',
]

# Version information
__version__ = '1.0.0'
__author__ = 'CLO Management System'
__description__ = 'Utility modules for CLO financial calculations'
