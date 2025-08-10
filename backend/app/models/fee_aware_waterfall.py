"""
Fee-Aware Waterfall Strategy
Enhanced waterfall implementation that integrates fee calculations with OC/IC triggers
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from .waterfall import WaterfallStep, PaymentPriority
from .trigger_aware_waterfall import TriggerAwareWaterfallStrategy
from ..services.fee_service import FeeService, FeeCalculationResult
from ..services.trigger_service import TriggerService


class FeeAwareWaterfallStrategy(TriggerAwareWaterfallStrategy):
    """
    Waterfall strategy that integrates both fee calculations and OC/IC triggers
    Extends TriggerAwareWaterfallStrategy with comprehensive fee management
    """
    
    def __init__(self, calculator, trigger_service: TriggerService, fee_service: FeeService, deal_id: str):
        """
        Initialize fee-aware waterfall strategy
        
        Args:
            calculator: Waterfall calculator instance
            trigger_service: Trigger service for OC/IC calculations
            fee_service: Fee service for fee calculations
            deal_id: CLO deal identifier
        """
        super().__init__(calculator, trigger_service, deal_id)
        self.fee_service = fee_service
        self.current_fee_results: Optional[FeeCalculationResult] = None
        
    def execute_waterfall(self, collection_amount: Decimal, period: int = 1,
                         begin_date: Optional[date] = None, end_date: Optional[date] = None,
                         collateral_balance: Decimal = Decimal('0'),
                         liability_balances: Optional[Dict[str, Decimal]] = None,
                         interest_due_by_tranche: Optional[Dict[str, Decimal]] = None,
                         libor_rate: Decimal = Decimal('0')) -> Dict[str, Any]:
        """
        Execute waterfall with integrated fee calculations and trigger evaluation
        
        Args:
            collection_amount: Total cash available for distribution
            period: Payment period number
            begin_date: Period start date (required for fee calculations)
            end_date: Period end date (required for fee calculations)
            collateral_balance: Current collateral balance for OC calculations
            liability_balances: Current liability balances by tranche
            interest_due_by_tranche: Interest due amounts by tranche
            libor_rate: Period LIBOR/SOFR rate for fee calculations
            
        Returns:
            Enhanced waterfall execution results with fee and trigger integration
        """
        # Initialize defaults
        if liability_balances is None:
            liability_balances = {}
        if interest_due_by_tranche is None:
            interest_due_by_tranche = {}
        if begin_date is None:
            raise ValueError("begin_date is required for fee calculations")
        if end_date is None:
            raise ValueError("end_date is required for fee calculations")
        
        # Calculate fees before waterfall execution
        fee_basis_amounts = self._calculate_fee_basis_amounts(liability_balances, collateral_balance)
        
        self.current_fee_results = self.fee_service.calculate_fees(
            deal_id=self.deal_id,
            period=period,
            begin_date=begin_date,
            end_date=end_date,
            fee_basis_amounts=fee_basis_amounts,
            libor_rate=libor_rate
        )
        
        # Execute trigger-aware waterfall (includes trigger calculations)
        execution_result = super().execute_waterfall(
            collection_amount, period, collateral_balance, 
            liability_balances, interest_due_by_tranche
        )
        
        # Enhance results with fee information
        execution_result['fee_results'] = {
            'period': period,
            'fee_calculations': self.current_fee_results.fee_results,
            'total_fees_accrued': float(self.current_fee_results.total_fees_accrued),
            'total_fees_paid': float(self.current_fee_results.total_fees_paid),
            'total_unpaid_balance': float(self.current_fee_results.total_unpaid_balance),
            'fee_basis_amounts': {name: float(amount) for name, amount in fee_basis_amounts.items()}
        }
        
        # Save fee results to database
        self.fee_service.save_fee_results_to_db(self.deal_id, period, begin_date, end_date)
        
        # Rollforward fees for next period
        self.fee_service.rollforward_all_fees()
        
        return execution_result
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: str) -> bool:
        """
        Enhanced trigger checking with fee deferral logic
        
        Args:
            step: Waterfall payment step
            tranche: Target tranche name
            
        Returns:
            True if payment should proceed, False if blocked by triggers or fee logic
        """
        # First check parent trigger logic (OC/IC triggers)
        if not super().check_payment_triggers(step, tranche):
            return False
        
        # Additional fee-specific trigger logic
        if not self.current_fee_results:
            return True
        
        # Block subordinate management fees if IC tests fail
        if step.value == "SUBORDINATE_MGMT_FEES":
            trigger_context = self.trigger_service.get_trigger_context_for_waterfall()
            if not trigger_context.get('all_ic_pass', True):
                return False  # Defer subordinate management fees
        
        # Allow all other payments to proceed
        return True
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: str) -> Decimal:
        """
        Enhanced payment calculation with fee payment amounts
        
        Args:
            step: Waterfall payment step
            tranche: Target tranche name
            
        Returns:
            Payment amount including fee requirements
        """
        # Get base amount from parent (includes trigger cure amounts)
        base_amount = super().calculate_payment_amount(step, tranche)
        
        if not self.current_fee_results:
            return base_amount
        
        # Add fee amounts for specific steps
        fee_amount = Decimal('0')
        
        if step.value == "SENIOR_MGMT_FEES":
            fee_result = self.current_fee_results.fee_results.get("Senior Management Fee")
            if fee_result:
                fee_amount = Decimal(str(fee_result.get('unpaid_balance', 0)))
        
        elif step.value == "SUBORDINATE_MGMT_FEES":
            fee_result = self.current_fee_results.fee_results.get("Subordinate Management Fee")
            if fee_result:
                fee_amount = Decimal(str(fee_result.get('unpaid_balance', 0)))
        
        elif step.value == "TRUSTEE_FEES":
            fee_result = self.current_fee_results.fee_results.get("Trustee Fee")
            if fee_result:
                fee_amount = Decimal(str(fee_result.get('unpaid_balance', 0)))
        
        elif step.value == "ADMINISTRATIVE_FEES":
            # Sum all administrative fees
            for fee_name, fee_result in self.current_fee_results.fee_results.items():
                if "Administrative" in fee_name or "Admin" in fee_name:
                    fee_amount += Decimal(str(fee_result.get('unpaid_balance', 0)))
        
        return base_amount + fee_amount
    
    def get_enhanced_payment_sequence(self) -> List[WaterfallStep]:
        """
        Get payment sequence enhanced with fee payment steps
        
        Returns:
            Enhanced payment sequence including fee steps
        """
        # Start with trigger-enhanced sequence from parent
        enhanced_sequence = super().get_enhanced_payment_sequence()
        
        # Insert fee payment steps at appropriate positions
        final_sequence = []
        
        for step in enhanced_sequence:
            final_sequence.append(step)
            
            # Insert fee steps after expense payments
            if step.value == "SENIOR_EXPENSES":
                # Add fee payments in priority order
                final_sequence.append(WaterfallStep("TRUSTEE_FEES"))
                final_sequence.append(WaterfallStep("ADMINISTRATIVE_FEES"))
                final_sequence.append(WaterfallStep("SENIOR_MGMT_FEES"))
            
            # Insert subordinate management fees after interest payments
            if 'INTEREST' in step.value and step == enhanced_sequence[-1]:  # Last interest step
                # Check if subordinate fees should be deferred
                trigger_context = self.trigger_service.get_trigger_context_for_waterfall()
                if trigger_context.get('all_ic_pass', True):
                    final_sequence.append(WaterfallStep("SUBORDINATE_MGMT_FEES"))
        
        return final_sequence
    
    def apply_payment_to_fees(self, step: WaterfallStep, amount: Decimal) -> Decimal:
        """
        Apply payment amount to fee requirements
        
        Args:
            step: Waterfall payment step
            amount: Payment amount
            
        Returns:
            Unused amount after applying to fees
        """
        if not self.current_fee_results:
            return amount
        
        fee_payments = {}
        
        # Determine which fees to pay based on step
        if step.value == "SENIOR_MGMT_FEES":
            fee_payments["Senior Management Fee"] = amount
        elif step.value == "SUBORDINATE_MGMT_FEES":
            fee_payments["Subordinate Management Fee"] = amount
        elif step.value == "TRUSTEE_FEES":
            fee_payments["Trustee Fee"] = amount
        elif step.value == "ADMINISTRATIVE_FEES":
            # Distribute among all administrative fees proportionally
            admin_fees = {name: result for name, result in self.current_fee_results.fee_results.items()
                         if "Administrative" in name or "Admin" in name}
            
            if admin_fees:
                total_admin_due = sum(Decimal(str(result.get('unpaid_balance', 0))) 
                                    for result in admin_fees.values())
                
                if total_admin_due > 0:
                    for fee_name, fee_result in admin_fees.items():
                        fee_due = Decimal(str(fee_result.get('unpaid_balance', 0)))
                        fee_allocation = amount * fee_due / total_admin_due
                        fee_payments[fee_name] = fee_allocation
        
        if fee_payments:
            unused_amounts = self.fee_service.apply_fee_payments(fee_payments)
            return sum(unused_amounts.values())
        
        return amount
    
    def get_comprehensive_status_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive status summary including fees and triggers
        
        Returns:
            Complete summary of fee calculations, trigger results, and waterfall status
        """
        # Get trigger status from parent
        status_summary = super().get_trigger_status_summary()
        
        # Add fee information
        if self.current_fee_results:
            status_summary['fee_status'] = {
                'period': self.current_fee_results.period,
                'total_fees_accrued': float(self.current_fee_results.total_fees_accrued),
                'total_unpaid_balance': float(self.current_fee_results.total_unpaid_balance),
                'fee_calculations': self.current_fee_results.fee_results
            }
            
            # Add fee payment requirements
            fee_requirements = self.fee_service.get_fee_payment_requirements()
            status_summary['fee_payment_requirements'] = fee_requirements
        
        # Add comprehensive reports
        if hasattr(self.fee_service, 'get_comprehensive_fee_report'):
            status_summary['comprehensive_fee_report'] = self.fee_service.get_comprehensive_fee_report(self.deal_id)
        
        return status_summary
    
    def simulate_fee_and_trigger_scenarios(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate different fee payment and trigger cure scenarios
        
        Args:
            scenarios: Scenario definitions including fee payments and trigger cures
            
        Returns:
            Simulation results showing impact of different strategies
        """
        simulation_results = {}
        
        for scenario_name, scenario_data in scenarios.items():
            scenario_result = {
                "scenario_name": scenario_name,
                "fee_payments": scenario_data.get('fee_payments', {}),
                "trigger_cures": scenario_data.get('trigger_cures', {}),
                "results": {}
            }
            
            # Apply fee payments if provided
            fee_payments = scenario_data.get('fee_payments', {})
            if fee_payments:
                unused_fee_amounts = self.fee_service.apply_fee_payments(fee_payments)
                scenario_result['unused_fee_amounts'] = unused_fee_amounts
            
            # Apply trigger cures if provided (from parent class)
            trigger_cures = scenario_data.get('trigger_cures', {})
            if trigger_cures:
                trigger_unused = super().simulate_cure_scenarios({scenario_name: trigger_cures})
                scenario_result['trigger_results'] = trigger_unused[scenario_name]
            
            # Get post-scenario status
            scenario_result['post_scenario_status'] = {
                'fee_requirements': self.fee_service.get_fee_payment_requirements(),
                'trigger_context': self.trigger_service.get_trigger_context_for_waterfall()
            }
            
            simulation_results[scenario_name] = scenario_result
        
        return simulation_results
    
    def _calculate_fee_basis_amounts(self, liability_balances: Dict[str, Decimal], 
                                   collateral_balance: Decimal) -> Dict[str, Decimal]:
        """
        Calculate fee basis amounts based on fee types and current balances
        
        Args:
            liability_balances: Current liability balances by tranche
            collateral_balance: Current collateral balance
            
        Returns:
            Fee basis amounts by fee name
        """
        fee_basis_amounts = {}
        
        # Get fee basis requirements
        fee_requirements = self.fee_service.get_fee_basis_requirements()
        
        # Total liability balance for percentage-based fees
        total_liability_balance = sum(liability_balances.values())
        
        for fee_name, basis_type in fee_requirements.items():
            if basis_type == "beginning_balance" or basis_type == "average_balance":
                # Use total liability balance as proxy for fee basis
                # In practice, this might be more sophisticated based on fee configuration
                fee_basis_amounts[fee_name] = total_liability_balance
            elif basis_type == "collateral_balance":
                fee_basis_amounts[fee_name] = collateral_balance
            else:  # fixed_amount
                fee_basis_amounts[fee_name] = Decimal('0')  # Fixed fees don't need basis
        
        return fee_basis_amounts