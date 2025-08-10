"""
CLO Fee Management System
Converted from VBA Fees.cls - handles all fee types with complex accrual and payment logic
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
import numpy as np
from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .clo_deal import CLODeal
from .liability import DayCountConvention


class FeeType(str, Enum):
    """Fee calculation types"""
    BEGINNING = "BEGINNING"  # Based on beginning balance
    AVERAGE = "AVERAGE"      # Based on average balance
    FIXED = "FIXED"          # Fixed amount


class Fee(Base):
    """
    CLO Fee Model - converted from VBA Fees.cls
    Handles management fees, trustee fees, and incentive fees with complex calculation logic
    """
    __tablename__ = 'fees'
    
    fee_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    fee_name = Column(String(100), nullable=False)  # "Management Fee", "Trustee Fee", etc.
    
    # Fee Configuration
    fee_type = Column(String(20), nullable=False)  # BEGINNING, AVERAGE, FIXED
    fee_percentage = Column(Numeric(10,6), default=0)  # Annual rate (e.g., 0.005 = 0.5%)
    fixed_amount = Column(Numeric(18,2), default=0)  # Fixed component
    day_count_convention = Column(String(10), nullable=False)  # Day count method
    
    # Interest on Fee Configuration
    interest_on_fee = Column(Boolean, default=False)
    interest_spread = Column(Numeric(10,6), default=0)  # Spread for interest calculation
    initial_unpaid_fee = Column(Numeric(18,2), default=0)  # Starting unpaid balance
    
    # Deal Configuration
    num_periods = Column(Integer, nullable=False)
    beginning_fee_basis = Column(Numeric(18,2), default=0)  # Initial basis amount
    
    # Current State
    current_period = Column(Integer, default=1)
    last_calculated_period = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="fees")
    fee_calculations = relationship("FeeCalculation", back_populates="fee", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Fee({self.deal_id}:{self.fee_name}, Type={self.fee_type})>"


class FeeCalculation(Base):
    """
    Individual period fee calculations
    Stores detailed calculation results for each payment period
    """
    __tablename__ = 'fee_calculations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fee_id = Column(Integer, ForeignKey('fees.fee_id'), nullable=False)
    period_number = Column(Integer, nullable=False)
    
    # Period Definition
    begin_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    day_count_fraction = Column(Numeric(10,8))  # Calculated day count fraction
    
    # Fee Basis Calculations
    beginning_fee_basis = Column(Numeric(18,2), default=0)  # Balance at start
    ending_fee_basis = Column(Numeric(18,2), default=0)     # Balance at end
    calculated_fee_basis = Column(Numeric(18,2), default=0)  # Basis used for calculation
    
    # Interest Rate Information
    libor_rate = Column(Numeric(10,6), default=0)  # Period LIBOR/SOFR rate
    
    # Fee Calculation Results
    base_fee_accrued = Column(Numeric(18,2), default=0)      # Base fee amount
    interest_on_unpaid_fee = Column(Numeric(18,2), default=0) # Interest on deferred fees
    total_fee_accrued = Column(Numeric(18,2), default=0)     # Total accrued fee
    
    # Payment Tracking
    beginning_unpaid_balance = Column(Numeric(18,2), default=0)
    fee_paid = Column(Numeric(18,2), default=0)
    ending_unpaid_balance = Column(Numeric(18,2), default=0)
    
    # Metadata
    calculation_timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    fee = relationship("Fee", back_populates="fee_calculations")
    
    def __repr__(self):
        return f"<FeeCalculation(Fee={self.fee_id}, Period={self.period_number}, Accrued={self.total_fee_accrued})>"


class FeeCalculator:
    """
    Fee calculation engine - complete VBA Fees.cls conversion
    Handles all fee types with period-by-period tracking and rollforward logic
    """
    
    def __init__(self, fee_config: Fee):
        """
        Initialize fee calculator with configuration
        
        Args:
            fee_config: Fee model with configuration parameters
        """
        self.fee_name = fee_config.fee_name
        self.fee_type = FeeType(fee_config.fee_type)
        self.fee_percentage = Decimal(str(fee_config.fee_percentage))
        self.fixed_amount = Decimal(str(fee_config.fixed_amount))
        self.day_count_convention = DayCountConvention(fee_config.day_count_convention)
        self.interest_on_fee = fee_config.interest_on_fee
        self.interest_spread = Decimal(str(fee_config.interest_spread))
        self.initial_unpaid_fee = Decimal(str(fee_config.initial_unpaid_fee))
        
        # Initialize arrays for period-by-period tracking
        self.num_periods = fee_config.num_periods
        self.fee_basis: List[Optional[Decimal]] = [None] * (self.num_periods + 1)
        self.beginning_balance: List[Decimal] = [Decimal('0')] * (self.num_periods + 1)
        self.fee_accrued: List[Decimal] = [Decimal('0')] * (self.num_periods + 1)
        self.fee_paid: List[Decimal] = [Decimal('0')] * (self.num_periods + 1)
        self.ending_balance: List[Decimal] = [Decimal('0')] * (self.num_periods + 1)
        
        # Current state
        self.current_period = 1
        self.last_calculated_period = 0
        self.beginning_fee_basis = Decimal(str(fee_config.beginning_fee_basis))
        self.ending_fee_basis = Decimal('0')
        
        # Initialize first period
        self.beginning_balance[1] = self.initial_unpaid_fee
    
    def setup_deal(self, num_periods: int, beginning_basis: Decimal) -> None:
        """
        Setup fee calculator for deal processing
        
        Args:
            num_periods: Total number of payment periods
            beginning_basis: Initial fee basis amount
        """
        self.num_periods = num_periods
        self.beginning_fee_basis = beginning_basis
        
        # Reinitialize arrays with correct size
        self.fee_basis = [None] * (num_periods + 1)
        self.beginning_balance = [Decimal('0')] * (num_periods + 1)
        self.fee_accrued = [Decimal('0')] * (num_periods + 1)
        self.fee_paid = [Decimal('0')] * (num_periods + 1)
        self.ending_balance = [Decimal('0')] * (num_periods + 1)
        
        self.beginning_balance[1] = self.initial_unpaid_fee
        self.current_period = 1
    
    def calculate_fee(self, begin_date: date, end_date: date, 
                     ending_fee_basis: Decimal, libor_rate: Decimal = Decimal('0')) -> Decimal:
        """
        Calculate fee for current period - complete VBA Calc() conversion
        
        Args:
            begin_date: Period start date
            end_date: Period end date
            ending_fee_basis: Fee basis at period end
            libor_rate: Period LIBOR/SOFR rate
            
        Returns:
            Total fee accrued for the period
        """
        if ending_fee_basis <= 0:
            return Decimal('0')
        
        self.ending_fee_basis = ending_fee_basis
        
        # Calculate day count fraction
        day_count_fraction = self._calculate_day_count_fraction(begin_date, end_date)
        
        # Calculate base fee based on fee type
        if self.fee_type == FeeType.BEGINNING:
            if self.fee_percentage > 0:
                self.fee_basis[self.current_period] = self.beginning_fee_basis
            base_fee = (self.beginning_fee_basis * self.fee_percentage + self.fixed_amount) * day_count_fraction
            
        elif self.fee_type == FeeType.AVERAGE:
            if self.fee_percentage > 0:
                self.fee_basis[self.current_period] = (self.beginning_fee_basis + self.ending_fee_basis) / 2
            average_basis = (self.beginning_fee_basis + self.ending_fee_basis) / 2
            base_fee = (average_basis * self.fee_percentage + self.fixed_amount) * day_count_fraction
            
        else:  # FIXED
            self.fee_basis[self.current_period] = self.fixed_amount
            base_fee = self.fixed_amount * day_count_fraction
        
        # Add interest on unpaid fees if applicable
        interest_on_unpaid = Decimal('0')
        if self.interest_on_fee:
            unpaid_balance = self.beginning_balance[self.current_period]
            interest_rate = libor_rate + self.interest_spread
            interest_on_unpaid = unpaid_balance * interest_rate * day_count_fraction
        
        # Total fee accrued
        total_fee_accrued = base_fee + interest_on_unpaid
        self.fee_accrued[self.current_period] = total_fee_accrued
        self.last_calculated_period = self.current_period
        
        return total_fee_accrued
    
    def pay_fee(self, amount: Decimal) -> Decimal:
        """
        Apply fee payment and return unused amount - complete VBA PayFee() conversion
        
        Args:
            amount: Payment amount to apply
            
        Returns:
            Unused payment amount after applying to fee
        """
        total_amount_due = (self.beginning_balance[self.current_period] + 
                           self.fee_accrued[self.current_period] - 
                           self.fee_paid[self.current_period])
        
        if amount >= total_amount_due:
            # Full payment - pay everything due
            self.fee_paid[self.current_period] += total_amount_due
            return amount - total_amount_due
        else:
            # Partial payment - pay what we can
            self.fee_paid[self.current_period] += amount
            return Decimal('0')
    
    def rollforward(self) -> None:
        """
        Rollforward to next period - complete VBA Rollfoward() conversion
        """
        # Calculate ending balance for current period
        self.ending_balance[self.current_period] = (
            self.beginning_balance[self.current_period] + 
            self.fee_accrued[self.current_period] - 
            self.fee_paid[self.current_period]
        )
        
        # Setup next period if within bounds
        if self.current_period + 1 <= self.num_periods:
            self.beginning_fee_basis = self.ending_fee_basis
            self.beginning_balance[self.current_period + 1] = self.ending_balance[self.current_period]
        
        self.current_period += 1
    
    def get_fee_accrued(self) -> Decimal:
        """Get fee accrued for current period"""
        return self.fee_accrued[self.current_period]
    
    def get_total_fee_paid(self) -> Decimal:
        """Get total fee paid across all periods - complete VBA FeePaid() conversion"""
        return sum(self.fee_paid[1:self.last_calculated_period + 1])
    
    def get_unpaid_balance(self) -> Decimal:
        """Get current unpaid fee balance"""
        if self.current_period <= self.num_periods:
            return (self.beginning_balance[self.current_period] + 
                   self.fee_accrued[self.current_period] - 
                   self.fee_paid[self.current_period])
        return Decimal('0')
    
    def get_output(self) -> List[Dict[str, Any]]:
        """
        Get complete fee calculation results - complete VBA Output() conversion
        
        Returns:
            List of period-by-period fee calculation results
        """
        output = []
        
        for period in range(1, self.last_calculated_period + 1):
            period_data = {
                'period': period,
                'fee_basis': float(self.fee_basis[period]) if self.fee_basis[period] else 0.0,
                'beginning_balance': float(self.beginning_balance[period]),
                'fee_accrued': float(self.fee_accrued[period]),
                'fee_paid': float(self.fee_paid[period]),
                'ending_balance': float(self.ending_balance[period])
            }
            output.append(period_data)
        
        return output
    
    def get_current_result(self) -> Dict[str, Any]:
        """Get current period calculation result"""
        return {
            'period': self.current_period,
            'fee_name': self.fee_name,
            'fee_type': self.fee_type.value,
            'fee_basis': float(self.fee_basis[self.current_period]) if self.fee_basis[self.current_period] else 0.0,
            'beginning_balance': float(self.beginning_balance[self.current_period]),
            'fee_accrued': float(self.fee_accrued[self.current_period]),
            'fee_paid': float(self.fee_paid[self.current_period]),
            'unpaid_balance': float(self.get_unpaid_balance()),
            'total_fee_paid': float(self.get_total_fee_paid())
        }
    
    def _calculate_day_count_fraction(self, begin_date: date, end_date: date) -> Decimal:
        """
        Calculate day count fraction based on convention
        
        Args:
            begin_date: Period start date
            end_date: Period end date
            
        Returns:
            Day count fraction for the period
        """
        # Convert dates for calculation
        start_date = datetime.combine(begin_date, datetime.min.time())
        end_date_dt = datetime.combine(end_date, datetime.min.time())
        
        if self.day_count_convention == DayCountConvention.ACT_360:
            # Actual days / 360
            days_diff = (end_date_dt - start_date).days
            return Decimal(str(days_diff)) / Decimal('360')
            
        elif self.day_count_convention == DayCountConvention.ACT_365:
            # Actual days / 365
            days_diff = (end_date_dt - start_date).days
            return Decimal(str(days_diff)) / Decimal('365')
            
        elif self.day_count_convention == DayCountConvention.THIRTY_360:
            # 30/360 calculation
            d1 = begin_date.day
            d2 = end_date.day
            m1 = begin_date.month
            m2 = end_date.month
            y1 = begin_date.year
            y2 = end_date.year
            
            # 30/360 adjustment rules
            if d1 == 31:
                d1 = 30
            if d2 == 31 and d1 >= 30:
                d2 = 30
                
            days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
            return Decimal(str(days)) / Decimal('360')
            
        else:  # ACT_ACT
            # Actual/Actual - simplified implementation
            days_diff = (end_date_dt - start_date).days
            year = begin_date.year
            
            # Check if leap year
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            year_days = 366 if is_leap else 365
            
            return Decimal(str(days_diff)) / Decimal(str(year_days))