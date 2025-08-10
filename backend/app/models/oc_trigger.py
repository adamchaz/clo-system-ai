"""
OCTrigger Model - Python conversion of OCTrigger.cls VBA class
Handles Overcollateralization trigger calculations and cure mechanisms
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


class OCTriggerResult:
    """Result object for OC trigger calculations"""
    
    def __init__(self):
        self.numerator: Decimal = Decimal('0')
        self.denominator: Decimal = Decimal('0')
        self.calculated_ratio: Decimal = Decimal('0')
        self.threshold: Decimal = Decimal('0')
        self.pass_fail: bool = True
        self.interest_cure_amount: Decimal = Decimal('0')
        self.principal_cure_amount: Decimal = Decimal('0')
        self.prior_interest_cure: Decimal = Decimal('0')
        self.prior_principal_cure: Decimal = Decimal('0')
        self.interest_cure_paid: Decimal = Decimal('0')
        self.principal_cure_paid: Decimal = Decimal('0')


class OCTrigger(Base):
    """
    OCTrigger Model - Overcollateralization trigger tracking
    Converted from VBA OCTrigger.cls (186 lines) with enhanced functionality
    """
    __tablename__ = 'oc_triggers'
    
    # Primary Key
    trigger_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    tranche_name = Column(String(50), nullable=False)
    
    # Trigger Configuration
    trigger_name = Column(String(100), nullable=False)
    oc_threshold = Column(Numeric(8,6), nullable=False)  # e.g., 1.20 = 120%
    
    # Period Tracking
    period_number = Column(Integer, nullable=False)
    
    # OC Calculation Components
    numerator = Column(Numeric(18,2))           # Collateral balance
    denominator = Column(Numeric(18,2))         # Liability balance
    calculated_ratio = Column(Numeric(10,6))    # OC ratio
    
    # Test Results
    pass_fail = Column(Boolean)
    
    # Cure Amounts - Interest Component
    interest_cure_amount = Column(Numeric(18,2), default=0)
    prior_interest_cure = Column(Numeric(18,2), default=0)
    interest_cure_paid = Column(Numeric(18,2), default=0)
    
    # Cure Amounts - Principal Component  
    principal_cure_amount = Column(Numeric(18,2), default=0)
    prior_principal_cure = Column(Numeric(18,2), default=0)
    principal_cure_paid = Column(Numeric(18,2), default=0)
    
    # Audit Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="oc_triggers")
    
    # Unique constraint
    __table_args__ = (
        {'extend_existing': True},
    )
    
    def __repr__(self):
        return f"<OCTrigger({self.deal_id}:{self.tranche_name}, Period={self.period_number})>"


class OCTriggerCalculator:
    """
    OCTrigger Calculator - Python implementation of VBA OCTrigger.cls logic
    Handles overcollateralization ratio calculations and cure mechanisms
    """
    
    def __init__(self, name: str, threshold: Decimal):
        """
        Initialize OC trigger calculator
        
        Args:
            name: Trigger name identifier
            threshold: OC threshold ratio (e.g., 1.20 for 120%)
        """
        self.name = name
        self.trigger_threshold = threshold
        self.period_results: Dict[int, OCTriggerResult] = {}
        self.current_period = 1
        self.last_period_calculated = 0
        
    def setup_deal(self, num_payments: int):
        """
        Setup calculator for deal with specified number of payment periods
        
        Args:
            num_payments: Total number of payment periods
        """
        # Initialize all periods
        for period in range(1, num_payments + 1):
            self.period_results[period] = OCTriggerResult()
            
        self.current_period = 1
        
    def calculate(self, numerator: Decimal, denominator: Decimal) -> bool:
        """
        Calculate OC ratio and determine cure amounts
        VBA: Calc(iNum As Double, iDeno As Double)
        
        Args:
            numerator: Collateral balance (asset side)
            denominator: Liability balance (note side)
            
        Returns:
            bool: True if test passes, False if fails
        """
        if self.current_period not in self.period_results:
            self.period_results[self.current_period] = OCTriggerResult()
            
        result = self.period_results[self.current_period]
        
        # Store calculation inputs
        result.numerator = numerator
        result.denominator = denominator
        result.threshold = self.trigger_threshold
        
        # Calculate OC ratio
        if denominator > 0:
            calculated_ratio = numerator / denominator
            result.calculated_ratio = calculated_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            # Determine pass/fail
            if calculated_ratio >= self.trigger_threshold:
                result.pass_fail = True
                result.interest_cure_amount = Decimal('0')
                result.principal_cure_amount = Decimal('0')
            else:
                result.pass_fail = False
                
                # Calculate cure amounts (VBA logic)
                # Interest cure: (1 - ratio / threshold) * denominator
                interest_cure = (Decimal('1') - calculated_ratio / self.trigger_threshold) * denominator
                result.interest_cure_amount = interest_cure.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Principal cure: (threshold * denominator - numerator) / (threshold - 1)
                if self.trigger_threshold > Decimal('1'):
                    principal_cure = (self.trigger_threshold * denominator - numerator) / (self.trigger_threshold - Decimal('1'))
                    result.principal_cure_amount = principal_cure.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    result.principal_cure_amount = Decimal('0')
            
            self.last_period_calculated = self.current_period
            return result.pass_fail
        else:
            # If no denominator, test automatically passes
            result.pass_fail = True
            result.calculated_ratio = Decimal('0')
            result.interest_cure_amount = Decimal('0')
            result.principal_cure_amount = Decimal('0')
            return True
    
    def get_pass_fail(self) -> bool:
        """
        Get current period pass/fail status
        VBA: PassFail() As Boolean
        """
        if self.current_period in self.period_results:
            return self.period_results[self.current_period].pass_fail
        return True
    
    def get_interest_cure_amount(self) -> Decimal:
        """
        Get required interest cure amount for current period
        VBA: InterestCureAmount() As Double
        """
        if self.current_period not in self.period_results:
            return Decimal('0')
            
        result = self.period_results[self.current_period]
        return result.interest_cure_amount - result.interest_cure_paid - result.prior_interest_cure
    
    def get_principal_cure_amount(self) -> Decimal:
        """
        Get required principal cure amount for current period  
        VBA: PrincipalCureAmount() As Double
        """
        if self.current_period not in self.period_results:
            return Decimal('0')
            
        result = self.period_results[self.current_period]
        return result.principal_cure_amount - result.principal_cure_paid - result.prior_principal_cure
    
    def add_prior_interest_cure(self, amount: Decimal) -> Decimal:
        """
        Add prior interest cure payment
        VBA: AddPriorIntCure(iAmount As Double)
        
        Args:
            amount: Amount of prior cure to add
            
        Returns:
            Decimal: Unused amount after applying cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.interest_cure_amount - result.interest_cure_paid - result.prior_interest_cure
        
        if amount >= cure_due:
            result.prior_interest_cure += cure_due
            # Deal has been cured by IC Test - zero out principal cure
            result.principal_cure_amount = Decimal('0')
            return amount - cure_due
        else:
            result.prior_interest_cure += amount
            return Decimal('0')
    
    def pay_interest(self, amount: Decimal) -> Decimal:
        """
        Apply interest payment to cure
        VBA: PayInterest(iAmount As Double)
        
        Args:
            amount: Interest payment amount
            
        Returns:
            Decimal: Unused amount after applying to cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.interest_cure_amount - result.interest_cure_paid - result.prior_interest_cure
        
        if amount >= cure_due:
            result.interest_cure_paid += cure_due
            remaining = amount - cure_due
            # OC breach has been cured by interest proceeds
            result.principal_cure_amount = Decimal('0')
        else:
            result.interest_cure_paid += amount
            remaining = Decimal('0')
        
        # Recalculate principal cure based on any interest payments
        if not result.pass_fail and result.principal_cure_amount > 0:
            # Recalculate with updated interest payments
            adjusted_denominator = result.denominator - result.interest_cure_paid - result.prior_interest_cure
            if adjusted_denominator > 0 and self.trigger_threshold > Decimal('1'):
                new_principal_cure = (self.trigger_threshold * adjusted_denominator - result.numerator) / (self.trigger_threshold - Decimal('1'))
                result.principal_cure_amount = max(Decimal('0'), new_principal_cure.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return remaining
    
    def add_prior_principal_cure(self, amount: Decimal) -> Decimal:
        """
        Add prior principal cure payment
        VBA: AddPriorPrinCure(iAmount As Double)
        
        Args:
            amount: Amount of prior principal cure
            
        Returns:
            Decimal: Unused amount after applying cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.principal_cure_amount - result.principal_cure_paid - result.prior_principal_cure
        
        if amount >= cure_due:
            result.prior_principal_cure += cure_due
            return amount - cure_due
        else:
            result.prior_principal_cure += amount
            return Decimal('0')
    
    def pay_principal(self, amount: Decimal) -> Decimal:
        """
        Apply principal payment to cure
        VBA: PayPrincipal(iAmount As Double)
        
        Args:
            amount: Principal payment amount
            
        Returns:
            Decimal: Unused amount after applying to cure
        """
        if self.current_period not in self.period_results:
            return amount
            
        result = self.period_results[self.current_period]
        cure_due = result.principal_cure_amount - result.principal_cure_paid - result.prior_principal_cure
        
        if amount >= cure_due:
            result.principal_cure_paid += cure_due
            return amount - cure_due
        else:
            result.principal_cure_paid += amount
            return Decimal('0')
    
    def rollforward(self):
        """
        Move to next period
        VBA: Rollfoward()
        """
        self.current_period += 1
    
    def get_current_result(self) -> OCTriggerResult:
        """Get current period result"""
        if self.current_period in self.period_results:
            return self.period_results[self.current_period]
        return OCTriggerResult()
    
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
            ["Numerator", "Denominator", "Result", "Threshold", "Pass/Fail", 
             "Prior Int Cure", "Prior Prin Cure", "Int Cure Amount", "Int Cure Paid", 
             "Prin Cure Amount", "Prin Cure Paid"]
        ]
        
        # Data rows
        for period in range(1, self.last_period_calculated + 1):
            if period not in self.period_results:
                continue
                
            result = self.period_results[period]
            output.append([
                float(result.numerator),
                float(result.denominator),
                f"{float(result.calculated_ratio):.3%}",
                f"{float(self.trigger_threshold):.3%}",
                result.pass_fail,
                float(result.prior_interest_cure),
                float(result.prior_principal_cure),
                float(result.interest_cure_amount),
                float(result.interest_cure_paid),
                float(result.principal_cure_amount),
                float(result.principal_cure_paid)
            ])
        
        return output
    
    def get_cure_status_summary(self) -> Dict[str, Any]:
        """Get summary of cure status for current period"""
        if self.current_period not in self.period_results:
            return {"period": self.current_period, "test_passing": True, "cures_needed": False}
            
        result = self.period_results[self.current_period]
        
        interest_cure_needed = self.get_interest_cure_amount()
        principal_cure_needed = self.get_principal_cure_amount()
        
        return {
            "period": self.current_period,
            "oc_ratio": float(result.calculated_ratio),
            "oc_threshold": float(self.trigger_threshold),
            "test_passing": result.pass_fail,
            "cures_needed": interest_cure_needed > 0 or principal_cure_needed > 0,
            "interest_cure_needed": float(interest_cure_needed),
            "principal_cure_needed": float(principal_cure_needed),
            "total_interest_cure": float(result.interest_cure_amount),
            "total_principal_cure": float(result.principal_cure_amount)
        }