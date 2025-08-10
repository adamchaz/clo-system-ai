"""
ICTrigger Model - Python conversion of ICTrigger.cls VBA class
Handles Interest Coverage trigger calculations and cure mechanisms
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from ..core.database import Base


class ICTriggerResult:
    """Result object for IC trigger calculations"""
    
    def __init__(self):
        self.numerator: Decimal = Decimal('0')          # Interest collections
        self.denominator: Decimal = Decimal('0')        # Interest due  
        self.liability_balance: Decimal = Decimal('0')  # For cure calculations
        self.calculated_ratio: Decimal = Decimal('0')
        self.threshold: Decimal = Decimal('0')
        self.pass_fail: bool = True
        self.cure_amount: Decimal = Decimal('0')
        self.prior_cure_payments: Decimal = Decimal('0')
        self.cure_amount_paid: Decimal = Decimal('0')


class ICTrigger(Base):
    """
    ICTrigger Model - Interest Coverage trigger tracking
    Converted from VBA ICTrigger.cls (144 lines) with enhanced functionality
    """
    __tablename__ = 'ic_triggers'
    
    # Primary Key
    trigger_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys  
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    tranche_name = Column(String(50), nullable=False)
    
    # Trigger Configuration
    trigger_name = Column(String(100), nullable=False)
    ic_threshold = Column(Numeric(8,6), nullable=False)  # e.g., 1.10 = 110%
    
    # Period Tracking
    period_number = Column(Integer, nullable=False)
    
    # IC Calculation Components
    numerator = Column(Numeric(18,2))           # Interest collections
    denominator = Column(Numeric(18,2))         # Interest due
    liability_balance = Column(Numeric(18,2))   # For cure calculations
    calculated_ratio = Column(Numeric(10,6))    # IC ratio
    
    # Test Results
    pass_fail = Column(Boolean)
    
    # Cure Amounts
    cure_amount = Column(Numeric(18,2), default=0)
    prior_cure_payments = Column(Numeric(18,2), default=0)
    cure_amount_paid = Column(Numeric(18,2), default=0)
    
    # Audit Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="ic_triggers")
    
    # Unique constraint
    __table_args__ = (
        {'extend_existing': True},
    )
    
    def __repr__(self):
        return f"<ICTrigger({self.deal_id}:{self.tranche_name}, Period={self.period_number})>"


class ICTriggerCalculator:
    """
    ICTrigger Calculator - Python implementation of VBA ICTrigger.cls logic
    Handles interest coverage ratio calculations and cure mechanisms
    """
    
    def __init__(self, name: str, threshold: Decimal):
        """
        Initialize IC trigger calculator
        
        Args:
            name: Trigger name identifier  
            threshold: IC threshold ratio (e.g., 1.10 for 110%)
        """
        self.name = name
        self.trigger_threshold = threshold
        self.period_results: Dict[int, ICTriggerResult] = {}
        self.current_period = 1
        self.last_period_calculated = 0
        
    def setup_deal(self, num_payments: int):
        """
        Setup calculator for deal with specified number of payment periods
        VBA: DealSetup(iNumofPayments As Long)
        
        Args:
            num_payments: Total number of payment periods
        """
        # Initialize all periods
        for period in range(1, num_payments + 1):
            self.period_results[period] = ICTriggerResult()
            
        self.current_period = 1
        
    def calculate(self, numerator: Decimal, denominator: Decimal, liability_balance: Decimal) -> bool:
        """
        Calculate IC ratio and determine cure amounts
        VBA: Calc(iNum As Double, iDeno As Double, iLiabBal As Double)
        
        Args:
            numerator: Interest collections (cash inflow)
            denominator: Interest due (cash outflow requirement)
            liability_balance: Current liability balance for cure calculation
            
        Returns:
            bool: True if test passes, False if fails
        """
        if self.current_period not in self.period_results:
            self.period_results[self.current_period] = ICTriggerResult()
            
        result = self.period_results[self.current_period]
        
        # Store calculation inputs
        result.numerator = numerator
        result.denominator = denominator
        result.liability_balance = liability_balance
        result.threshold = self.trigger_threshold
        
        # Calculate IC ratio
        if denominator > 0:
            calculated_ratio = numerator / denominator
            result.calculated_ratio = calculated_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            # Determine pass/fail
            if calculated_ratio >= self.trigger_threshold:
                result.pass_fail = True
                result.cure_amount = Decimal('0')
            else:
                result.pass_fail = False
                
                # Calculate cure amount (VBA logic)
                # Cure = (1 - ratio / threshold) * liability_balance
                cure_amount = (Decimal('1') - calculated_ratio / self.trigger_threshold) * liability_balance
                result.cure_amount = cure_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            self.last_period_calculated = self.current_period
            return result.pass_fail
        else:
            # If no denominator, test automatically passes
            result.pass_fail = True
            result.calculated_ratio = Decimal('0')
            result.cure_amount = Decimal('0')
            return True
    
    def get_pass_fail(self) -> bool:
        """
        Get current period pass/fail status
        VBA: PassFail() As Boolean
        """
        if self.current_period in self.period_results:
            return self.period_results[self.current_period].pass_fail
        return True
    
    def get_cure_amount(self) -> Decimal:
        """
        Get required cure amount for current period
        VBA: CureAmount() As Double
        """
        if self.current_period not in self.period_results:
            return Decimal('0')
            
        result = self.period_results[self.current_period]
        return result.cure_amount - result.prior_cure_payments - result.cure_amount_paid
    
    def add_prior_cure(self, amount: Decimal) -> Decimal:
        """
        Add prior cure payment
        VBA: AddPriorCure(iAmount As Double)
        
        Args:
            amount: Amount of prior cure to add
            
        Returns:
            Decimal: Unused amount after applying cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.cure_amount - result.prior_cure_payments - result.cure_amount_paid
        
        if cure_due > amount:
            result.prior_cure_payments += amount
            return Decimal('0')
        else:
            result.prior_cure_payments += cure_due
            return amount - cure_due
    
    def pay_cure(self, amount: Decimal) -> Decimal:
        """
        Apply cure payment
        VBA: PayCure(iAmount As Double)
        
        Args:
            amount: Cure payment amount
            
        Returns:
            Decimal: Unused amount after applying cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.cure_amount - result.prior_cure_payments - result.cure_amount_paid
        
        if amount > cure_due:
            result.cure_amount_paid += cure_due
            return amount - cure_due
        else:
            result.cure_amount_paid += amount
            return Decimal('0')
    
    def rollforward(self):
        """
        Move to next period
        VBA: Rollfoward()  (Note: VBA has typo in method name)
        """
        self.current_period += 1
    
    def get_current_result(self) -> ICTriggerResult:
        """Get current period result"""
        if self.current_period in self.period_results:
            return self.period_results[self.current_period]
        return ICTriggerResult()
    
    def get_output(self) -> List[List[Any]]:
        """
        Generate output array for reporting
        VBA: Output() As Variant
        
        Returns:
            List of lists containing calculation results
        """
        if self.last_period_calculated == 0:
            return []
            
        # Header row
        output = [
            ["Numerator", "Denominator", "Liability Balance", "Results", "Threshold", 
             "Pass/Fail", "Prior Cure Payments", "Cure Amount", "Cure Paid"]
        ]
        
        # Data rows
        for period in range(1, self.last_period_calculated + 1):
            if period not in self.period_results:
                continue
                
            result = self.period_results[period]
            output.append([
                float(result.numerator),
                float(result.denominator),
                float(result.liability_balance),
                f"{float(result.calculated_ratio):.3%}",
                f"{float(self.trigger_threshold):.3%}",
                result.pass_fail,
                float(result.prior_cure_payments),
                float(result.cure_amount),
                float(result.cure_amount_paid)
            ])
        
        return output
    
    def get_cure_status_summary(self) -> Dict[str, Any]:
        """Get summary of cure status for current period"""
        if self.current_period not in self.period_results:
            return {"period": self.current_period, "test_passing": True, "cure_needed": False}
            
        result = self.period_results[self.current_period]
        cure_needed = self.get_cure_amount()
        
        return {
            "period": self.current_period,
            "ic_ratio": float(result.calculated_ratio),
            "ic_threshold": float(self.trigger_threshold),
            "test_passing": result.pass_fail,
            "cure_needed": cure_needed > 0,
            "cure_amount_needed": float(cure_needed),
            "total_cure_amount": float(result.cure_amount),
            "numerator": float(result.numerator),
            "denominator": float(result.denominator),
            "liability_balance": float(result.liability_balance)
        }
    
    def get_period_results(self, start_period: int = 1, end_period: Optional[int] = None) -> Dict[int, ICTriggerResult]:
        """
        Get results for a range of periods
        
        Args:
            start_period: Starting period (inclusive)
            end_period: Ending period (inclusive), defaults to last calculated
            
        Returns:
            Dictionary of period results
        """
        if end_period is None:
            end_period = self.last_period_calculated
            
        return {
            period: result for period, result in self.period_results.items()
            if start_period <= period <= end_period
        }
    
    def is_test_failing(self) -> bool:
        """Check if current period test is failing"""
        return not self.get_pass_fail()
    
    def get_total_cure_paid(self) -> Decimal:
        """Get total cure amount paid across all periods"""
        total = Decimal('0')
        for result in self.period_results.values():
            total += result.cure_amount_paid + result.prior_cure_payments
        return total
    
    def get_total_cure_outstanding(self) -> Decimal:
        """Get total outstanding cure amount across all periods"""
        total = Decimal('0')
        for period, result in self.period_results.items():
            if period <= self.current_period:
                outstanding = result.cure_amount - result.prior_cure_payments - result.cure_amount_paid
                total += max(Decimal('0'), outstanding)
        return total
    
    def reset_period_calculations(self, period: int):
        """Reset calculations for a specific period"""
        if period in self.period_results:
            self.period_results[period] = ICTriggerResult()
    
    def validate_calculation_inputs(self, numerator: Decimal, denominator: Decimal, 
                                  liability_balance: Decimal) -> List[str]:
        """
        Validate calculation inputs
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if numerator < 0:
            errors.append("Numerator (interest collections) cannot be negative")
            
        if denominator < 0:
            errors.append("Denominator (interest due) cannot be negative")
            
        if liability_balance < 0:
            errors.append("Liability balance cannot be negative")
            
        if self.trigger_threshold <= 0:
            errors.append("IC threshold must be positive")
            
        if self.trigger_threshold < Decimal('1.0'):
            errors.append("IC threshold should typically be >= 1.0 (100%)")
            
        return errors