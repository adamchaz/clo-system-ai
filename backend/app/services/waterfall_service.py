"""
Waterfall Calculation Service
Implements sophisticated waterfall distribution calculations for CLO deals
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import logging

from sqlalchemy.orm import Session
from ..core.database_config import db_config
from ..services.data_integration import DataIntegrationService

logger = logging.getLogger(__name__)

class WaterfallService:
    """Service for waterfall calculations and cash flow projections"""
    
    def __init__(self):
        self.integration_service = DataIntegrationService()
        
    def calculate_waterfall(
        self, 
        deal_id: str,
        payment_date: date,
        available_funds: Decimal,
        principal_collections: Decimal = Decimal(0),
        interest_collections: Decimal = Decimal(0)
    ) -> Dict[str, Any]:
        """
        Calculate waterfall distribution for a payment period
        
        Args:
            deal_id: CLO deal identifier
            payment_date: Payment date for calculation
            available_funds: Total funds available for distribution
            principal_collections: Principal collections for the period
            interest_collections: Interest collections for the period
            
        Returns:
            Comprehensive waterfall calculation results
        """
        logger.info(f"Calculating waterfall for deal {deal_id} on {payment_date}")
        
        try:
            # Get deal configuration and tranches
            deal_config = self._get_deal_configuration(deal_id)
            tranches = self._get_deal_tranches(deal_id)
            
            # Initialize calculation state
            calculation_state = {
                'remaining_funds': available_funds,
                'payment_steps': [],
                'tranche_payments': {},
                'trigger_status': {}
            }
            
            # Execute waterfall sequence
            payment_sequence = self._get_payment_sequence(deal_id)
            
            for step in payment_sequence:
                self._execute_payment_step(
                    step, 
                    calculation_state, 
                    tranches, 
                    deal_config
                )
            
            # Calculate summary metrics
            summary = self._calculate_summary(calculation_state)
            
            return {
                'deal_id': deal_id,
                'payment_date': payment_date,
                'calculation_timestamp': datetime.now(),
                'total_available_funds': available_funds,
                'principal_collections': principal_collections,
                'interest_collections': interest_collections,
                'payment_steps': calculation_state['payment_steps'],
                'tranche_payments': calculation_state['tranche_payments'],
                'trigger_status': calculation_state['trigger_status'],
                **summary
            }
            
        except Exception as e:
            logger.error(f"Waterfall calculation failed for deal {deal_id}: {e}")
            raise
    
    def project_cash_flows(
        self,
        deal_id: str,
        start_date: date,
        end_date: date,
        scenario: str = "base",
        assumptions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate cash flow projections for a CLO deal
        
        Args:
            deal_id: CLO deal identifier
            start_date: Projection start date
            end_date: Projection end date
            scenario: Scenario name for projections
            assumptions: Custom assumptions for projection
            
        Returns:
            Cash flow projection results
        """
        logger.info(f"Projecting cash flows for deal {deal_id} from {start_date} to {end_date}")
        
        try:
            # Get scenario parameters
            scenario_params = self.integration_service.get_scenario_parameters(scenario)
            
            # Generate monthly projections
            monthly_projections = []
            current_date = start_date
            
            while current_date <= end_date:
                projection = self._calculate_monthly_projection(
                    deal_id, 
                    current_date, 
                    scenario_params,
                    assumptions
                )
                monthly_projections.append(projection)
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # Calculate summary statistics
            summary_stats = self._calculate_projection_summary(monthly_projections)
            
            return {
                'deal_id': deal_id,
                'scenario': scenario,
                'projection_date': datetime.now(),
                'start_date': start_date,
                'end_date': end_date,
                'monthly_projections': monthly_projections,
                **summary_stats
            }
            
        except Exception as e:
            logger.error(f"Cash flow projection failed for deal {deal_id}: {e}")
            raise
    
    def run_stress_tests(
        self,
        deal_id: str,
        scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run stress testing scenarios on waterfall calculations
        
        Args:
            deal_id: CLO deal identifier
            scenarios: List of stress test scenarios
            
        Returns:
            List of stress test results
        """
        logger.info(f"Running {len(scenarios)} stress test scenarios for deal {deal_id}")
        
        results = []
        
        try:
            base_waterfall = self._get_base_waterfall(deal_id)
            
            for scenario in scenarios:
                stress_result = self._run_single_stress_test(
                    deal_id, 
                    scenario, 
                    base_waterfall
                )
                results.append(stress_result)
            
            # Sort results by severity (worst case first)
            results.sort(key=lambda x: x.get('portfolio_loss', 0), reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Stress testing failed for deal {deal_id}: {e}")
            raise
    
    def _get_deal_configuration(self, deal_id: str) -> Dict[str, Any]:
        """Get deal configuration from operational database"""
        # Implementation will query operational database
        # For now, return mock configuration
        return {
            'deal_id': deal_id,
            'management_fee_rate': Decimal('0.005'),  # 0.5%
            'trustee_fee_rate': Decimal('0.001'),     # 0.1%
            'senior_expense_cap': Decimal('100000'),
            'reinvestment_period_end': None,
            'triggers_enabled': True
        }
    
    def _get_deal_tranches(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get tranche structure for deal"""
        # Implementation will query operational database
        # For now, return mock tranche structure
        return [
            {
                'tranche_id': 'A1',
                'tranche_name': 'Class A-1 Notes',
                'priority': 1,
                'original_balance': Decimal('200000000'),
                'current_balance': Decimal('180000000'),
                'coupon_rate': Decimal('0.045'),  # 4.5%
                'is_floating_rate': True,
                'spread': Decimal('0.015')  # 150bp over LIBOR
            },
            {
                'tranche_id': 'A2',
                'tranche_name': 'Class A-2 Notes',
                'priority': 2,
                'original_balance': Decimal('150000000'),
                'current_balance': Decimal('135000000'),
                'coupon_rate': Decimal('0.055'),  # 5.5%
                'is_floating_rate': False
            },
            {
                'tranche_id': 'B',
                'tranche_name': 'Class B Notes',
                'priority': 3,
                'original_balance': Decimal('75000000'),
                'current_balance': Decimal('68000000'),
                'coupon_rate': Decimal('0.075'),  # 7.5%
                'is_floating_rate': False
            },
            {
                'tranche_id': 'C',
                'tranche_name': 'Subordinate Notes',
                'priority': 4,
                'original_balance': Decimal('50000000'),
                'current_balance': Decimal('45000000'),
                'coupon_rate': Decimal('0.095'),  # 9.5%
                'is_floating_rate': False
            },
            {
                'tranche_id': 'EQ',
                'tranche_name': 'Equity',
                'priority': 5,
                'original_balance': Decimal('25000000'),
                'current_balance': Decimal('22000000'),
                'coupon_rate': None,
                'is_floating_rate': False
            }
        ]
    
    def _get_payment_sequence(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get payment sequence configuration for deal"""
        return [
            {
                'step': 1,
                'description': 'Management Fees',
                'type': 'fees',
                'priority': 1,
                'calculation_method': 'management_fee'
            },
            {
                'step': 2,
                'description': 'Trustee and Administrative Fees',
                'type': 'fees',
                'priority': 2,
                'calculation_method': 'administrative_fee'
            },
            {
                'step': 3,
                'description': 'Class A-1 Interest',
                'type': 'interest',
                'priority': 3,
                'tranche_id': 'A1'
            },
            {
                'step': 4,
                'description': 'Class A-2 Interest',
                'type': 'interest',
                'priority': 4,
                'tranche_id': 'A2'
            },
            {
                'step': 5,
                'description': 'Class A Principal (Sequential/Pro Rata)',
                'type': 'principal',
                'priority': 5,
                'tranches': ['A1', 'A2'],
                'calculation_method': 'sequential_or_pro_rata'
            },
            {
                'step': 6,
                'description': 'Class B Interest',
                'type': 'interest',
                'priority': 6,
                'tranche_id': 'B'
            },
            {
                'step': 7,
                'description': 'Class C Interest',
                'type': 'interest',
                'priority': 7,
                'tranche_id': 'C'
            },
            {
                'step': 8,
                'description': 'Class B Principal',
                'type': 'principal',
                'priority': 8,
                'tranche_id': 'B'
            },
            {
                'step': 9,
                'description': 'Class C Principal',
                'type': 'principal',
                'priority': 9,
                'tranche_id': 'C'
            },
            {
                'step': 10,
                'description': 'Equity Distribution',
                'type': 'equity',
                'priority': 10,
                'tranche_id': 'EQ'
            }
        ]
    
    def _execute_payment_step(
        self,
        step: Dict[str, Any],
        calculation_state: Dict[str, Any],
        tranches: List[Dict[str, Any]],
        deal_config: Dict[str, Any]
    ) -> None:
        """Execute a single payment step in the waterfall"""
        step_type = step.get('type')
        remaining_funds = calculation_state['remaining_funds']
        
        if remaining_funds <= 0:
            # No funds remaining, record zero payment
            self._record_payment_step(step, Decimal(0), Decimal(0), calculation_state)
            return
        
        if step_type == 'fees':
            payment_amount = self._calculate_fee_payment(step, deal_config, remaining_funds)
        elif step_type == 'interest':
            payment_amount = self._calculate_interest_payment(step, tranches, remaining_funds)
        elif step_type == 'principal':
            payment_amount = self._calculate_principal_payment(step, tranches, remaining_funds)
        elif step_type == 'equity':
            payment_amount = remaining_funds  # Equity gets all remaining funds
        else:
            payment_amount = Decimal(0)
        
        # Ensure payment doesn't exceed available funds
        actual_payment = min(payment_amount, remaining_funds)
        
        # Record payment step
        self._record_payment_step(step, payment_amount, actual_payment, calculation_state)
        
        # Update remaining funds
        calculation_state['remaining_funds'] -= actual_payment
    
    def _calculate_fee_payment(
        self,
        step: Dict[str, Any],
        deal_config: Dict[str, Any],
        available_funds: Decimal
    ) -> Decimal:
        """Calculate fee payment amount"""
        calculation_method = step.get('calculation_method')
        
        if calculation_method == 'management_fee':
            # Simplified: annual fee rate / 12 * portfolio balance
            fee_rate = deal_config.get('management_fee_rate', Decimal('0.005'))
            portfolio_balance = Decimal('450000000')  # Mock portfolio balance
            monthly_fee = portfolio_balance * fee_rate / 12
            return monthly_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        elif calculation_method == 'administrative_fee':
            # Simplified flat fee
            return min(Decimal('25000'), available_funds)
        
        return Decimal(0)
    
    def _calculate_interest_payment(
        self,
        step: Dict[str, Any],
        tranches: List[Dict[str, Any]],
        available_funds: Decimal
    ) -> Decimal:
        """Calculate interest payment for a tranche"""
        tranche_id = step.get('tranche_id')
        
        # Find the tranche
        tranche = next((t for t in tranches if t['tranche_id'] == tranche_id), None)
        if not tranche:
            return Decimal(0)
        
        # Calculate interest payment
        current_balance = tranche['current_balance']
        coupon_rate = tranche.get('coupon_rate', Decimal(0))
        
        # Monthly interest = balance * annual_rate / 12
        monthly_interest = current_balance * coupon_rate / 12
        return monthly_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_principal_payment(
        self,
        step: Dict[str, Any],
        tranches: List[Dict[str, Any]],
        available_funds: Decimal
    ) -> Decimal:
        """Calculate principal payment for tranche(s)"""
        tranche_id = step.get('tranche_id')
        tranche_ids = step.get('tranches', [tranche_id] if tranche_id else [])
        
        if not tranche_ids:
            return Decimal(0)
        
        # Simplified: assume 2% monthly principal payment on current balance
        total_principal = Decimal(0)
        
        for t_id in tranche_ids:
            tranche = next((t for t in tranches if t['tranche_id'] == t_id), None)
            if tranche:
                principal_payment = tranche['current_balance'] * Decimal('0.02')  # 2% monthly
                total_principal += principal_payment
        
        return total_principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _record_payment_step(
        self,
        step: Dict[str, Any],
        target_amount: Decimal,
        actual_amount: Decimal,
        calculation_state: Dict[str, Any]
    ) -> None:
        """Record a payment step in the calculation state"""
        payment_step = {
            'step_number': step.get('step', 0),
            'description': step.get('description', ''),
            'payment_type': step.get('type', ''),
            'target_amount': float(target_amount),
            'actual_amount': float(actual_amount),
            'remaining_funds': float(calculation_state['remaining_funds'] - actual_amount),
            'tranche_id': step.get('tranche_id'),
            'priority': step.get('priority', 0)
        }
        
        calculation_state['payment_steps'].append(payment_step)
        
        # Update tranche payments
        tranche_id = step.get('tranche_id')
        if tranche_id:
            if tranche_id not in calculation_state['tranche_payments']:
                calculation_state['tranche_payments'][tranche_id] = {}
            
            payment_type = step.get('type', 'other')
            calculation_state['tranche_payments'][tranche_id][payment_type] = float(actual_amount)
    
    def _calculate_summary(self, calculation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary metrics from payment steps"""
        payment_steps = calculation_state['payment_steps']
        
        total_fees = sum(
            step['actual_amount'] for step in payment_steps
            if step['payment_type'] == 'fees'
        )
        
        total_interest = sum(
            step['actual_amount'] for step in payment_steps
            if step['payment_type'] == 'interest'
        )
        
        total_principal = sum(
            step['actual_amount'] for step in payment_steps
            if step['payment_type'] == 'principal'
        )
        
        total_distributions = sum(step['actual_amount'] for step in payment_steps)
        
        return {
            'total_fees_paid': total_fees,
            'total_interest_paid': total_interest,
            'total_principal_paid': total_principal,
            'total_distributions': total_distributions,
            'remaining_funds': float(calculation_state['remaining_funds'])
        }
    
    def _calculate_monthly_projection(
        self,
        deal_id: str,
        projection_date: date,
        scenario_params: List[Dict[str, Any]],
        assumptions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate projection for a single month"""
        # Simplified projection calculation
        return {
            'payment_date': projection_date,
            'principal_collections': float(Decimal('5000000')),  # Mock values
            'interest_collections': float(Decimal('3000000')),
            'fees_and_expenses': float(Decimal('100000')),
            'senior_payments': float(Decimal('6000000')),
            'mezzanine_payments': float(Decimal('1500000')),
            'subordinate_payments': float(Decimal('400000')),
            'equity_distribution': float(Decimal('100000')),
            'ending_balance': float(Decimal('440000000'))
        }
    
    def _calculate_projection_summary(self, monthly_projections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for projections"""
        if not monthly_projections:
            return {}
        
        total_collections = sum(
            proj['principal_collections'] + proj['interest_collections']
            for proj in monthly_projections
        )
        
        total_distributions = sum(
            proj['senior_payments'] + proj['mezzanine_payments'] + 
            proj['subordinate_payments'] + proj['equity_distribution']
            for proj in monthly_projections
        )
        
        return {
            'total_collections': total_collections,
            'total_distributions': total_distributions,
            'average_monthly_payment': total_distributions / len(monthly_projections),
            'final_recovery_rate': 0.98,  # Mock value
            'duration': 5.2,  # Mock duration in years
            'weighted_average_life': 4.8  # Mock WAL
        }
    
    def _get_base_waterfall(self, deal_id: str) -> Dict[str, Any]:
        """Get base waterfall calculation for comparison"""
        # Implementation would run base case waterfall
        return {}
    
    def _run_single_stress_test(
        self,
        deal_id: str,
        scenario: Dict[str, Any],
        base_waterfall: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single stress test scenario"""
        # Implementation would apply stress scenario and calculate impact
        return {
            'scenario_name': scenario.get('scenario_name', 'Unnamed'),
            'portfolio_loss': 5000000,  # Mock loss amount
            'loss_percentage': 1.1,  # Mock loss percentage
            'tranche_impacts': {
                'A1': 0,
                'A2': 0,
                'B': 2000000,
                'C': 3000000
            }
        }