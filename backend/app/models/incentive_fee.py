"""
Incentive Fee System - VBA IncentiveFee.cls Conversion

This module provides a complete Python implementation of the VBA IncentiveFee.cls,
including hurdle rate calculations, IRR computation, and manager compensation logic.

Key Features:
- Complete VBA functional parity for IncentiveFee.cls (141 lines)
- IRR-based incentive fee calculations with hurdle rate thresholds
- Subordinated payment tracking and discounting
- Database persistence with comprehensive audit trail
- Excel XIRR function equivalent implementation
- Period-by-period fee calculation and rollforward logic
"""

import json
import math
import numpy as np
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dateutil.relativedelta import relativedelta

from sqlalchemy import Column, Integer, String, Date, DateTime, DECIMAL, Boolean, Text, ForeignKey, Index, text
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

from ..core.database import Base


class IncentiveFeeStructureModel(Base):
    """SQLAlchemy model for incentive fee structures"""
    __tablename__ = 'incentive_fee_structures'
    
    fee_structure_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), nullable=False)
    fee_structure_name = Column(String(100), nullable=False)
    hurdle_rate = Column(DECIMAL(precision=6, scale=4), nullable=False)
    incentive_fee_rate = Column(DECIMAL(precision=6, scale=4), nullable=False)
    closing_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('TRUE'))
    threshold_reached = Column(Boolean, nullable=False, server_default=text('FALSE'))
    cum_discounted_sub_payments = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    analysis_date = Column(Date, nullable=True)
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    description = Column(Text, nullable=True)
    
    # Relationships
    subordinated_payments = relationship("SubordinatedPaymentModel", back_populates="fee_structure", cascade="all, delete-orphan")
    calculations = relationship("IncentiveFeeCalculationModel", back_populates="fee_structure", cascade="all, delete-orphan")
    transactions = relationship("FeePaymentTransactionModel", back_populates="fee_structure", cascade="all, delete-orphan")
    irr_history = relationship("IRRCalculationHistoryModel", back_populates="fee_structure", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_incentive_fee_structures_deal_id', 'deal_id'),
        Index('ix_incentive_fee_structures_active', 'is_active'),
    )


