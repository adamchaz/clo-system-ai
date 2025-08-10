"""
CLO Waterfall Logic - Payment Priority and Distribution Rules
Converts VBA waterfall calculations to Python with sophisticated payment sequencing
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
import json

from ..core.database import Base
from .asset import Asset
from .cash_flow import AssetCashFlow


class WaterfallStep(str, Enum):
    """Waterfall payment steps in priority order"""
    # Collection Account Management
    COLLECTION = "COLLECTION"
    EXPENSES = "EXPENSES"
    
    # Senior Fees and Expenses
    TRUSTEE_FEES = "TRUSTEE_FEES"
    ADMIN_FEES = "ADMIN_FEES"
    SENIOR_MGMT_FEES = "SENIOR_MGMT_FEES"
    
    # Interest Payments (by seniority)
    CLASS_A_INTEREST = "CLASS_A_INTEREST"
    CLASS_B_INTEREST = "CLASS_B_INTEREST" 
    CLASS_C_INTEREST = "CLASS_C_INTEREST"
    CLASS_D_INTEREST = "CLASS_D_INTEREST"
    
    # Reserve Account Funding
    INTEREST_RESERVE = "INTEREST_RESERVE"
    
    # Principal Payments
    CLASS_A_PRINCIPAL = "CLASS_A_PRINCIPAL"
    CLASS_B_PRINCIPAL = "CLASS_B_PRINCIPAL"
    CLASS_C_PRINCIPAL = "CLASS_C_PRINCIPAL"
    CLASS_D_PRINCIPAL = "CLASS_D_PRINCIPAL"
    
    # Junior Management Fees
    JUNIOR_MGMT_FEES = "JUNIOR_MGMT_FEES"
    INCENTIVE_MGMT_FEES = "INCENTIVE_MGMT_FEES"
    
    # Subordinated Payments
    CLASS_E_INTEREST = "CLASS_E_INTEREST"
    CLASS_E_PRINCIPAL = "CLASS_E_PRINCIPAL"
    
    # Residual
    RESIDUAL_EQUITY = "RESIDUAL_EQUITY"


class PaymentPriority(str, Enum):
    """Payment priority levels"""
    SENIOR = "SENIOR"
    SUBORDINATED = "SUBORDINATED"  
    RESIDUAL = "RESIDUAL"


class WaterfallConfiguration(Base):
    """
    Waterfall payment rules and configuration by deal
    Defines payment priorities, caps, and trigger conditions
    """
    __tablename__ = 'waterfall_configurations'
    
    config_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    
    # Configuration metadata
    config_name = Column(String(100), nullable=False)
    effective_date = Column(Date, nullable=False)
    version = Column(Integer, default=1)
    
    # Waterfall rules (JSON structure)
    payment_rules = Column(Text, nullable=False)  # JSON string of WaterfallRule objects
    
    # Reserve account requirements
    interest_reserve_target = Column(Numeric(18,2))
    interest_reserve_cap = Column(Numeric(18,2))
    
    # Management fee rates
    senior_mgmt_fee_rate = Column(Numeric(6,4))  # e.g., 0.004 = 40bps
    junior_mgmt_fee_rate = Column(Numeric(6,4))
    incentive_fee_rate = Column(Numeric(6,4))
    incentive_hurdle_rate = Column(Numeric(6,4))
    
    # Trustee and administrative fees
    trustee_fee_annual = Column(Numeric(10,2))
    admin_fee_cap = Column(Numeric(10,2))
    
    # Trigger events
    enable_oc_tests = Column(Boolean, default=True)
    enable_ic_tests = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    
    def get_payment_rules(self) -> List[Dict]:
        """Parse JSON payment rules"""
        return json.loads(self.payment_rules) if self.payment_rules else []


class WaterfallExecution(Base):
    """
    Records of waterfall execution by payment date
    Tracks cash available and distributions by step
    """
    __tablename__ = 'waterfall_executions'
    
    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    payment_date = Column(Date, nullable=False)
    config_id = Column(Integer, ForeignKey('waterfall_configurations.config_id'))
    
    # Available cash
    collection_amount = Column(Numeric(18,2), nullable=False)
    beginning_cash = Column(Numeric(18,2), default=0)
    total_available = Column(Numeric(18,2), nullable=False)
    
    # Reserve account balances
    interest_reserve_beginning = Column(Numeric(18,2), default=0)
    interest_reserve_ending = Column(Numeric(18,2), default=0)
    
    # Final residuals
    remaining_cash = Column(Numeric(18,2), default=0)
    
    # Trigger test results
    oc_test_pass = Column(Boolean)
    ic_test_pass = Column(Boolean)
    
    # Execution status
    execution_status = Column(String(20), default='PENDING')  # PENDING, COMPLETED, FAILED
    execution_notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    payments = relationship("WaterfallPayment", back_populates="execution", cascade="all, delete-orphan")


class WaterfallPayment(Base):
    """
    Individual payment within waterfall execution
    Records amount paid for each waterfall step
    """
    __tablename__ = 'waterfall_payments'
    
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey('waterfall_executions.execution_id'), nullable=False)
    
    # Payment details
    payment_step = Column(String(30), nullable=False)  # WaterfallStep enum value
    step_sequence = Column(Integer, nullable=False)    # Order within waterfall
    payment_priority = Column(String(20))              # PaymentPriority enum value
    
    # Amounts
    amount_due = Column(Numeric(18,2), nullable=False)
    amount_paid = Column(Numeric(18,2), nullable=False)
    amount_deferred = Column(Numeric(18,2), default=0)
    
    # Payment targets (tranche, account, etc.)
    target_tranche_id = Column(String(50), ForeignKey('clo_tranches.tranche_id'))
    target_account = Column(String(50))  # COLLECTION, INTEREST_RESERVE, etc.
    
    # Calculation details
    calculation_base = Column(Numeric(18,2))  # Base amount for rate calculations
    payment_rate = Column(Numeric(8,6))       # Rate applied (for fees)
    
    # Notes
    payment_notes = Column(Text)
    
    # Relationship
    execution = relationship("WaterfallExecution", back_populates="payments")


class WaterfallCalculator:
    """
    Core waterfall calculation engine
    Processes payment priorities and distributes available cash
    """
    
    def __init__(self, deal_id: str, payment_date: date, session):
        self.deal_id = deal_id
        self.payment_date = payment_date
        self.session = session
        self.config = self._load_configuration()
        self.available_cash = Decimal('0')
        self.payments: List[Dict] = []
        
    def execute_waterfall(self, collection_amount: Decimal, beginning_cash: Decimal = Decimal('0')) -> WaterfallExecution:
        """
        Execute complete waterfall for payment date
        Returns WaterfallExecution record with all payments
        """
        self.available_cash = collection_amount + beginning_cash
        total_available = self.available_cash
        
        # Create execution record
        execution = WaterfallExecution(
            deal_id=self.deal_id,
            payment_date=self.payment_date,
            config_id=self.config.config_id if self.config else None,
            collection_amount=collection_amount,
            beginning_cash=beginning_cash,
            total_available=total_available,
            execution_status='PENDING'
        )
        
        try:
            # Execute waterfall steps in priority order
            self._process_senior_expenses(execution)
            self._process_interest_payments(execution)
            self._process_reserve_funding(execution)
            self._process_principal_payments(execution)
            self._process_junior_fees(execution)
            self._process_subordinated_payments(execution)
            self._process_residual_payments(execution)
            
            # Update final balances
            execution.remaining_cash = self.available_cash
            execution.execution_status = 'COMPLETED'
            
            # Save to database
            self.session.add(execution)
            self.session.commit()
            
            return execution
            
        except Exception as e:
            execution.execution_status = 'FAILED'
            execution.execution_notes = str(e)
            self.session.add(execution)
            self.session.commit()
            raise
    
    def _process_senior_expenses(self, execution: WaterfallExecution):
        """Process senior fees and expenses (first priority)"""
        
        # Trustee fees
        trustee_fee = self._calculate_trustee_fee()
        self._make_payment(
            execution, WaterfallStep.TRUSTEE_FEES, trustee_fee,
            target_account="TRUSTEE_PAYABLE", 
            notes="Quarterly trustee fee"
        )
        
        # Administrative fees  
        admin_fee = self._calculate_admin_fee()
        self._make_payment(
            execution, WaterfallStep.ADMIN_FEES, admin_fee,
            target_account="ADMIN_PAYABLE",
            notes="Administrative and operational expenses"
        )
        
        # Senior management fees
        senior_mgmt_fee = self._calculate_senior_mgmt_fee()
        self._make_payment(
            execution, WaterfallStep.SENIOR_MGMT_FEES, senior_mgmt_fee,
            target_account="MGMT_FEE_PAYABLE",
            notes="Senior management fee"
        )
    
    def _process_interest_payments(self, execution: WaterfallExecution):
        """Process note interest payments by seniority"""
        
        # Get tranches in payment order
        tranches = self._get_tranches_by_seniority()
        
        for tranche in tranches:
            if tranche.seniority_level <= 4:  # Senior tranches (A, B, C, D)
                interest_due = self._calculate_interest_due(tranche)
                step_name = f"CLASS_{tranche.tranche_name[-1]}_INTEREST"
                
                # Check if payment triggers are met
                can_pay = self._check_interest_payment_triggers(tranche)
                
                if can_pay:
                    self._make_payment(
                        execution, step_name, interest_due,
                        target_tranche_id=tranche.tranche_id,
                        notes=f"Interest payment to {tranche.tranche_name}"
                    )
                else:
                    # Defer payment if triggers not met
                    self._defer_payment(
                        execution, step_name, interest_due,
                        target_tranche_id=tranche.tranche_id,
                        notes=f"Interest deferred due to trigger breach"
                    )
    
    def _process_reserve_funding(self, execution: WaterfallExecution):
        """Fund interest reserve account to target level"""
        
        if not self.config:
            return
            
        current_reserve = self._get_current_reserve_balance()
        target_reserve = self.config.interest_reserve_target or Decimal('0')
        reserve_cap = self.config.interest_reserve_cap or target_reserve
        
        # Calculate required funding
        funding_needed = min(
            max(target_reserve - current_reserve, Decimal('0')),
            reserve_cap - current_reserve
        )
        
        if funding_needed > 0:
            self._make_payment(
                execution, WaterfallStep.INTEREST_RESERVE, funding_needed,
                target_account="INTEREST_RESERVE",
                notes=f"Reserve funding: ${current_reserve:,.0f} → ${target_reserve:,.0f}"
            )
    
    def _process_principal_payments(self, execution: WaterfallExecution):
        """Process note principal payments"""
        
        # Check if principal payments are triggered
        oc_pass = self._check_overcollateralization_tests()
        ic_pass = self._check_interest_coverage_tests()
        
        execution.oc_test_pass = oc_pass
        execution.ic_test_pass = ic_pass
        
        if not (oc_pass and ic_pass):
            # Principal payments trapped - all goes to Class A
            self._process_accelerated_principal(execution)
            return
        
        # Normal sequential principal payments
        tranches = self._get_tranches_by_seniority()
        
        for tranche in tranches:
            if tranche.seniority_level <= 4 and tranche.current_balance > 0:
                
                # Calculate principal payment amount
                principal_payment = self._calculate_principal_payment(tranche)
                
                if principal_payment > 0:
                    step_name = f"CLASS_{tranche.tranche_name[-1]}_PRINCIPAL"
                    self._make_payment(
                        execution, step_name, principal_payment,
                        target_tranche_id=tranche.tranche_id,
                        notes=f"Principal payment to {tranche.tranche_name}"
                    )
                    
                    # Update tranche balance
                    tranche.current_balance -= principal_payment
    
    def _process_accelerated_principal(self, execution: WaterfallExecution):
        """Process accelerated principal payments when tests fail"""
        
        # All available cash goes to Class A principal
        class_a = self._get_tranche_by_class('A')
        if class_a and class_a.current_balance > 0:
            
            principal_payment = min(self.available_cash, class_a.current_balance)
            
            if principal_payment > 0:
                self._make_payment(
                    execution, WaterfallStep.CLASS_A_PRINCIPAL, principal_payment,
                    target_tranche_id=class_a.tranche_id,
                    notes="Accelerated principal payment due to test failure"
                )
                
                class_a.current_balance -= principal_payment
    
    def _process_junior_fees(self, execution: WaterfallExecution):
        """Process junior management fees"""
        
        # Junior management fee
        junior_fee = self._calculate_junior_mgmt_fee()
        if junior_fee > 0:
            self._make_payment(
                execution, WaterfallStep.JUNIOR_MGMT_FEES, junior_fee,
                target_account="MGMT_FEE_PAYABLE",
                notes="Junior management fee"
            )
        
        # Incentive management fee (if hurdle met)
        incentive_fee = self._calculate_incentive_fee()
        if incentive_fee > 0:
            self._make_payment(
                execution, WaterfallStep.INCENTIVE_MGMT_FEES, incentive_fee,
                target_account="MGMT_FEE_PAYABLE", 
                notes="Incentive fee above hurdle rate"
            )
    
    def _process_subordinated_payments(self, execution: WaterfallExecution):
        """Process subordinated note payments (Class E)"""
        
        class_e = self._get_tranche_by_class('E')
        if not class_e:
            return
        
        # Class E interest
        interest_due = self._calculate_interest_due(class_e)
        if interest_due > 0:
            self._make_payment(
                execution, WaterfallStep.CLASS_E_INTEREST, interest_due,
                target_tranche_id=class_e.tranche_id,
                notes=f"Interest payment to {class_e.tranche_name}"
            )
        
        # Class E principal (if any balance remaining)
        if class_e.current_balance > 0:
            principal_payment = min(self.available_cash, class_e.current_balance)
            if principal_payment > 0:
                self._make_payment(
                    execution, WaterfallStep.CLASS_E_PRINCIPAL, principal_payment,
                    target_tranche_id=class_e.tranche_id,
                    notes=f"Principal payment to {class_e.tranche_name}"
                )
                
                class_e.current_balance -= principal_payment
    
    def _process_residual_payments(self, execution: WaterfallExecution):
        """Process any remaining residual payments to equity"""
        
        if self.available_cash > 0:
            self._make_payment(
                execution, WaterfallStep.RESIDUAL_EQUITY, self.available_cash,
                target_account="EQUITY_DISTRIBUTION",
                notes="Residual distribution to equity holders"
            )
    
    def _make_payment(self, execution: WaterfallExecution, step: str, amount_due: Decimal,
                     target_tranche_id: Optional[str] = None, 
                     target_account: Optional[str] = None,
                     notes: Optional[str] = None):
        """Execute payment within waterfall constraints"""
        
        # Calculate actual payment (limited by available cash)
        amount_paid = min(amount_due, self.available_cash)
        amount_deferred = amount_due - amount_paid
        
        # Create payment record
        payment = WaterfallPayment(
            execution_id=execution.execution_id,
            payment_step=step,
            step_sequence=len(execution.payments) + 1,
            payment_priority=self._get_payment_priority(step),
            amount_due=amount_due,
            amount_paid=amount_paid,
            amount_deferred=amount_deferred,
            target_tranche_id=target_tranche_id,
            target_account=target_account,
            payment_notes=notes
        )
        
        execution.payments.append(payment)
        
        # Reduce available cash
        self.available_cash -= amount_paid
        
        # Ensure no negative cash
        if self.available_cash < 0:
            self.available_cash = Decimal('0')
    
    def _defer_payment(self, execution: WaterfallExecution, step: str, amount_due: Decimal,
                      target_tranche_id: Optional[str] = None,
                      notes: Optional[str] = None):
        """Record deferred payment (no cash disbursed)"""
        
        payment = WaterfallPayment(
            execution_id=execution.execution_id,
            payment_step=step,
            step_sequence=len(execution.payments) + 1,
            payment_priority=self._get_payment_priority(step),
            amount_due=amount_due,
            amount_paid=Decimal('0'),
            amount_deferred=amount_due,
            target_tranche_id=target_tranche_id,
            payment_notes=notes
        )
        
        execution.payments.append(payment)
    
    def _calculate_trustee_fee(self) -> Decimal:
        """Calculate quarterly trustee fee"""
        if not self.config or not self.config.trustee_fee_annual:
            return Decimal('0')
        
        return (self.config.trustee_fee_annual / Decimal('4')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_admin_fee(self) -> Decimal:
        """Calculate administrative fees"""
        # Implementation would calculate actual admin expenses
        # For now, return configured cap amount quarterly
        if not self.config or not self.config.admin_fee_cap:
            return Decimal('0')
            
        return (self.config.admin_fee_cap / Decimal('4')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_senior_mgmt_fee(self) -> Decimal:
        """Calculate senior management fee based on collateral balance"""
        if not self.config or not self.config.senior_mgmt_fee_rate:
            return Decimal('0')
        
        collateral_balance = self._get_collateral_balance()
        quarterly_rate = self.config.senior_mgmt_fee_rate / Decimal('4')
        
        return (collateral_balance * quarterly_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_junior_mgmt_fee(self) -> Decimal:
        """Calculate junior management fee"""
        if not self.config or not self.config.junior_mgmt_fee_rate:
            return Decimal('0')
        
        collateral_balance = self._get_collateral_balance()
        quarterly_rate = self.config.junior_mgmt_fee_rate / Decimal('4')
        
        return (collateral_balance * quarterly_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_incentive_fee(self) -> Decimal:
        """Calculate incentive fee if hurdle rate exceeded"""
        # Complex calculation based on equity returns vs hurdle
        # Implementation would calculate actual returns and compare to hurdle
        return Decimal('0')  # Placeholder
    
    def _calculate_interest_due(self, tranche) -> Decimal:
        """Calculate interest payment due for tranche"""
        if not tranche.current_balance or not tranche.coupon_rate:
            return Decimal('0')
        
        # Quarterly interest calculation
        quarterly_rate = Decimal(str(tranche.coupon_rate)) / Decimal('4')
        
        return (Decimal(str(tranche.current_balance)) * quarterly_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_principal_payment(self, tranche) -> Decimal:
        """Calculate principal payment for tranche"""
        # Implementation would consider:
        # - Available cash after senior payments
        # - Amortization schedules
        # - Call provisions
        # - Reinvestment period status
        
        # For now, return proportion of available cash
        if not tranche.current_balance:
            return Decimal('0')
            
        # Simple sequential payment - pay in full if cash available
        return min(self.available_cash, Decimal(str(tranche.current_balance)))
    
    def _check_overcollateralization_tests(self) -> bool:
        """Check if OC tests are passing"""
        # Implementation would calculate actual OC ratios
        # and compare to required thresholds
        return True  # Placeholder
    
    def _check_interest_coverage_tests(self) -> bool:
        """Check if IC tests are passing"""
        # Implementation would calculate actual IC ratios
        return True  # Placeholder
    
    def _check_interest_payment_triggers(self, tranche) -> bool:
        """Check if interest payment triggers are satisfied"""
        # For senior tranches, usually always pay unless in default
        return tranche.seniority_level <= 4
    
    def _get_payment_priority(self, step: str) -> str:
        """Get payment priority level for waterfall step"""
        senior_steps = [
            WaterfallStep.TRUSTEE_FEES, WaterfallStep.ADMIN_FEES, 
            WaterfallStep.SENIOR_MGMT_FEES, WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.CLASS_B_INTEREST, WaterfallStep.CLASS_C_INTEREST,
            WaterfallStep.CLASS_D_INTEREST, WaterfallStep.INTEREST_RESERVE,
            WaterfallStep.CLASS_A_PRINCIPAL, WaterfallStep.CLASS_B_PRINCIPAL,
            WaterfallStep.CLASS_C_PRINCIPAL, WaterfallStep.CLASS_D_PRINCIPAL
        ]
        
        if step in [s.value for s in senior_steps]:
            return PaymentPriority.SENIOR.value
        elif step in [WaterfallStep.CLASS_E_INTEREST.value, WaterfallStep.CLASS_E_PRINCIPAL.value]:
            return PaymentPriority.SUBORDINATED.value
        else:
            return PaymentPriority.RESIDUAL.value
    
    def _load_configuration(self):
        """Load waterfall configuration for deal"""
        return self.session.query(WaterfallConfiguration).filter_by(
            deal_id=self.deal_id
        ).order_by(WaterfallConfiguration.effective_date.desc()).first()
    
    def _get_tranches_by_seniority(self):
        """Get tranches ordered by seniority"""
        from .clo_deal import CLOTranche  # Import here to avoid circular imports
        return self.session.query(CLOTranche).filter_by(
            deal_id=self.deal_id
        ).order_by(CLOTranche.seniority_level).all()
    
    def _get_tranche_by_class(self, class_letter: str):
        """Get specific tranche by class letter"""
        from .clo_deal import CLOTranche
        return self.session.query(CLOTranche).filter(
            CLOTranche.deal_id == self.deal_id,
            CLOTranche.tranche_name.ilike(f'%Class {class_letter}%')
        ).first()
    
    def _get_collateral_balance(self) -> Decimal:
        """Get current collateral balance for fee calculations"""
        from .clo_deal import DealAsset
        result = self.session.query(func.sum(DealAsset.par_amount)).filter(
            DealAsset.deal_id == self.deal_id,
            DealAsset.position_status == 'ACTIVE'
        ).scalar()
        
        return Decimal(str(result or 0))
    
    def _get_current_reserve_balance(self) -> Decimal:
        """Get current interest reserve account balance"""
        # Implementation would query reserve account balances
        return Decimal('0')  # Placeholder