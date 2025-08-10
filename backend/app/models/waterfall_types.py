"""
Waterfall Types and Implementations
Handles different CLO waterfall structures with configurable payment logic
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import date
from enum import Enum

from .waterfall import WaterfallStep, WaterfallCalculator, WaterfallExecution
from .clo_deal import CLOTranche


class WaterfallType(str, Enum):
    """Standard waterfall implementation types"""
    TRADITIONAL = "TRADITIONAL"           # Sequential pay, OC/IC tests
    TURBO = "TURBO"                      # Accelerated principal payments
    PIK_TOGGLE = "PIK_TOGGLE"            # Payment-in-kind toggle notes
    EQUITY_CLAW_BACK = "EQUITY_CLAW_BACK"  # Equity claw-back provisions
    CALL_PROTECTION = "CALL_PROTECTION"   # Non-call periods with step-downs
    REINVESTMENT = "REINVESTMENT"        # Reinvestment period rules
    EUROPEAN_STYLE = "EUROPEAN_STYLE"    # European waterfall variations
    CUSTOM = "CUSTOM"                    # Deal-specific custom logic


class PaymentPhase(str, Enum):
    """Payment phases within waterfall"""
    RAMP_UP = "RAMP_UP"                  # Portfolio ramp-up period
    REINVESTMENT = "REINVESTMENT"        # Active reinvestment period
    AMORTIZATION = "AMORTIZATION"        # Principal amortization phase
    CALL_PERIOD = "CALL_PERIOD"          # Optional redemption period
    ACCELERATION = "ACCELERATION"        # Accelerated amortization


class TriggerCondition(str, Enum):
    """Trigger conditions affecting payments"""
    OC_TEST_FAILURE = "OC_TEST_FAILURE"
    IC_TEST_FAILURE = "IC_TEST_FAILURE"
    REINVESTMENT_END = "REINVESTMENT_END"
    CALL_DATE_REACHED = "CALL_DATE_REACHED"
    DEFAULT_THRESHOLD = "DEFAULT_THRESHOLD"
    EQUITY_HURDLE_MET = "EQUITY_HURDLE_MET"
    FREQUENCY_CHANGE = "FREQUENCY_CHANGE"


class BaseWaterfallStrategy(ABC):
    """
    Abstract base class for waterfall implementations
    Defines interface that all waterfall types must implement
    """
    
    def __init__(self, calculator: WaterfallCalculator):
        self.calculator = calculator
        self.deal_id = calculator.deal_id
        self.payment_date = calculator.payment_date
        self.session = calculator.session
    
    @abstractmethod
    def get_payment_sequence(self) -> List[WaterfallStep]:
        """Return ordered list of payment steps for this waterfall type"""
        pass
    
    @abstractmethod
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Check if payment step should be executed based on triggers"""
        pass
    
    @abstractmethod
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Calculate payment amount for specific step"""
        pass
    
    @abstractmethod
    def get_payment_phase(self) -> PaymentPhase:
        """Determine current payment phase for the deal"""
        pass
    
    def process_waterfall(self, execution: WaterfallExecution):
        """Execute complete waterfall using strategy-specific logic"""
        phase = self.get_payment_phase()
        sequence = self.get_payment_sequence()
        
        for step in sequence:
            if self._should_process_step(step, phase):
                self._process_payment_step(execution, step)
    
    def _should_process_step(self, step: WaterfallStep, phase: PaymentPhase) -> bool:
        """Determine if step should be processed in current phase"""
        # Base implementation - override in specific strategies
        return True
    
    def _process_payment_step(self, execution: WaterfallExecution, step: WaterfallStep):
        """Process individual payment step"""
        tranche = self._get_target_tranche(step)
        
        if self.check_payment_triggers(step, tranche):
            amount = self.calculate_payment_amount(step, tranche)
            
            self.calculator._make_payment(
                execution, step.value, amount,
                target_tranche_id=tranche.tranche_id if tranche else None,
                notes=f"{step.value} payment in {self.get_payment_phase().value} phase"
            )
    
    def _get_target_tranche(self, step: WaterfallStep) -> Optional[CLOTranche]:
        """Get target tranche for payment step"""
        if 'CLASS_A' in step.value:
            return self.calculator._get_tranche_by_class('A')
        elif 'CLASS_B' in step.value:
            return self.calculator._get_tranche_by_class('B')
        elif 'CLASS_C' in step.value:
            return self.calculator._get_tranche_by_class('C')
        elif 'CLASS_D' in step.value:
            return self.calculator._get_tranche_by_class('D')
        elif 'CLASS_E' in step.value:
            return self.calculator._get_tranche_by_class('E')
        return None


class TraditionalWaterfall(BaseWaterfallStrategy):
    """
    Traditional sequential-pay waterfall
    Standard CLO structure with OC/IC tests and sequential principal payments
    """
    
    def get_payment_sequence(self) -> List[WaterfallStep]:
        """Traditional waterfall sequence"""
        return [
            # Senior expenses
            WaterfallStep.TRUSTEE_FEES,
            WaterfallStep.ADMIN_FEES, 
            WaterfallStep.SENIOR_MGMT_FEES,
            
            # Interest payments by seniority
            WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.CLASS_B_INTEREST,
            WaterfallStep.CLASS_C_INTEREST,
            WaterfallStep.CLASS_D_INTEREST,
            
            # Reserve funding
            WaterfallStep.INTEREST_RESERVE,
            
            # Principal payments (sequential)
            WaterfallStep.CLASS_A_PRINCIPAL,
            WaterfallStep.CLASS_B_PRINCIPAL,
            WaterfallStep.CLASS_C_PRINCIPAL,
            WaterfallStep.CLASS_D_PRINCIPAL,
            
            # Junior fees
            WaterfallStep.JUNIOR_MGMT_FEES,
            WaterfallStep.INCENTIVE_MGMT_FEES,
            
            # Subordinated
            WaterfallStep.CLASS_E_INTEREST,
            WaterfallStep.CLASS_E_PRINCIPAL,
            
            # Residual
            WaterfallStep.RESIDUAL_EQUITY
        ]
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Traditional trigger logic"""
        if step in [WaterfallStep.CLASS_A_PRINCIPAL, WaterfallStep.CLASS_B_PRINCIPAL,
                   WaterfallStep.CLASS_C_PRINCIPAL, WaterfallStep.CLASS_D_PRINCIPAL]:
            # Principal payments require OC/IC tests to pass
            return (self.calculator._check_overcollateralization_tests() and
                   self.calculator._check_interest_coverage_tests())
        
        # Senior expenses and interest always pay (unless in default)
        return True
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Traditional payment amount calculations"""
        if step == WaterfallStep.TRUSTEE_FEES:
            return self.calculator._calculate_trustee_fee()
        elif step == WaterfallStep.ADMIN_FEES:
            return self.calculator._calculate_admin_fee()
        elif step == WaterfallStep.SENIOR_MGMT_FEES:
            return self.calculator._calculate_senior_mgmt_fee()
        elif 'INTEREST' in step.value and tranche:
            return self.calculator._calculate_interest_due(tranche)
        elif 'PRINCIPAL' in step.value and tranche:
            return self.calculator._calculate_principal_payment(tranche)
        elif step == WaterfallStep.INTEREST_RESERVE:
            return self._calculate_reserve_funding()
        else:
            return Decimal('0')
    
    def get_payment_phase(self) -> PaymentPhase:
        """Determine payment phase based on deal dates"""
        deal = self.calculator.session.query(self.calculator.deal_id).first()
        
        if self.payment_date <= deal.reinvestment_end_date:
            return PaymentPhase.REINVESTMENT
        elif self.payment_date >= deal.no_call_date:
            return PaymentPhase.CALL_PERIOD
        else:
            return PaymentPhase.AMORTIZATION
    
    def _calculate_reserve_funding(self) -> Decimal:
        """Calculate interest reserve funding need"""
        current_reserve = self.calculator._get_current_reserve_balance()
        target_reserve = self.calculator.config.interest_reserve_target or Decimal('0')
        
        return max(target_reserve - current_reserve, Decimal('0'))


class TurboWaterfall(TraditionalWaterfall):
    """
    Turbo waterfall with accelerated principal payments
    Excess cash after senior expenses goes to principal
    """
    
    def get_payment_sequence(self) -> List[WaterfallStep]:
        """Turbo sequence - principal payments earlier"""
        return [
            # Senior expenses
            WaterfallStep.TRUSTEE_FEES,
            WaterfallStep.ADMIN_FEES,
            WaterfallStep.SENIOR_MGMT_FEES,
            
            # Interest payments
            WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.CLASS_B_INTEREST,
            WaterfallStep.CLASS_C_INTEREST,
            WaterfallStep.CLASS_D_INTEREST,
            
            # Turbo principal (before reserve funding)
            WaterfallStep.CLASS_A_PRINCIPAL,
            WaterfallStep.CLASS_B_PRINCIPAL,
            WaterfallStep.CLASS_C_PRINCIPAL, 
            WaterfallStep.CLASS_D_PRINCIPAL,
            
            # Then reserve and subordinated payments
            WaterfallStep.INTEREST_RESERVE,
            WaterfallStep.JUNIOR_MGMT_FEES,
            WaterfallStep.CLASS_E_INTEREST,
            WaterfallStep.CLASS_E_PRINCIPAL,
            WaterfallStep.RESIDUAL_EQUITY
        ]
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Turbo payment amounts - principal gets more cash"""
        base_amount = super().calculate_payment_amount(step, tranche)
        
        if 'PRINCIPAL' in step.value and tranche:
            # In turbo, principal gets all available cash (subject to balance limits)
            available = self.calculator.available_cash
            balance_limit = Decimal(str(tranche.current_balance or 0))
            
            return min(available, balance_limit)
        
        return base_amount


