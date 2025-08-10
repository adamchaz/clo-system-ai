"""
Trigger-Aware Waterfall Strategy
Enhanced waterfall implementation that integrates OC/IC trigger calculations
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from .waterfall import WaterfallStep, PaymentPriority
from .dynamic_waterfall import DynamicWaterfallStrategy
from ..services.trigger_service import TriggerService, TriggerCalculationResult


class TriggerAwareWaterfallStrategy(DynamicWaterfallStrategy):
    """
    Waterfall strategy that integrates OC/IC trigger calculations
    Extends DynamicWaterfallStrategy with trigger-aware payment logic
    """
    
    def __init__(self, calculator, trigger_service: TriggerService, deal_id: str):
        """
        Initialize trigger-aware waterfall strategy
        
        Args:
            calculator: Waterfall calculator instance
            trigger_service: Trigger service for OC/IC calculations
            deal_id: CLO deal identifier
        """
        super().__init__(calculator)
        self.trigger_service = trigger_service
        self.deal_id = deal_id
        self.current_trigger_results: Optional[TriggerCalculationResult] = None
        
    def execute_waterfall(self, collection_amount: Decimal, period: int = 1,
                         collateral_balance: Decimal = Decimal('0'),
                         liability_balances: Optional[Dict[str, Decimal]] = None,
                         interest_due_by_tranche: Optional[Dict[str, Decimal]] = None) -> Dict[str, Any]:
        """
        Execute waterfall with trigger-aware payment logic
        
        Args:
            collection_amount: Total cash available for distribution
            period: Payment period number
            collateral_balance: Current collateral balance for OC calculations
            liability_balances: Current liability balances by tranche
            interest_due_by_tranche: Interest due amounts by tranche
            
        Returns:
            Waterfall execution results with trigger integration
        """
        # Initialize defaults
        if liability_balances is None:
            liability_balances = {}
        if interest_due_by_tranche is None:
            interest_due_by_tranche = {}
        
        # Calculate triggers before waterfall execution
        self.current_trigger_results = self.trigger_service.calculate_triggers(
            deal_id=self.deal_id,
            period=period,
            collateral_balance=collateral_balance,
            liability_balances=liability_balances,
            interest_collections=collection_amount,  # Simplified assumption
            interest_due_by_tranche=interest_due_by_tranche
        )
        
        # Execute base waterfall with trigger context
        execution_result = super().execute_waterfall(collection_amount)
        
        # Enhance results with trigger information
        execution_result['trigger_results'] = {
            'period': period,
            'oc_results': self.current_trigger_results.oc_results,
            'ic_results': self.current_trigger_results.ic_results,
            'all_oc_pass': self.current_trigger_results.all_oc_pass,
            'all_ic_pass': self.current_trigger_results.all_ic_pass,
            'total_oc_cure_needed': float(self.current_trigger_results.total_oc_cure_needed),
            'total_ic_cure_needed': float(self.current_trigger_results.total_ic_cure_needed)
        }
        
        # Save trigger results to database
        self.trigger_service.save_trigger_results_to_db(self.deal_id, period)
        
        # Rollforward triggers for next period
        self.trigger_service.rollforward_all_triggers()
        
        return execution_result
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: str) -> bool:
        """
        Enhanced trigger checking with real OC/IC integration
        Overrides base implementation to use actual trigger calculations
        
        Args:
            step: Waterfall payment step
            tranche: Target tranche name
            
        Returns:
            True if payment should proceed, False if blocked by triggers
        """
        if not self.current_trigger_results:
            return True  # No trigger results available, allow payment
        
        # Get trigger context for this tranche
        trigger_context = self.trigger_service.get_trigger_context_for_waterfall(tranche)
        
        # Principal payment trigger logic
        if 'PRINCIPAL' in step.value:
            # Principal payments blocked if OC or IC tests fail
            oc_pass = trigger_context.get('oc_test_pass', True)
            ic_pass = trigger_context.get('ic_test_pass', True)
            
            if not (oc_pass and ic_pass):
                return False  # Block principal payment
        
        # Interest payment trigger logic (generally not blocked, but could defer)
        if 'INTEREST' in step.value:
            # Interest payments generally proceed even if tests fail
            # But might be deferred in certain structures
            return True
        
        # Fee payment trigger logic
        if 'FEES' in step.value:
            # Management fees might be deferred if tests fail
            ic_pass = trigger_context.get('ic_test_pass', True)
            if step == WaterfallStep.JUNIOR_MGMT_FEES and not ic_pass:
                return False  # Defer junior management fees
        
        # Reserve funding trigger logic
        if step == WaterfallStep.INTEREST_RESERVE:
            # Reserve funding might be prioritized if tests fail
            return True
        
        # Default: allow payment
        return True
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: str) -> Decimal:
        """
        Enhanced payment calculation with cure amount integration
        
        Args:
            step: Waterfall payment step
            tranche: Target tranche name
            
        Returns:
            Payment amount including any cure requirements
        """
        # Get base payment amount
        base_amount = super().calculate_payment_amount(step, tranche)
        
        if not self.current_trigger_results:
            return base_amount
        
        # Add cure amounts for specific steps
        cure_amount = Decimal('0')
        
        # OC cure payments
        if step.value == "OC_INTEREST_CURE":
            oc_result = self.current_trigger_results.oc_results.get(tranche, {})
            cure_amount = Decimal(str(oc_result.get('interest_cure_needed', 0)))
        
        elif step.value == "OC_PRINCIPAL_CURE":
            oc_result = self.current_trigger_results.oc_results.get(tranche, {})
            cure_amount = Decimal(str(oc_result.get('principal_cure_needed', 0)))
        
        # IC cure payments
        elif step.value == "IC_CURE":
            ic_result = self.current_trigger_results.ic_results.get(tranche, {})
            cure_amount = Decimal(str(ic_result.get('cure_needed', 0)))
        
        return base_amount + cure_amount
    
    def get_enhanced_payment_sequence(self) -> List[WaterfallStep]:
        """
        Get payment sequence enhanced with cure payment steps
        
        Returns:
            Enhanced payment sequence including cure steps
        """
        # Base sequence from parent
        base_sequence = super().get_payment_sequence()
        
        # Insert cure payment steps at appropriate positions
        enhanced_sequence = []
        
        for step in base_sequence:
            enhanced_sequence.append(step)
            
            # Insert cure steps after interest payments
            if 'INTEREST' in step.value:
                # Add IC cure after interest payments
                enhanced_sequence.append(WaterfallStep("IC_CURE"))
            
            # Insert OC cures after principal payments
            if 'PRINCIPAL' in step.value:
                # Add OC cures after principal payments  
                enhanced_sequence.append(WaterfallStep("OC_INTEREST_CURE"))
                enhanced_sequence.append(WaterfallStep("OC_PRINCIPAL_CURE"))
        
        return enhanced_sequence
    
    def apply_payment_to_triggers(self, step: WaterfallStep, tranche: str, 
                                amount: Decimal) -> Decimal:
        """
        Apply payment amount to trigger cure requirements
        
        Args:
            step: Waterfall payment step
            tranche: Target tranche name
            amount: Payment amount
            
        Returns:
            Unused amount after applying to cures
        """
        if not self.current_trigger_results:
            return amount
        
        unused_amounts = {}
        
        # Apply cure payments based on step type
        if step.value == "IC_CURE":
            unused_amounts = self.trigger_service.apply_cure_payments(
                tranche_name=tranche,
                ic_cure=amount
            )
            return unused_amounts.get('ic', amount)
        
        elif step.value == "OC_INTEREST_CURE":
            unused_amounts = self.trigger_service.apply_cure_payments(
                tranche_name=tranche,
                oc_interest_cure=amount
            )
            return unused_amounts.get('oc_interest', amount)
        
        elif step.value == "OC_PRINCIPAL_CURE":
            unused_amounts = self.trigger_service.apply_cure_payments(
                tranche_name=tranche,
                oc_principal_cure=amount
            )
            return unused_amounts.get('oc_principal', amount)
        
        # For regular payments, check if they should be applied as cures
        elif 'INTEREST' in step.value and tranche in self.current_trigger_results.ic_results:
            ic_result = self.current_trigger_results.ic_results[tranche]
            if not ic_result.get('pass', True):
                # Apply interest payment as IC cure
                unused_amounts = self.trigger_service.apply_cure_payments(
                    tranche_name=tranche,
                    ic_cure=amount
                )
                return unused_amounts.get('ic', amount)
        
        elif 'PRINCIPAL' in step.value and tranche in self.current_trigger_results.oc_results:
            oc_result = self.current_trigger_results.oc_results[tranche]
            if not oc_result.get('pass', True):
                # Apply principal payment as OC cure
                unused_amounts = self.trigger_service.apply_cure_payments(
                    tranche_name=tranche,
                    oc_principal_cure=amount
                )
                return unused_amounts.get('oc_principal', amount)
        
        return amount  # No cure application needed
    
    def get_trigger_status_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive trigger status summary
        
        Returns:
            Summary of all trigger test results and cure requirements
        """
        if not self.current_trigger_results:
            return {"trigger_calculations": "not_available"}
        
        return {
            "period": self.current_trigger_results.period,
            "overall_status": {
                "all_oc_tests_pass": self.current_trigger_results.all_oc_pass,
                "all_ic_tests_pass": self.current_trigger_results.all_ic_pass,
                "total_oc_cure_needed": float(self.current_trigger_results.total_oc_cure_needed),
                "total_ic_cure_needed": float(self.current_trigger_results.total_ic_cure_needed)
            },
            "by_tranche": {
                "oc_tests": self.current_trigger_results.oc_results,
                "ic_tests": self.current_trigger_results.ic_results
            },
            "comprehensive_report": self.trigger_service.get_comprehensive_trigger_report(self.deal_id)
        }
    
    def simulate_cure_scenarios(self, cure_amounts: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """
        Simulate different cure payment scenarios
        
        Args:
            cure_amounts: Cure amounts by tranche and type
                         Format: {tranche: {'oc_interest': amount, 'oc_principal': amount, 'ic': amount}}
        
        Returns:
            Simulation results showing impact of different cure strategies
        """
        scenarios = {}
        
        for scenario_name, tranche_cures in cure_amounts.items():
            scenario_result = {
                "scenario_name": scenario_name,
                "cures_applied": {},
                "remaining_cures": {},
                "test_status_after": {}
            }
            
            # Apply cures for this scenario
            for tranche, cure_types in tranche_cures.items():
                oc_interest = cure_types.get('oc_interest', Decimal('0'))
                oc_principal = cure_types.get('oc_principal', Decimal('0'))
                ic_cure = cure_types.get('ic', Decimal('0'))
                
                unused = self.trigger_service.apply_cure_payments(
                    tranche_name=tranche,
                    oc_interest_cure=oc_interest,
                    oc_principal_cure=oc_principal,
                    ic_cure=ic_cure
                )
                
                scenario_result["cures_applied"][tranche] = {
                    "oc_interest": float(oc_interest - unused.get('oc_interest', Decimal('0'))),
                    "oc_principal": float(oc_principal - unused.get('oc_principal', Decimal('0'))),
                    "ic": float(ic_cure - unused.get('ic', Decimal('0')))
                }
                
                scenario_result["remaining_cures"][tranche] = {
                    "oc_interest": float(unused.get('oc_interest', Decimal('0'))),
                    "oc_principal": float(unused.get('oc_principal', Decimal('0'))),
                    "ic": float(unused.get('ic', Decimal('0')))
                }
            
            # Get post-cure trigger status
            scenario_result["test_status_after"] = self.trigger_service.get_trigger_context_for_waterfall()
            scenarios[scenario_name] = scenario_result
        
        return scenarios