class SubordinatedPaymentModel(Base):
    """SQLAlchemy model for subordinated payments"""
    __tablename__ = 'subordinated_payments'
    
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    fee_structure_id = Column(Integer, ForeignKey('incentive_fee_structures.fee_structure_id', ondelete='CASCADE'), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(DECIMAL(precision=18, scale=2), nullable=False)
    discounted_amount = Column(DECIMAL(precision=18, scale=2), nullable=True)
    days_from_closing = Column(Integer, nullable=True)
    discount_factor = Column(DECIMAL(precision=10, scale=8), nullable=True)
    is_historical = Column(Boolean, nullable=False, server_default=text('FALSE'))
    period_number = Column(Integer, nullable=True)
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    fee_structure = relationship("IncentiveFeeStructureModel", back_populates="subordinated_payments")
    
    __table_args__ = (
        Index('ix_subordinated_payments_fee_structure', 'fee_structure_id'),
        Index('ix_subordinated_payments_date', 'payment_date'),
        Index('ix_subordinated_payments_period', 'period_number'),
    )


class IncentiveFeeCalculationModel(Base):
    """SQLAlchemy model for incentive fee calculations"""
    __tablename__ = 'incentive_fee_calculations'
    
    calculation_id = Column(Integer, primary_key=True, autoincrement=True)
    fee_structure_id = Column(Integer, ForeignKey('incentive_fee_structures.fee_structure_id', ondelete='CASCADE'), nullable=False)
    period_number = Column(Integer, nullable=False)
    calculation_date = Column(Date, nullable=False)
    
    # VBA IncentiveFee.cls variables mapped
    current_threshold = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    threshold_reached = Column(Boolean, nullable=False, server_default=text('FALSE'))
    current_sub_payments = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    current_incentive_payments = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    fee_paid_period = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    cum_discounted_sub_payments = Column(DECIMAL(precision=18, scale=2), nullable=False, server_default=text('0'))
    period_irr = Column(DECIMAL(precision=8, scale=6), nullable=True)
    
    # Calculation metadata
    days_from_closing = Column(Integer, nullable=True)
    hurdle_rate_used = Column(DECIMAL(precision=6, scale=4), nullable=True)
    incentive_fee_rate_used = Column(DECIMAL(precision=6, scale=4), nullable=True)
    threshold_shortfall = Column(DECIMAL(precision=18, scale=2), nullable=True)
    
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    fee_structure = relationship("IncentiveFeeStructureModel", back_populates="calculations")
    transactions = relationship("FeePaymentTransactionModel", back_populates="calculation")
    
    __table_args__ = (
        Index('ix_incentive_fee_calculations_fee_structure', 'fee_structure_id'),
        Index('ix_incentive_fee_calculations_period', 'period_number'),
        Index('ix_incentive_fee_calculations_date', 'calculation_date'),
    )


class FeePaymentTransactionModel(Base):
    """SQLAlchemy model for fee payment transactions"""
    __tablename__ = 'fee_payment_transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    fee_structure_id = Column(Integer, ForeignKey('incentive_fee_structures.fee_structure_id', ondelete='CASCADE'), nullable=False)
    calculation_id = Column(Integer, ForeignKey('incentive_fee_calculations.calculation_id', ondelete='SET NULL'), nullable=True)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    base_amount = Column(DECIMAL(precision=18, scale=2), nullable=False)
    fee_amount = Column(DECIMAL(precision=18, scale=2), nullable=False)
    net_amount = Column(DECIMAL(precision=18, scale=2), nullable=False)
    fee_rate_applied = Column(DECIMAL(precision=6, scale=4), nullable=True)
    reference_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    fee_structure = relationship("IncentiveFeeStructureModel", back_populates="transactions")
    calculation = relationship("IncentiveFeeCalculationModel", back_populates="transactions")
    
    __table_args__ = (
        Index('ix_fee_payment_transactions_fee_structure', 'fee_structure_id'),
        Index('ix_fee_payment_transactions_date', 'transaction_date'),
        Index('ix_fee_payment_transactions_type', 'transaction_type'),
    )


class IRRCalculationHistoryModel(Base):
    """SQLAlchemy model for IRR calculation history"""
    __tablename__ = 'irr_calculation_history'
    
    irr_id = Column(Integer, primary_key=True, autoincrement=True)
    fee_structure_id = Column(Integer, ForeignKey('incentive_fee_structures.fee_structure_id', ondelete='CASCADE'), nullable=False)
    calculation_date = Column(Date, nullable=False)
    period_number = Column(Integer, nullable=False)
    irr_value = Column(DECIMAL(precision=8, scale=6), nullable=True)
    cash_flows_count = Column(Integer, nullable=True)
    calculation_method = Column(String(50), nullable=False, server_default=text("'XIRR'"))
    cash_flows_json = Column(Text, nullable=True)
    dates_json = Column(Text, nullable=True)
    calculation_successful = Column(Boolean, nullable=False, server_default=text('TRUE'))
    error_message = Column(Text, nullable=True)
    created_date = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    fee_structure = relationship("IncentiveFeeStructureModel", back_populates="irr_history")
    
    __table_args__ = (
        Index('ix_irr_calculation_history_fee_structure', 'fee_structure_id'),
        Index('ix_irr_calculation_history_date', 'calculation_date'),
        Index('ix_irr_calculation_history_period', 'period_number'),
    )


class IncentiveFee:
    """
    VBA IncentiveFee.cls Python Implementation
    
    Complete conversion of VBA IncentiveFee.cls (141 lines) with exact functional parity.
    Handles manager incentive fee calculations based on subordinated noteholder IRR hurdle rates.
    
    Key VBA Methods Implemented:
    - Setup(): Initialize fee structure and subordinated payment history
    - DealSetup(): Setup deal parameters and historical payment processing
    - Calc(): Calculate current period thresholds and fee eligibility
    - PaymentToSubNotholder(): Process subordinated payments and check threshold
    - PayIncentiveFee(): Calculate and apply incentive fees
    - Rollfoward(): Roll forward to next period with IRR calculation
    - Output(): Export results to VBA-equivalent 2D array
    
    VBA Variables Mapped:
    - clsFeeHurdleRate -> fee_hurdle_rate
    - clsIncentFee -> incentive_fee_rate
    - clsThresholdReach -> threshold_reached
    - clsSubPaymentsDict -> sub_payments_dict
    - clsClosingDate -> closing_date
    - clsCurrentThreshold -> current_threshold
    - clsCurrIncetivePayments -> current_incentive_payments
    - clsCurrSubPayments -> current_sub_payments
    - clsCurrDate -> current_date
    - clsPeriod -> period
    - clsCumDicountedSubPayments -> cum_discounted_sub_payments
    """
    
    def __init__(self, session: Session = None):
        """Initialize IncentiveFee with VBA-equivalent structure"""
        # VBA exact variable names (converted from Hungarian notation)
        self.fee_hurdle_rate: float = 0.0               # VBA: clsFeeHurdleRate
        self.incentive_fee_rate: float = 0.0            # VBA: clsIncentFee
        self.threshold_reached: bool = False            # VBA: clsThresholdReach
        self.sub_payments_dict: Dict[date, float] = {}  # VBA: clsSubPaymentsDict
        self.closing_date: Optional[date] = None        # VBA: clsClosingDate
        self.current_threshold: float = 0.0             # VBA: clsCurrentThreshold
        self.current_incentive_payments: float = 0.0    # VBA: clsCurrIncetivePayments (note VBA typo)
        self.current_sub_payments: float = 0.0          # VBA: clsCurrSubPayments
        self.current_date: Optional[date] = None        # VBA: clsCurrDate
        self.period: int = 1                            # VBA: clsPeriod
        self.cum_discounted_sub_payments: float = 0.0   # VBA: clsCumDicountedSubPayments (note VBA typo)
        
        # VBA arrays for data storage
        self.threshold: List[float] = []                # VBA: clsThreshold()
        self.irr: List[float] = []                     # VBA: clsIRR()
        self.fee_paid: List[float] = []                # VBA: clsFeePaid()
        
        # Enhanced attributes for database integration
        self.session = session
        self.fee_structure_id: Optional[int] = None
        self.deal_id: Optional[str] = None
        self.analysis_date: Optional[date] = None
        
        # Internal state
        self._is_setup: bool = False
        self._num_payments: int = 0
    
    def setup(self, i_fee_threshold: float, i_incentive_fee: float, 
              i_pay_to_sub_notholder: Dict[date, float]) -> None:
        """
        EXACT VBA Setup() method implementation
        
        VBA Signature: Public Sub Setup(iFeeThreshold As Double, iIncentiveFee As Double, 
                                        iPaytoSubNotholder As Dictionary)
        
        Sets up incentive fee structure with hurdle rate, fee rate, and payment history
        """
        # VBA: clsFeeHurdleRate = iFeeThreshold
        self.fee_hurdle_rate = i_fee_threshold
        
        # VBA: clsIncentFee = iIncentiveFee
        self.incentive_fee_rate = i_incentive_fee
        
        # VBA: Set clsSubPaymentsDict = iPaytoSubNotholder
        self.sub_payments_dict = dict(i_pay_to_sub_notholder)  # Create copy
        
        self._is_setup = True
    
    def deal_setup(self, i_num_of_payments: int, i_close_date: date, i_analysis_date: date) -> None:
        """
        EXACT VBA DealSetup() method implementation
        
        VBA Signature: Public Sub DealSetup(iNumofPayments As Long, iCloseDate As Date, ianalysisDate As Date)
        
        Sets up deal parameters and processes historical subordinated payments
        """
        if not self._is_setup:
            raise RuntimeError("IncentiveFee must be setup before calling deal_setup")
        
        # VBA: ReDim clsThreshold(iNumofPayments)
        # VBA: ReDim clsIRR(iNumofPayments)
        # VBA: ReDim clsFeePaid(iNumofPayments)
        self._num_payments = i_num_of_payments
        self.threshold = [0.0] * (i_num_of_payments + 1)  # VBA uses 1-based indexing
        self.irr = [0.0] * (i_num_of_payments + 1)
        self.fee_paid = [0.0] * (i_num_of_payments + 1)
        
        # VBA: clsPeriod = 1
        self.period = 1
        
        # VBA: clsClosingDate = iCloseDate
        self.closing_date = i_close_date
        self.analysis_date = i_analysis_date
        
        # VBA historical payment processing - exact implementation
        # VBA: For Each lDate In clsSubPaymentsDict.Keys
        #      If CDate(lDate) > ianalysisDate Then
        #          clsSubPaymentsDict.Remove lDate
        #      End If
        dates_to_remove = []
        for payment_date in self.sub_payments_dict.keys():
            if payment_date > i_analysis_date:
                dates_to_remove.append(payment_date)
        
        for date_to_remove in dates_to_remove:
            del self.sub_payments_dict[date_to_remove]
        
        # VBA cumulative discounted payments calculation - exact implementation
        # VBA: For Each lDate In clsSubPaymentsDict.Keys
        #      clsCumDicountedSubPayments = clsCumDicountedSubPayments + 
        #          (clsSubPaymentsDict(lDate) / ((1 + clsFeeHurdleRate) ^ ((lDate - clsClosingDate) / 365)))
        #      If clsCumDicountedSubPayments > 0 Then
        #         clsThresholdReach = True
        #         Exit For
        #      End If
        for payment_date, payment_amount in self.sub_payments_dict.items():
            days_diff = (payment_date - self.closing_date).days
            discount_factor = (1 + self.fee_hurdle_rate) ** (days_diff / 365.0)
            discounted_payment = payment_amount / discount_factor
            
            self.cum_discounted_sub_payments += discounted_payment
            
            # VBA: If clsCumDicountedSubPayments > 0 Then
            if self.cum_discounted_sub_payments > 0:
                # VBA: clsThresholdReach = True
                self.threshold_reached = True
                # VBA: Exit For
                break
    
    def calc(self, i_next_pay: date) -> None:
        """
        EXACT VBA Calc() method implementation
        
        VBA Signature: Public Sub Calc(iNextPay As Date)
        
        Calculates current period threshold and fee eligibility
        """
        # VBA: clsCurrDate = iNextPay
        self.current_date = i_next_pay
        
        # VBA threshold calculation logic - exact implementation
        # VBA: If clsThresholdReach Then
        if self.threshold_reached:
            # VBA: clsCurrentThreshold = 0
            self.current_threshold = 0.0
        else:
            # VBA: clsCurrentThreshold = clsCumDicountedSubPayments * (1 + clsFeeHurdleRate) ^ ((iNextPay - clsClosingDate) / 365)
            days_diff = (i_next_pay - self.closing_date).days
            growth_factor = (1 + self.fee_hurdle_rate) ** (days_diff / 365.0)
            self.current_threshold = self.cum_discounted_sub_payments * growth_factor
            
            # VBA: clsCurrentThreshold = -1 * clsCurrentThreshold
            self.current_threshold = -1 * self.current_threshold
        
        # VBA: clsThreshold(clsPeriod) = clsCurrentThreshold
        self.threshold[self.period] = self.current_threshold
    
    def incentive_fee_threshold(self) -> float:
        """
        EXACT VBA IncentiveFeeThreshold() method implementation
        
        VBA Signature: Public Function IncentiveFeeThreshold() As Double
        
        Returns the threshold amount needed to trigger incentive fees
        """
        # VBA: If clsThresholdReach Then
        if self.threshold_reached:
            # VBA: IncentiveFeeThreshold = 0
            return 0.0
        else:
            # VBA: IncentiveFeeThreshold = clsThreshold(clsPeriod) - clsCurrSubPayments
            return self.threshold[self.period] - self.current_sub_payments
    
    def payment_to_sub_notholder(self, i_amount: float) -> None:
        """
        EXACT VBA PaymentToSubNotholder() method implementation
        
        VBA Signature: Public Sub PaymentToSubNotholder(iAmount As Double)
        
        Records subordinated payment and checks if threshold is reached
        """
        # VBA: clsCurrSubPayments = clsCurrSubPayments + iAmount
        self.current_sub_payments += i_amount
        
        # VBA: If clsCurrSubPayments >= clsCurrentThreshold Then clsThresholdReach = True
        if self.current_sub_payments >= self.current_threshold:
            self.threshold_reached = True
    
    def pay_incentive_fee(self, i_amount: float) -> float:
        """
        EXACT VBA PayIncentiveFee() method implementation
        
        VBA Signature: Public Sub PayIncentiveFee(iAmount As Double)
        
        Calculates and applies incentive fee, returns net amount after fee
        Note: VBA modifies iAmount by reference, Python returns the modified amount
        """
        original_amount = i_amount
        
        # VBA: If clsThresholdReach Then
        if self.threshold_reached:
            # VBA: clsCurrIncetivePayments = clsCurrIncetivePayments + iAmount * clsIncentFee
            fee_amount = original_amount * self.incentive_fee_rate
            self.current_incentive_payments += fee_amount
            
            # VBA: iAmount = iAmount * (1 - clsIncentFee)
            net_amount = original_amount * (1 - self.incentive_fee_rate)
            return net_amount
        
        return original_amount
    
    def roll_forward(self) -> None:
        """
        EXACT VBA Rollfoward() method implementation (note VBA typo in method name)
        
        VBA Signature: Public Sub Rollfoward()
        
        Rolls forward to next period, calculates IRR, and resets current period variables
        """
        if not self.current_date:
            raise RuntimeError("Current date must be set before rolling forward")
        
        # VBA: clsThreshold(clsPeriod) = clsCurrentThreshold
        self.threshold[self.period] = self.current_threshold
        
        # VBA: clsFeePaid(clsPeriod) = clsCurrIncetivePayments
        self.fee_paid[self.period] = self.current_incentive_payments
        
        # VBA discounted payments update - exact implementation
        # VBA: clsCumDicountedSubPayments = clsCumDicountedSubPayments + 
        #      (clsCurrSubPayments / ((1 + clsFeeHurdleRate) ^ ((clsCurrDate - clsClosingDate) / 365)))
        days_diff = (self.current_date - self.closing_date).days
        discount_factor = (1 + self.fee_hurdle_rate) ** (days_diff / 365.0)
        discounted_current_payment = self.current_sub_payments / discount_factor
        self.cum_discounted_sub_payments += discounted_current_payment
        
        # VBA: clsSubPaymentsDict.Add clsCurrDate, clsCurrSubPayments
        self.sub_payments_dict[self.current_date] = self.current_sub_payments
        
        # VBA IRR calculation - exact Excel XIRR implementation
        # VBA: lDates = clsSubPaymentsDict.Keys
        # VBA: lValues = clsSubPaymentsDict.Items
        # VBA: For i = LBound(lDates) To UBound(lDates)
        #      lDates(i) = CDate(lDates(i))
        # VBA: lValue = Application.Xirr(lValues, lDates)
        dates = list(self.sub_payments_dict.keys())
        values = list(self.sub_payments_dict.values())
        
        # Sort by date to ensure proper IRR calculation
        sorted_data = sorted(zip(dates, values))
        sorted_dates = [item[0] for item in sorted_data]
        sorted_values = [item[1] for item in sorted_data]
        
        # Calculate IRR using XIRR equivalent
        irr_result = self._calculate_xirr(sorted_values, sorted_dates)
        
        # VBA: If VarType(lValue) = vbDouble Then
        #      clsIRR(clsPeriod) = CDbl(lValue)
        if irr_result is not None:
            self.irr[self.period] = irr_result
        
        # VBA: clsPeriod = clsPeriod + 1
        self.period += 1
        
        # VBA variable reset - exact implementation
        # VBA: clsCurrSubPayments = 0
        # VBA: clsCurrIncetivePayments = 0
        self.current_sub_payments = 0.0
        self.current_incentive_payments = 0.0
    
    def fee_paid_total(self) -> float:
        """
        EXACT VBA FeePaid() method implementation
        
        VBA Signature: Public Function FeePaid() As Double
        
        Returns cumulative fee paid across all periods
        """
        # VBA: Dim lTotal As Double
        # VBA: For i = LBound(clsFeePaid) To UBound(clsFeePaid)
        #      lTotal = lTotal + clsFeePaid(i)
        # VBA: FeePaid = lTotal
        l_total = 0.0
        for i in range(len(self.fee_paid)):
            l_total += self.fee_paid[i]
        
        return l_total
    
    def output(self) -> List[List[Any]]:
        """
        EXACT VBA Output() method implementation
        
        VBA Signature: Public Function Output() As Variant
        
        Returns 2D array with threshold, fee paid, and IRR data
        """
        # VBA: ReDim lOutput(0 To clsPeriod - 1, 2)
        l_output = []
        
        # VBA header row - exact implementation
        # VBA: lOutput(0, 0) = "Threshold"
        # VBA: lOutput(0, 1) = "Fee Paid"
        # VBA: lOutput(0, 2) = "IRR"
        header = ["Threshold", "Fee Paid", "IRR"]
        l_output.append(header)
        
        # VBA: For i = 1 To clsPeriod - 1
        for i in range(1, self.period):
            # VBA: lOutput(i, 0) = clsThreshold(i)
            # VBA: lOutput(i, 1) = clsFeePaid(i)
            # VBA: lOutput(i, 2) = Format(clsIRR(i), "0.000%")
            irr_formatted = f"{self.irr[i]:.3%}" if self.irr[i] != 0 else "0.000%"
            
            row = [self.threshold[i], self.fee_paid[i], irr_formatted]
            l_output.append(row)
        
        # VBA: Output = lOutput
        return l_output
    
    def _calculate_xirr(self, cash_flows: List[float], dates: List[date]) -> Optional[float]:
        """
        Calculate XIRR equivalent to Excel's Application.Xirr function
        
        Uses Newton-Raphson method to find the IRR that makes NPV = 0
        """
        if len(cash_flows) != len(dates) or len(cash_flows) < 2:
            return None
        
        # Need at least one positive and one negative cash flow
        has_positive = any(cf > 0 for cf in cash_flows)
        has_negative = any(cf < 0 for cf in cash_flows)
        if not (has_positive and has_negative):
            return None
        
        # Convert dates to days from first date
        base_date = dates[0]
        days_diff = [(d - base_date).days for d in dates]
        
        # Newton-Raphson iteration
        guess = 0.1  # 10% initial guess
        max_iterations = 100
        tolerance = 1e-10
        
        for iteration in range(max_iterations):
            # Calculate NPV and its derivative
            npv = 0.0
            npv_derivative = 0.0
            
            for i, (cf, days) in enumerate(zip(cash_flows, days_diff)):
                years = days / 365.25
                if years == 0:
                    npv += cf
                else:
                    factor = (1 + guess) ** years
                    npv += cf / factor
                    # Derivative: d/dx[cf/(1+x)^years] = -cf * years * (1+x)^(-years-1)
                    npv_derivative -= cf * years / (factor * (1 + guess))
            
            # Check convergence
            if abs(npv) < tolerance:
                return guess
            
            # Newton-Raphson update
            if abs(npv_derivative) < tolerance:
                break
            
            new_guess = guess - npv / npv_derivative
            
            # Ensure guess stays reasonable
            if new_guess < -0.99:  # Prevent rates below -99%
                new_guess = -0.99
            elif new_guess > 10:  # Prevent unreasonably high rates
                new_guess = 10.0
            
            if abs(new_guess - guess) < tolerance:
                return new_guess
            
            guess = new_guess
        
        return None  # Failed to converge
    
    def save_to_database(self, deal_id: str, fee_structure_name: str = "Default") -> int:
        """Save incentive fee structure to database"""
        if not self.session:
            raise RuntimeError("Database session required for persistence")
        
        if not self._is_setup:
            raise RuntimeError("IncentiveFee must be setup before saving")
        
        # Create fee structure record
        structure = IncentiveFeeStructureModel(
            deal_id=deal_id,
            fee_structure_name=fee_structure_name,
            hurdle_rate=Decimal(str(self.fee_hurdle_rate)),
            incentive_fee_rate=Decimal(str(self.incentive_fee_rate)),
            closing_date=self.closing_date,
            threshold_reached=self.threshold_reached,
            cum_discounted_sub_payments=Decimal(str(self.cum_discounted_sub_payments)),
            analysis_date=self.analysis_date
        )
        
        self.session.add(structure)
        self.session.flush()
        self.fee_structure_id = structure.fee_structure_id
        
        # Save subordinated payments
        for payment_date, payment_amount in self.sub_payments_dict.items():
            days_diff = (payment_date - self.closing_date).days
            discount_factor = (1 + self.fee_hurdle_rate) ** (days_diff / 365.0)
            discounted_amount = payment_amount / discount_factor
            
            payment_record = SubordinatedPaymentModel(
                fee_structure_id=structure.fee_structure_id,
                payment_date=payment_date,
                payment_amount=Decimal(str(payment_amount)),
                discounted_amount=Decimal(str(discounted_amount)),
                days_from_closing=days_diff,
                discount_factor=Decimal(str(discount_factor)),
                is_historical=payment_date <= self.analysis_date if self.analysis_date else True
            )
            self.session.add(payment_record)
        
        # Save calculations for completed periods
        for i in range(1, self.period):
            if i < len(self.threshold):
                calc_record = IncentiveFeeCalculationModel(
                    fee_structure_id=structure.fee_structure_id,
                    period_number=i,
                    calculation_date=self.current_date or self.analysis_date or date.today(),
                    current_threshold=Decimal(str(self.threshold[i])),
                    threshold_reached=self.threshold_reached,
                    fee_paid_period=Decimal(str(self.fee_paid[i])),
                    cum_discounted_sub_payments=Decimal(str(self.cum_discounted_sub_payments)),
                    period_irr=Decimal(str(self.irr[i])) if self.irr[i] != 0 else None,
                    hurdle_rate_used=Decimal(str(self.fee_hurdle_rate)),
                    incentive_fee_rate_used=Decimal(str(self.incentive_fee_rate))
                )
                self.session.add(calc_record)
        
        self.session.commit()
        return structure.fee_structure_id
    
    def get_fee_summary(self) -> Dict[str, Any]:
        """Get comprehensive fee calculation summary"""
        return {
            'fee_structure_id': self.fee_structure_id,
            'deal_id': self.deal_id,
            'hurdle_rate': self.fee_hurdle_rate,
            'incentive_fee_rate': self.incentive_fee_rate,
            'threshold_reached': self.threshold_reached,
            'current_period': self.period,
            'total_fee_paid': self.fee_paid_total(),
            'cum_discounted_sub_payments': self.cum_discounted_sub_payments,
            'current_threshold': self.current_threshold,
            'periods': [
                {
                    'period': i,
                    'threshold': self.threshold[i] if i < len(self.threshold) else 0,
                    'fee_paid': self.fee_paid[i] if i < len(self.fee_paid) else 0,
                    'irr': self.irr[i] if i < len(self.irr) else 0,
                    'irr_formatted': f"{self.irr[i]:.3%}" if i < len(self.irr) and self.irr[i] != 0 else "0.000%"
                }
                for i in range(1, self.period)
            ]
        }


class IncentiveFeeService:
    """Service class for incentive fee operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_incentive_fee_structure(self, deal_id: str, fee_structure_name: str,
                                     hurdle_rate: float, incentive_fee_rate: float,
                                     closing_date: date, historical_payments: Dict[date, float] = None,
                                     analysis_date: date = None) -> IncentiveFee:
        """Create and setup incentive fee structure"""
        incentive_fee = IncentiveFee(self.session)
        
        # Setup with parameters
        payments_dict = historical_payments or {}
        incentive_fee.setup(hurdle_rate, incentive_fee_rate, payments_dict)
        
        # Deal setup
        num_payments = 50  # Default number of periods
        analysis_date = analysis_date or date.today()
        incentive_fee.deal_setup(num_payments, closing_date, analysis_date)
        
        # Save to database
        structure_id = incentive_fee.save_to_database(deal_id, fee_structure_name)
        
        return incentive_fee
    
    def load_incentive_fee_structure(self, fee_structure_id: int) -> Optional[IncentiveFee]:
        """Load incentive fee structure from database"""
        structure = self.session.query(IncentiveFeeStructureModel).filter_by(
            fee_structure_id=fee_structure_id, is_active=True
        ).first()
        
        if not structure:
            return None
        
        # Load subordinated payments
        payments_dict = {}
        for payment in structure.subordinated_payments:
            payments_dict[payment.payment_date] = float(payment.payment_amount)
        
        # Create and setup incentive fee
        incentive_fee = IncentiveFee(self.session)
        incentive_fee.setup(float(structure.hurdle_rate), float(structure.incentive_fee_rate), payments_dict)
        incentive_fee.deal_setup(50, structure.closing_date, structure.analysis_date or date.today())
        
        # Restore state from database
        incentive_fee.fee_structure_id = structure.fee_structure_id
        incentive_fee.deal_id = structure.deal_id
        incentive_fee.threshold_reached = structure.threshold_reached
        incentive_fee.cum_discounted_sub_payments = float(structure.cum_discounted_sub_payments)
        
        # Load calculation history
        calculations = self.session.query(IncentiveFeeCalculationModel).filter_by(
            fee_structure_id=fee_structure_id
        ).order_by(IncentiveFeeCalculationModel.period_number).all()
        
        for calc in calculations:
            period = calc.period_number
            if period < len(incentive_fee.threshold):
                incentive_fee.threshold[period] = float(calc.current_threshold)
                incentive_fee.fee_paid[period] = float(calc.fee_paid_period)
                incentive_fee.irr[period] = float(calc.period_irr) if calc.period_irr else 0.0
        
        return incentive_fee
    
    def get_fee_structures_for_deal(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get all fee structures for a deal"""
        structures = self.session.query(IncentiveFeeStructureModel).filter_by(
            deal_id=deal_id, is_active=True
        ).order_by(IncentiveFeeStructureModel.created_date).all()
        
        return [{
            'fee_structure_id': s.fee_structure_id,
            'fee_structure_name': s.fee_structure_name,
            'hurdle_rate': float(s.hurdle_rate),
            'incentive_fee_rate': float(s.incentive_fee_rate),
            'closing_date': s.closing_date,
            'threshold_reached': s.threshold_reached,
            'total_subordinated_payments': sum(float(p.payment_amount) for p in s.subordinated_payments),
            'total_fees_paid': sum(float(c.fee_paid_period) for c in s.calculations),
            'description': s.description
        } for s in structures]
    
    def calculate_period_fee(self, fee_structure_id: int, calculation_date: date,
                           subordinated_payment: float, fee_payment_amount: float) -> Dict[str, Any]:
        """Calculate fees for a specific period"""
        incentive_fee = self.load_incentive_fee_structure(fee_structure_id)
        if not incentive_fee:
            raise ValueError(f"Fee structure {fee_structure_id} not found")
        
        # Calculate for the period
        incentive_fee.calc(calculation_date)
        
        # Process subordinated payment
        if subordinated_payment > 0:
            incentive_fee.payment_to_sub_notholder(subordinated_payment)
        
        # Calculate incentive fee
        net_amount = fee_payment_amount
        fee_amount = 0.0
        
        if fee_payment_amount > 0:
            net_amount = incentive_fee.pay_incentive_fee(fee_payment_amount)
            fee_amount = fee_payment_amount - net_amount
        
        # Get threshold information
        threshold_shortfall = incentive_fee.incentive_fee_threshold()
        
        # Roll forward
        incentive_fee.roll_forward()
        
        # Save updated state
        incentive_fee.save_to_database(incentive_fee.deal_id, "Updated")
        
        return {
            'period': incentive_fee.period - 1,  # Period was incremented in roll_forward
            'calculation_date': calculation_date,
            'subordinated_payment': subordinated_payment,
            'fee_payment_base_amount': fee_payment_amount,
            'fee_amount': fee_amount,
            'net_amount': net_amount,
            'threshold_reached': incentive_fee.threshold_reached,
            'threshold_shortfall': threshold_shortfall,
            'current_threshold': incentive_fee.threshold[incentive_fee.period - 1],
            'period_irr': incentive_fee.irr[incentive_fee.period - 1],
            'total_fees_paid': incentive_fee.fee_paid_total()
        }