class PIKToggleWaterfall(TraditionalWaterfall):
    """
    PIK Toggle waterfall with payment-in-kind option
    Interest can be paid in cash or added to principal
    """
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """PIK toggle trigger logic"""
        if 'INTEREST' in step.value and tranche and hasattr(tranche, 'pik_toggle_enabled'):
            # Check if PIK election has been made
            return not self._is_pik_elected(tranche)
        
        return super().check_payment_triggers(step, tranche)
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """PIK toggle payment calculation"""
        if 'INTEREST' in step.value and tranche:
            interest_due = self.calculator._calculate_interest_due(tranche)
            
            if self._is_pik_elected(tranche):
                # PIK election - add to principal balance instead
                tranche.current_balance = (tranche.current_balance or Decimal('0')) + interest_due
                return Decimal('0')  # No cash payment
            
            return interest_due
        
        return super().calculate_payment_amount(step, tranche)
    
    def _is_pik_elected(self, tranche: CLOTranche) -> bool:
        """Check if PIK has been elected for this tranche"""
        # Implementation would check PIK election records
        # For now, assume based on cash availability
        return self.calculator.available_cash < self.calculator._calculate_interest_due(tranche)


class EquityClawBackWaterfall(TraditionalWaterfall):
    """
    Equity claw-back waterfall
    Equity distributions subject to claw-back if performance hurdles not met
    """
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Equity claw-back calculation"""
        if step == WaterfallStep.RESIDUAL_EQUITY:
            # Check if equity hurdle has been met
            if self._equity_hurdle_met():
                return self.calculator.available_cash
            else:
                # Hold equity in escrow account
                return Decimal('0')
        
        return super().calculate_payment_amount(step, tranche)
    
    def _equity_hurdle_met(self) -> bool:
        """Check if equity return hurdle has been satisfied"""
        # Implementation would calculate IRR and compare to hurdle
        return True  # Placeholder


class CallProtectionWaterfall(TraditionalWaterfall):
    """
    Call protection waterfall with step-down provisions
    Different payment logic during call protection period
    """
    
    def get_payment_phase(self) -> PaymentPhase:
        """Enhanced phase detection with call protection"""
        deal = self.calculator.session.query(self.calculator.deal_id).first()
        
        if self.payment_date < deal.no_call_date:
            return PaymentPhase.CALL_PROTECTION
        elif self.payment_date < deal.reinvestment_end_date:
            return PaymentPhase.REINVESTMENT
        else:
            return PaymentPhase.CALL_PERIOD
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Call protection trigger logic"""
        phase = self.get_payment_phase()
        
        if phase == PaymentPhase.CALL_PROTECTION and 'PRINCIPAL' in step.value:
            # During call protection, principal payments may be restricted
            return self._call_protection_allows_principal_payment(tranche)
        
        return super().check_payment_triggers(step, tranche)
    
    def _call_protection_allows_principal_payment(self, tranche: Optional[CLOTranche]) -> bool:
        """Check call protection provisions"""
        # Implementation would check call protection terms
        return False  # Conservative assumption during call protection


