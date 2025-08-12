"""
CLO System Custom Exceptions

This module defines custom exception classes for the CLO Management System.
"""


class CLOError(Exception):
    """Base exception class for CLO system errors."""
    pass


class CLOBusinessError(CLOError):
    """Exception raised for business logic errors in CLO operations."""
    pass


class CLOValidationError(CLOError):
    """Exception raised for validation errors in CLO operations."""
    pass


class CLOConfigurationError(CLOError):
    """Exception raised for configuration errors in CLO operations."""
    pass


class CLODataError(CLOError):
    """Exception raised for data-related errors in CLO operations."""
    pass


class CLOCalculationError(CLOError):
    """Exception raised for calculation errors in CLO operations."""
    pass