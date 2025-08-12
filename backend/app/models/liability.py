"""
CLO Liability/Tranche Models
Converted from VBA Liability.cls - handles individual tranche modeling and payments
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


class DayCountConvention(str, Enum):
    """Day count conventions for interest calculations"""
    THIRTY_360 = "30/360"
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_ACT = "ACT/ACT"


class CouponType(str, Enum):
    """Coupon types for liability tranches"""
    FIXED = "FIXED"
    FLOATING = "FLOATING"


class Liability(Base):
    """
    CLO Liability/Tranche Model - converted from VBA Liability.cls
    Represents individual tranches with payment calculations and risk measures
    """
    __tablename__ = 'liabilities'
    
    liability_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    tranche_name = Column(String(50), nullable=False)  # A, B, C, D, E, Equity
    
    # Core Properties
    original_balance = Column(Numeric(18,2), nullable=False)
    current_balance = Column(Numeric(18,2), nullable=False)
    deferred_balance = Column(Numeric(18,2), default=0)  # PIK balance
    
    # Payment Terms
    is_pikable = Column(Boolean, default=False)
    is_equity_tranche = Column(Boolean, default=False)
    libor_spread = Column(Numeric(10,6))  # Spread over LIBOR/SOFR
    coupon_type = Column(String(10), default=CouponType.FLOATING.value)
    day_count_convention = Column(String(10), default=DayCountConvention.ACT_360.value)
    
    # Risk Measures - User Inputs
    input_price = Column(Numeric(8,6))  # Price as % of par
    input_discount_margin = Column(Numeric(8,6))  # Discount margin
    analysis_date = Column(Date)
    
    # Calculated Risk Measures
    calculated_yield = Column(Numeric(8,6))
    calculated_dm = Column(Numeric(8,6))
    calculated_price = Column(Numeric(8,6))
    weighted_average_life = Column(Numeric(6,4))
    macaulay_duration = Column(Numeric(6,4))
    modified_duration = Column(Numeric(6,4))
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="liabilities")
    cash_flows = relationship("LiabilityCashFlow", back_populates="liability", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Liability({self.deal_id}:{self.tranche_name}, Balance={self.current_balance})>"


class LiabilityCashFlow(Base):
    """
    Individual period cash flows for liability tranches
    Stores payment history and projections
    """
    __tablename__ = 'liability_cash_flows'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    liability_id = Column(Integer, ForeignKey('liabilities.liability_id'), nullable=False)
    period_number = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    
    # Period Balances
    beginning_balance = Column(Numeric(18,2), default=0)
    ending_balance = Column(Numeric(18,2), default=0)
    deferred_beginning_balance = Column(Numeric(18,2), default=0)  # PIK balance
    deferred_ending_balance = Column(Numeric(18,2), default=0)
    
    # Interest Calculations
    coupon_rate = Column(Numeric(10,6))  # Period coupon rate
    interest_accrued = Column(Numeric(18,2), default=0)
    interest_paid = Column(Numeric(18,2), default=0)
    deferred_interest_accrued = Column(Numeric(18,2), default=0)  # PIK interest
    deferred_interest_paid = Column(Numeric(18,2), default=0)
    
    # Principal Payments
    principal_paid = Column(Numeric(18,2), default=0)
    deferred_principal_paid = Column(Numeric(18,2), default=0)  # PIK principal
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    liability = relationship("Liability", back_populates="cash_flows")
    
    def __repr__(self):
        return f"<LiabilityCashFlow(Period {self.period_number}, Date={self.payment_date})>"


class LiabilityCalculator:
    """
    Cash flow calculation engine for liability tranches
    Converted from VBA Liability.cls methods
    """
    
    def __init__(self, liability: Liability, payment_dates: List[date]):
        self.liability = liability
        self.payment_dates = payment_dates
        self.current_period = 1
        self.last_calculated_period = 0
        
        # Initialize cash flow arrays
        self._initialize_cash_flows()
    
    def _initialize_cash_flows(self):
        """Initialize cash flow records for all payment periods"""
        for i, payment_date in enumerate(self.payment_dates):
            cash_flow = LiabilityCashFlow(
                liability_id=self.liability.liability_id,
                period_number=i + 1,
                payment_date=payment_date,
                beginning_balance=self.liability.current_balance if i == 0 else Decimal('0'),
                deferred_beginning_balance=self.liability.deferred_balance if i == 0 else Decimal('0')
            )
            self.liability.cash_flows.append(cash_flow)
    
    def calculate_period(self, period: int, libor_rate: Decimal, 
                        prev_payment_date: date, next_payment_date: date) -> None:
        """
        Calculate interest accrual for a specific period
        Equivalent to VBA Calc() method
        """
        if self.liability.is_equity_tranche:
            return
        
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return
        
        # Calculate coupon rate
        if self.liability.coupon_type == CouponType.FIXED.value:
            coupon_rate = self.liability.libor_spread or Decimal('0')
        else:
            coupon_rate = (libor_rate or Decimal('0')) + (self.liability.libor_spread or Decimal('0'))
        
        cash_flow.coupon_rate = coupon_rate
        
        # Calculate date fraction
        day_fraction = self._calculate_date_fraction(
            prev_payment_date, next_payment_date, 
            DayCountConvention(self.liability.day_count_convention)
        )
        
        # Calculate interest accrual
        cash_flow.interest_accrued = cash_flow.beginning_balance * day_fraction * coupon_rate
        
        # Calculate PIK interest if applicable
        if self.liability.is_pikable:
            # Ensure deferred_beginning_balance is not None
            deferred_balance = cash_flow.deferred_beginning_balance or Decimal('0')
            cash_flow.deferred_interest_accrued = (
                deferred_balance * day_fraction * coupon_rate
            )
        
        # Track calculation progress
        if cash_flow.beginning_balance > 0:
            self.last_calculated_period = period
    
    def pay_interest(self, period: int, amount: Decimal) -> Decimal:
        """
        Apply interest payment and return remaining amount
        Equivalent to VBA PayInterest() method
        """
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return amount
        
        if self.liability.is_equity_tranche:
            # Equity receives all available amount
            cash_flow.interest_paid = (cash_flow.interest_paid or Decimal('0')) + amount
            self.last_calculated_period = period
            return Decimal('0')
        
        # Pay current interest first
        current_interest_due = (cash_flow.interest_accrued or Decimal('0')) - (cash_flow.interest_paid or Decimal('0'))
        if amount >= current_interest_due:
            cash_flow.interest_paid = (cash_flow.interest_paid or Decimal('0')) + current_interest_due
            amount -= current_interest_due
        else:
            cash_flow.interest_paid = (cash_flow.interest_paid or Decimal('0')) + amount
            return Decimal('0')
        
        # Pay deferred interest if PIK-able
        if self.liability.is_pikable and amount > 0:
            deferred_interest_due = (
                (cash_flow.deferred_interest_accrued or Decimal('0')) - 
                (cash_flow.deferred_interest_paid or Decimal('0'))
            )
            if amount >= deferred_interest_due:
                cash_flow.deferred_interest_paid = (
                    (cash_flow.deferred_interest_paid or Decimal('0')) + deferred_interest_due
                )
                amount -= deferred_interest_due
            else:
                cash_flow.deferred_interest_paid = (
                    (cash_flow.deferred_interest_paid or Decimal('0')) + amount
                )
                amount = Decimal('0')
        
        return amount
    
    def pay_principal(self, period: int, amount: Decimal) -> Decimal:
        """
        Apply principal payment and return remaining amount
        Equivalent to VBA PayPrincipal() method
        """
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return amount
        
        if self.liability.is_equity_tranche:
            # Equity receives all available amount
            cash_flow.principal_paid = (cash_flow.principal_paid or Decimal('0')) + amount
            self.last_calculated_period = period
            return Decimal('0')
        
        # Calculate principal due
        principal_due = (cash_flow.beginning_balance or Decimal('0')) - (cash_flow.principal_paid or Decimal('0'))
        
        if amount >= principal_due:
            cash_flow.principal_paid = (cash_flow.principal_paid or Decimal('0')) + principal_due
            amount -= principal_due
        else:
            cash_flow.principal_paid = (cash_flow.principal_paid or Decimal('0')) + amount
            amount = Decimal('0')
        
        return amount
    
    def pay_pik_interest(self, period: int, amount: Decimal) -> Decimal:
        """
        Pay down PIK balance (deferred interest converted to principal)
        Equivalent to VBA PayPIKInterest() method
        """
        if not self.liability.is_pikable:
            return amount
        
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return amount
        
        # Calculate total PIK balance due
        pik_balance_due = (
            (cash_flow.deferred_beginning_balance or Decimal('0')) -
            (cash_flow.deferred_principal_paid or Decimal('0')) +
            (cash_flow.deferred_interest_accrued or Decimal('0')) -
            (cash_flow.deferred_interest_paid or Decimal('0'))
        )
        
        if amount >= pik_balance_due:
            cash_flow.deferred_principal_paid = (
                (cash_flow.deferred_principal_paid or Decimal('0')) + pik_balance_due
            )
            amount -= pik_balance_due
        else:
            cash_flow.deferred_principal_paid = (
                (cash_flow.deferred_principal_paid or Decimal('0')) + amount
            )
            amount = Decimal('0')
        
        return amount
    
    def roll_forward(self, period: int) -> None:
        """
        Roll balances forward to next period
        Equivalent to VBA Rollfoward() method
        """
        current_cf = self._get_cash_flow(period)
        next_cf = self._get_cash_flow(period + 1)
        
        if not current_cf:
            return
        
        if not self.liability.is_equity_tranche:
            # Calculate ending balances
            current_cf.ending_balance = (
                (current_cf.beginning_balance or Decimal('0')) -
                (current_cf.principal_paid or Decimal('0'))
            )
            
            current_cf.deferred_ending_balance = (
                (current_cf.deferred_beginning_balance or Decimal('0')) +
                (current_cf.deferred_interest_accrued or Decimal('0')) -
                (current_cf.deferred_interest_paid or Decimal('0')) -
                (current_cf.deferred_principal_paid or Decimal('0'))
            )
            
            # Roll to next period
            if next_cf:
                next_cf.beginning_balance = current_cf.ending_balance
                next_cf.deferred_beginning_balance = (
                    current_cf.deferred_ending_balance +
                    (current_cf.interest_accrued or Decimal('0')) -
                    (current_cf.interest_paid or Decimal('0'))
                )
        else:
            # Equity tranche - maintain constant balance
            if next_cf:
                next_cf.beginning_balance = current_cf.beginning_balance
        
        self.current_period += 1
    
    def calculate_risk_measures(self, yield_curve, analysis_date: date) -> Dict[str, Decimal]:
        """
        Calculate risk measures (yield, duration, WAL)
        Equivalent to VBA CalcRiskMeasures() method
        """
        if not self.liability.current_balance or self.liability.current_balance <= 0:
            return {}
        
        # Prepare cash flow arrays
        total_cash_flows = []
        payment_dates = []
        discount_rates = []
        
        total_principal_paid = Decimal('0')
        weighted_principal = Decimal('0')
        
        for i in range(1, self.last_calculated_period + 1):
            cash_flow = self._get_cash_flow(i)
            if not cash_flow:
                continue
            
            # Total cash flow for period
            total_cf = (
                (cash_flow.interest_paid or Decimal('0')) +
                (cash_flow.principal_paid or Decimal('0')) +
                (cash_flow.deferred_interest_paid or Decimal('0')) +
                (cash_flow.deferred_principal_paid or Decimal('0'))
            )
            
            total_cash_flows.append(float(total_cf))
            payment_dates.append(cash_flow.payment_date)
            
            # Get discount rate from yield curve
            discount_rate = yield_curve.zero_rate(analysis_date, cash_flow.payment_date)
            discount_rates.append(float(discount_rate))
            
            # WAL calculation
            days_to_payment = (cash_flow.payment_date - analysis_date).days
            weighted_principal += days_to_payment * (cash_flow.principal_paid or Decimal('0'))
            total_principal_paid += (cash_flow.principal_paid or Decimal('0'))
        
        # Calculate metrics using financial math functions
        current_price = self.liability.input_price or Decimal('1.0')
        discount_margin = self.liability.input_discount_margin or Decimal('0')
        
        # Price calculation with discount margin
        calculated_price = self._calculate_present_value(
            total_cash_flows, payment_dates, discount_rates, 
            analysis_date, discount_margin
        )
        calculated_price /= float(self.liability.current_balance)
        
        # Yield calculation
        calculated_yield = self._calculate_yield(
            float(current_price * self.liability.current_balance),
            total_cash_flows, payment_dates
        )
        
        # WAL calculation
        remaining_balance = self.liability.current_balance - total_principal_paid
        final_payment_days = (payment_dates[-1] - analysis_date).days if payment_dates else 0
        weighted_principal += remaining_balance * final_payment_days
        weighted_average_life = weighted_principal / self.liability.original_balance / Decimal('365')
        
        # Duration calculations
        macaulay_duration = self._calculate_macaulay_duration(
            total_cash_flows, payment_dates, analysis_date, calculated_yield
        )
        
        modified_duration = macaulay_duration / (1 + calculated_yield / 4) if calculated_yield > 0 else Decimal('0')
        
        return {
            'calculated_yield': Decimal(str(calculated_yield)),
            'calculated_price': Decimal(str(calculated_price)),
            'weighted_average_life': weighted_average_life,
            'macaulay_duration': Decimal(str(macaulay_duration)),
            'modified_duration': Decimal(str(modified_duration))
        }
    
    def get_current_balance(self, period: int) -> Decimal:
        """Get current balance including PIK balance"""
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return Decimal('0')
        
        current_balance = cash_flow.beginning_balance or Decimal('0')
        
        if self.liability.is_pikable:
            pik_balance = (cash_flow.deferred_beginning_balance or Decimal('0')) - (cash_flow.deferred_principal_paid or Decimal('0'))
            current_balance += pik_balance
        
        return current_balance
    
    def get_interest_due(self, period: int) -> Decimal:
        """Get total interest due for period"""
        cash_flow = self._get_cash_flow(period)
        if not cash_flow:
            return Decimal('0')
        
        interest_due = (cash_flow.interest_accrued or Decimal('0')) - (cash_flow.interest_paid or Decimal('0'))
        
        if self.liability.is_pikable:
            deferred_interest_due = (
                (cash_flow.deferred_interest_accrued or Decimal('0')) -
                (cash_flow.deferred_interest_paid or Decimal('0'))
            )
            interest_due += deferred_interest_due
        
        return interest_due
    
    def get_current_distribution_percentage(self, period: int) -> Decimal:
        """Get current period distribution as percentage of original balance"""
        cash_flow = self._get_cash_flow(period)
        if not cash_flow or not self.liability.original_balance:
            return Decimal('0')
        
        total_distribution = (
            (cash_flow.principal_paid or Decimal('0')) +
            (cash_flow.interest_paid or Decimal('0'))
        )
        
        return total_distribution / self.liability.original_balance
    
    def _get_cash_flow(self, period: int) -> Optional[LiabilityCashFlow]:
        """Get cash flow record for specific period"""
        for cf in self.liability.cash_flows:
            if cf.period_number == period:
                return cf
        return None
    
    def _calculate_date_fraction(self, start_date: date, end_date: date, 
                               convention: DayCountConvention) -> Decimal:
        """Calculate date fraction based on day count convention"""
        days = (end_date - start_date).days
        
        if convention == DayCountConvention.THIRTY_360:
            return Decimal(str(days)) / Decimal('360')
        elif convention == DayCountConvention.ACT_360:
            return Decimal(str(days)) / Decimal('360')
        elif convention == DayCountConvention.ACT_365:
            return Decimal(str(days)) / Decimal('365')
        elif convention == DayCountConvention.ACT_ACT:
            # Simplified - should use actual year length
            return Decimal(str(days)) / Decimal('365.25')
        
        return Decimal(str(days)) / Decimal('360')  # Default
    
    def _calculate_present_value(self, cash_flows: List[float], dates: List[date], 
                               rates: List[float], analysis_date: date, 
                               spread: Decimal) -> float:
        """Calculate present value with spread adjustment"""
        pv = 0.0
        
        for cf, payment_date, rate in zip(cash_flows, dates, rates):
            years = (payment_date - analysis_date).days / 365.25
            discount_rate = rate + float(spread)
            discount_factor = (1 + discount_rate / 4) ** (years * 4)
            pv += cf / discount_factor
        
        return pv
    
    def _calculate_yield(self, price: float, cash_flows: List[float], 
                        dates: List[date]) -> float:
        """Calculate yield to maturity using Newton-Raphson method"""
        # Simplified yield calculation - production would use more sophisticated method
        if not cash_flows or price <= 0:
            return 0.0
        
        # Initial guess
        total_cf = sum(cash_flows)
        if total_cf <= price:
            return 0.0
        
        # Simple approximation
        return (total_cf / price - 1) / (len(cash_flows) / 4)
    
    def _calculate_macaulay_duration(self, cash_flows: List[float], dates: List[date],
                                   analysis_date: date, yield_rate: float) -> float:
        """Calculate Macaulay duration"""
        if not cash_flows or yield_rate <= 0:
            return 0.0
        
        weighted_time = 0.0
        present_value = 0.0
        
        for cf, payment_date in zip(cash_flows, dates):
            years = (payment_date - analysis_date).days / 365.25
            discount_factor = (1 + yield_rate / 4) ** (years * 4)
            pv = cf / discount_factor
            
            weighted_time += years * pv
            present_value += pv
        
        return weighted_time / present_value if present_value > 0 else 0.0


def generate_output_report(liability: Liability, calculator: LiabilityCalculator) -> List[List[Any]]:
    """
    Generate formatted output report for liability
    Equivalent to VBA Output() method
    """
    if liability.is_equity_tranche:
        return _generate_equity_output(liability, calculator)
    else:
        return _generate_debt_output(liability, calculator)


def _generate_equity_output(liability: Liability, calculator: LiabilityCalculator) -> List[List[Any]]:
    """Generate output for equity tranche"""
    periods = max(calculator.last_calculated_period, 10)
    output = []
    
    # Header row
    output.append(["Period", "Beg Balance", "Prin Paid", "Int Paid", "Current Percent"])
    
    for period in range(1, periods + 1):
        cash_flow = calculator._get_cash_flow(period)
        if cash_flow:
            current_pct = calculator.get_current_distribution_percentage(period)
            output.append([
                period,
                float(cash_flow.beginning_balance or 0),
                float(cash_flow.principal_paid or 0),
                float(cash_flow.interest_paid or 0),
                f"{current_pct:.4%}"
            ])
    
    return output


def _generate_debt_output(liability: Liability, calculator: LiabilityCalculator) -> List[List[Any]]:
    """Generate output for debt tranche"""
    periods = max(calculator.last_calculated_period, 10)
    output = []
    
    # Header row
    headers = ["Period", "Coupon", "Beg Balance", "Int Accrued", "Int Paid", 
              "Prin Paid", "End Balance", "Def Beg Balance"]
    
    if liability.is_pikable:
        headers.extend(["Def Int Accrued", "Def Int Paid"])
    
    headers.extend(["Def Prin Paid", "Def End Balance"])
    output.append(headers)
    
    # Data rows
    for period in range(1, periods + 1):
        cash_flow = calculator._get_cash_flow(period)
        if cash_flow:
            row = [
                period,
                f"{cash_flow.coupon_rate:.5%}" if cash_flow.coupon_rate else "0.00000%",
                float(cash_flow.beginning_balance or 0),
                float(cash_flow.interest_accrued or 0),
                float(cash_flow.interest_paid or 0),
                float(cash_flow.principal_paid or 0),
                float(cash_flow.ending_balance or 0),
                float(cash_flow.deferred_beginning_balance or 0)
            ]
            
            if liability.is_pikable:
                row.extend([
                    float(cash_flow.deferred_interest_accrued or 0),
                    float(cash_flow.deferred_interest_paid or 0)
                ])
            
            row.extend([
                float(cash_flow.deferred_principal_paid or 0),
                float(cash_flow.deferred_ending_balance or 0)
            ])
            
            output.append(row)
    
    return output