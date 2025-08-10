"""
Trigger Service - Integration layer for OC/IC triggers with waterfall system
Manages trigger calculations and integration with payment waterfall logic
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from ..models.oc_trigger import OCTrigger, OCTriggerCalculator
from ..models.ic_trigger import ICTrigger, ICTriggerCalculator
from ..models.clo_deal import CLODeal
from ..models.liability import Liability
from ..models.asset import Asset


class TriggerCalculationResult:
    """Result of trigger calculations for a period"""
    
    def __init__(self):
        self.period: int = 0
        self.oc_results: Dict[str, Any] = {}  # By tranche name
        self.ic_results: Dict[str, Any] = {}  # By tranche name
        self.all_oc_pass: bool = True
        self.all_ic_pass: bool = True
        self.total_oc_cure_needed: Decimal = Decimal('0')
        self.total_ic_cure_needed: Decimal = Decimal('0')


class TriggerService:
    """
    Service class for managing OC/IC trigger calculations and waterfall integration
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.oc_calculators: Dict[str, OCTriggerCalculator] = {}  # By tranche name
        self.ic_calculators: Dict[str, ICTriggerCalculator] = {}  # By tranche name
    
    def setup_deal_triggers(self, deal_id: str, num_periods: int) -> None:
        """
        Setup OC/IC trigger calculators for a deal
        
        Args:
            deal_id: CLO deal identifier
            num_periods: Number of payment periods
        """
        # Get deal and tranches
        deal = self.session.query(CLODeal).filter_by(deal_id=deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Setup calculators for each tranche
        for tranche in deal.tranches:
            # OC Trigger setup (example thresholds - would come from deal configuration)
            oc_threshold = self._get_oc_threshold(tranche.tranche_name)
            oc_calculator = OCTriggerCalculator(
                name=f"{tranche.tranche_name} OC",
                threshold=oc_threshold
            )
            oc_calculator.setup_deal(num_periods)
            self.oc_calculators[tranche.tranche_name] = oc_calculator
            
            # IC Trigger setup
            ic_threshold = self._get_ic_threshold(tranche.tranche_name)
            ic_calculator = ICTriggerCalculator(
                name=f"{tranche.tranche_name} IC", 
                threshold=ic_threshold
            )
            ic_calculator.setup_deal(num_periods)
            self.ic_calculators[tranche.tranche_name] = ic_calculator
    
    def calculate_triggers(self, deal_id: str, period: int, 
                         collateral_balance: Decimal,
                         liability_balances: Dict[str, Decimal],
                         interest_collections: Decimal,
                         interest_due_by_tranche: Dict[str, Decimal]) -> TriggerCalculationResult:
        """
        Calculate OC/IC triggers for a specific period
        
        Args:
            deal_id: CLO deal identifier
            period: Payment period number
            collateral_balance: Total collateral par amount
            liability_balances: Current balance by tranche name
            interest_collections: Total interest collections for period
            interest_due_by_tranche: Interest due by tranche name
            
        Returns:
            TriggerCalculationResult with all calculation results
        """
        result = TriggerCalculationResult()
        result.period = period
        
        # Calculate OC triggers for each tranche
        for tranche_name, calculator in self.oc_calculators.items():
            if tranche_name in liability_balances:
                liability_balance = liability_balances[tranche_name]
                
                # Calculate OC ratio: collateral / liability
                oc_pass = calculator.calculate(collateral_balance, liability_balance)
                
                # Get cure amounts
                interest_cure = calculator.get_interest_cure_amount()
                principal_cure = calculator.get_principal_cure_amount()
                
                result.oc_results[tranche_name] = {
                    'pass': oc_pass,
                    'ratio': float(calculator.get_current_result().calculated_ratio),
                    'threshold': float(calculator.trigger_threshold),
                    'interest_cure_needed': float(interest_cure),
                    'principal_cure_needed': float(principal_cure),
                    'total_cure_needed': float(interest_cure + principal_cure)
                }
                
                result.total_oc_cure_needed += interest_cure + principal_cure
                
                if not oc_pass:
                    result.all_oc_pass = False
        
        # Calculate IC triggers for each tranche
        for tranche_name, calculator in self.ic_calculators.items():
            if tranche_name in liability_balances and tranche_name in interest_due_by_tranche:
                liability_balance = liability_balances[tranche_name]
                interest_due = interest_due_by_tranche[tranche_name]
                
                # Calculate IC ratio: collections / due (simplified - would need proper allocation)
                ic_pass = calculator.calculate(interest_collections, interest_due, liability_balance)
                
                # Get cure amount
                cure_needed = calculator.get_cure_amount()
                
                result.ic_results[tranche_name] = {
                    'pass': ic_pass,
                    'ratio': float(calculator.get_current_result().calculated_ratio),
                    'threshold': float(calculator.trigger_threshold),
                    'cure_needed': float(cure_needed)
                }
                
                result.total_ic_cure_needed += cure_needed
                
                if not ic_pass:
                    result.all_ic_pass = False
        
        return result
    
    def apply_cure_payments(self, tranche_name: str, 
                          oc_interest_cure: Decimal = Decimal('0'),
                          oc_principal_cure: Decimal = Decimal('0'),
                          ic_cure: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """
        Apply cure payments to triggers
        
        Args:
            tranche_name: Target tranche name
            oc_interest_cure: OC interest cure payment
            oc_principal_cure: OC principal cure payment  
            ic_cure: IC cure payment
            
        Returns:
            Dictionary with unused amounts by cure type
        """
        unused_amounts = {}
        
        # Apply OC cures
        if tranche_name in self.oc_calculators:
            oc_calc = self.oc_calculators[tranche_name]
            
            # Apply interest cure
            if oc_interest_cure > 0:
                unused_amounts['oc_interest'] = oc_calc.pay_interest(oc_interest_cure)
            
            # Apply principal cure
            if oc_principal_cure > 0:
                unused_amounts['oc_principal'] = oc_calc.pay_principal(oc_principal_cure)
        
        # Apply IC cure
        if tranche_name in self.ic_calculators and ic_cure > 0:
            ic_calc = self.ic_calculators[tranche_name]
            unused_amounts['ic'] = ic_calc.pay_cure(ic_cure)
        
        return unused_amounts
    
    def get_trigger_context_for_waterfall(self, tranche_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get trigger context for waterfall payment decisions
        
        Args:
            tranche_name: Specific tranche (if None, returns all)
            
        Returns:
            Dictionary with trigger test results for waterfall logic
        """
        context = {}
        
        if tranche_name:
            # Single tranche context
            if tranche_name in self.oc_calculators:
                context['oc_test_pass'] = self.oc_calculators[tranche_name].get_pass_fail()
                context['oc_interest_cure_needed'] = float(self.oc_calculators[tranche_name].get_interest_cure_amount())
                context['oc_principal_cure_needed'] = float(self.oc_calculators[tranche_name].get_principal_cure_amount())
            
            if tranche_name in self.ic_calculators:
                context['ic_test_pass'] = self.ic_calculators[tranche_name].get_pass_fail()
                context['ic_cure_needed'] = float(self.ic_calculators[tranche_name].get_cure_amount())
        else:
            # All tranches context
            context['oc_tests'] = {}
            context['ic_tests'] = {}
            
            for tranche, calc in self.oc_calculators.items():
                context['oc_tests'][tranche] = {
                    'pass': calc.get_pass_fail(),
                    'interest_cure_needed': float(calc.get_interest_cure_amount()),
                    'principal_cure_needed': float(calc.get_principal_cure_amount())
                }
            
            for tranche, calc in self.ic_calculators.items():
                context['ic_tests'][tranche] = {
                    'pass': calc.get_pass_fail(),
                    'cure_needed': float(calc.get_cure_amount())
                }
            
            # Overall pass/fail
            context['all_oc_pass'] = all(calc.get_pass_fail() for calc in self.oc_calculators.values())
            context['all_ic_pass'] = all(calc.get_pass_fail() for calc in self.ic_calculators.values())
        
        return context
    
    def rollforward_all_triggers(self):
        """Rollforward all trigger calculators to next period"""
        for calculator in self.oc_calculators.values():
            calculator.rollforward()
        
        for calculator in self.ic_calculators.values():
            calculator.rollforward()
    
    def save_trigger_results_to_db(self, deal_id: str, period: int) -> None:
        """
        Save current trigger calculation results to database
        
        Args:
            deal_id: CLO deal identifier
            period: Payment period number
        """
        # Save OC trigger results
        for tranche_name, calculator in self.oc_calculators.items():
            current_result = calculator.get_current_result()
            
            oc_trigger = OCTrigger(
                deal_id=deal_id,
                tranche_name=tranche_name,
                trigger_name=calculator.name,
                oc_threshold=calculator.trigger_threshold,
                period_number=period,
                numerator=current_result.numerator,
                denominator=current_result.denominator,
                calculated_ratio=current_result.calculated_ratio,
                pass_fail=current_result.pass_fail,
                interest_cure_amount=current_result.interest_cure_amount,
                principal_cure_amount=current_result.principal_cure_amount,
                prior_interest_cure=current_result.prior_interest_cure,
                prior_principal_cure=current_result.prior_principal_cure,
                interest_cure_paid=current_result.interest_cure_paid,
                principal_cure_paid=current_result.principal_cure_paid
            )
            
            self.session.add(oc_trigger)
        
        # Save IC trigger results
        for tranche_name, calculator in self.ic_calculators.items():
            current_result = calculator.get_current_result()
            
            ic_trigger = ICTrigger(
                deal_id=deal_id,
                tranche_name=tranche_name,
                trigger_name=calculator.name,
                ic_threshold=calculator.trigger_threshold,
                period_number=period,
                numerator=current_result.numerator,
                denominator=current_result.denominator,
                liability_balance=current_result.liability_balance,
                calculated_ratio=current_result.calculated_ratio,
                pass_fail=current_result.pass_fail,
                cure_amount=current_result.cure_amount,
                prior_cure_payments=current_result.prior_cure_payments,
                cure_amount_paid=current_result.cure_amount_paid
            )
            
            self.session.add(ic_trigger)
        
        self.session.commit()
    
    def load_trigger_results_from_db(self, deal_id: str, period: int) -> bool:
        """
        Load trigger results from database for a specific period
        
        Args:
            deal_id: CLO deal identifier
            period: Payment period number
            
        Returns:
            True if results were found and loaded, False otherwise
        """
        # Load OC triggers
        oc_triggers = self.session.query(OCTrigger)\
            .filter_by(deal_id=deal_id, period_number=period)\
            .all()
        
        if not oc_triggers:
            return False
        
        for oc_trigger in oc_triggers:
            if oc_trigger.tranche_name in self.oc_calculators:
                calculator = self.oc_calculators[oc_trigger.tranche_name]
                # Load the result into calculator (simplified - would need full state restoration)
                calculator.period_results[period] = calculator.get_current_result()
        
        # Load IC triggers
        ic_triggers = self.session.query(ICTrigger)\
            .filter_by(deal_id=deal_id, period_number=period)\
            .all()
        
        for ic_trigger in ic_triggers:
            if ic_trigger.tranche_name in self.ic_calculators:
                calculator = self.ic_calculators[ic_trigger.tranche_name]
                # Load the result into calculator (simplified - would need full state restoration)
                calculator.period_results[period] = calculator.get_current_result()
        
        return True
    
    def get_comprehensive_trigger_report(self, deal_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive trigger report for all periods
        
        Returns:
            Detailed report with all trigger calculations and trends
        """
        report = {
            'deal_id': deal_id,
            'oc_triggers': {},
            'ic_triggers': {},
            'summary': {}
        }
        
        # OC trigger report
        for tranche_name, calculator in self.oc_calculators.items():
            report['oc_triggers'][tranche_name] = {
                'threshold': float(calculator.trigger_threshold),
                'periods': calculator.get_output(),
                'current_status': calculator.get_cure_status_summary()
            }
        
        # IC trigger report  
        for tranche_name, calculator in self.ic_calculators.items():
            report['ic_triggers'][tranche_name] = {
                'threshold': float(calculator.trigger_threshold),
                'periods': calculator.get_output(),
                'current_status': calculator.get_cure_status_summary()
            }
        
        # Summary statistics
        report['summary'] = {
            'periods_calculated': max(calc.last_period_calculated for calc in self.oc_calculators.values()) if self.oc_calculators else 0,
            'oc_tests_passing': sum(1 for calc in self.oc_calculators.values() if calc.get_pass_fail()),
            'ic_tests_passing': sum(1 for calc in self.ic_calculators.values() if calc.get_pass_fail()),
            'total_oc_cure_outstanding': sum(calc.get_interest_cure_amount() + calc.get_principal_cure_amount() 
                                           for calc in self.oc_calculators.values()),
            'total_ic_cure_outstanding': sum(calc.get_cure_amount() for calc in self.ic_calculators.values())
        }
        
        return report
    
    def _get_oc_threshold(self, tranche_name: str) -> Decimal:
        """Get OC threshold for tranche (would come from deal configuration)"""
        # Default thresholds by tranche seniority
        thresholds = {
            'Class A': Decimal('1.20'),  # 120%
            'Class B': Decimal('1.15'),  # 115%
            'Class C': Decimal('1.10'),  # 110%
            'Class D': Decimal('1.05'),  # 105%
            'Class E': Decimal('1.00'),  # 100%
        }
        return thresholds.get(tranche_name, Decimal('1.10'))
    
    def _get_ic_threshold(self, tranche_name: str) -> Decimal:
        """Get IC threshold for tranche (would come from deal configuration)"""
        # Default thresholds by tranche seniority
        thresholds = {
            'Class A': Decimal('1.10'),  # 110%
            'Class B': Decimal('1.05'),  # 105%
            'Class C': Decimal('1.00'),  # 100%
            'Class D': Decimal('1.00'),  # 100%
            'Class E': Decimal('1.00'),  # 100%
        }
        return thresholds.get(tranche_name, Decimal('1.00'))