class WaterfallStrategyFactory:
    """
    Factory for creating waterfall strategy instances
    Maps waterfall types to implementation classes
    """
    
    _strategies = {
        WaterfallType.TRADITIONAL: TraditionalWaterfall,
        WaterfallType.TURBO: TurboWaterfall,
        WaterfallType.PIK_TOGGLE: PIKToggleWaterfall,
        WaterfallType.EQUITY_CLAW_BACK: EquityClawBackWaterfall,
        WaterfallType.CALL_PROTECTION: CallProtectionWaterfall,
    }
    
    @classmethod
    def create_strategy(cls, waterfall_type: WaterfallType, calculator: WaterfallCalculator) -> BaseWaterfallStrategy:
        """Create waterfall strategy instance"""
        strategy_class = cls._strategies.get(waterfall_type, TraditionalWaterfall)
        return strategy_class(calculator)
    
    @classmethod
    def register_custom_strategy(cls, waterfall_type: WaterfallType, strategy_class: type):
        """Register custom waterfall strategy"""
        cls._strategies[waterfall_type] = strategy_class
    
    @classmethod
    def get_available_types(cls) -> List[WaterfallType]:
        """Get list of available waterfall types"""
        return list(cls._strategies.keys())


class EnhancedWaterfallCalculator(WaterfallCalculator):
    """
    Enhanced waterfall calculator with pluggable strategies
    Extends base calculator to support multiple waterfall types
    """
    
    def __init__(self, deal_id: str, payment_date: date, session, waterfall_type: WaterfallType = WaterfallType.TRADITIONAL):
        super().__init__(deal_id, payment_date, session)
        self.waterfall_type = waterfall_type
        self.strategy = WaterfallStrategyFactory.create_strategy(waterfall_type, self)
    
    def execute_waterfall(self, collection_amount: Decimal, beginning_cash: Decimal = Decimal('0')) -> WaterfallExecution:
        """Execute waterfall using configured strategy"""
        self.available_cash = collection_amount + beginning_cash
        
        # Create execution record
        execution = self._create_execution_record(collection_amount, beginning_cash)
        
        try:
            # Use strategy-specific waterfall processing
            self.strategy.process_waterfall(execution)
            
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
    
    def _create_execution_record(self, collection_amount: Decimal, beginning_cash: Decimal) -> WaterfallExecution:
        """Create base execution record"""
        from .waterfall import WaterfallExecution
        
        return WaterfallExecution(
            deal_id=self.deal_id,
            payment_date=self.payment_date,
            config_id=self.config.config_id if self.config else None,
            collection_amount=collection_amount,
            beginning_cash=beginning_cash,
            total_available=collection_amount + beginning_cash,
            execution_status='PENDING'
        )