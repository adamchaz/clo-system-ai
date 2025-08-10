"""
Fee Service - Integration layer for fee calculations with waterfall system
Manages fee calculations and integration with payment waterfall logic
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from ..models.fee import Fee, FeeCalculation, FeeCalculator, FeeType
from ..models.clo_deal import CLODeal
from ..models.liability import DayCountConvention


class FeeCalculationResult:
    """Result of fee calculations for a period"""
    
    def __init__(self):
        self.period: int = 0
        self.fee_results: Dict[str, Any] = {}  # By fee name
        self.total_fees_accrued: Decimal = Decimal('0')
        self.total_fees_paid: Decimal = Decimal('0')
        self.total_unpaid_balance: Decimal = Decimal('0')


class FeeService:
    """
    Service class for managing fee calculations and waterfall integration
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.fee_calculators: Dict[str, FeeCalculator] = {}  # By fee name
        self.current_period = 1
    
    def setup_deal_fees(self, deal_id: str, num_periods: int) -> None:
        """
        Setup fee calculators for a deal
        
        Args:
            deal_id: CLO deal identifier
            num_periods: Number of payment periods
        """
        # Get deal and its fee configurations
        deal = self.session.query(CLODeal).filter_by(deal_id=deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        fees = self.session.query(Fee).filter_by(deal_id=deal_id).all()
        if not fees:
            # Create default fee configurations if none exist
            self._create_default_fees(deal_id, num_periods)
            fees = self.session.query(Fee).filter_by(deal_id=deal_id).all()
        
        # Setup calculators for each fee
        for fee in fees:
            fee_calculator = FeeCalculator(fee)
            fee_calculator.setup_deal(num_periods, Decimal('0'))  # Will be set during calculation
            self.fee_calculators[fee.fee_name] = fee_calculator
    
    def calculate_fees(self, deal_id: str, period: int, begin_date: date, end_date: date,
                      fee_basis_amounts: Dict[str, Decimal],
                      libor_rate: Decimal = Decimal('0')) -> FeeCalculationResult:
        """
        Calculate fees for a specific period
        
        Args:
            deal_id: CLO deal identifier
            period: Payment period number
            begin_date: Period start date
            end_date: Period end date
            fee_basis_amounts: Fee basis amounts by fee name
            libor_rate: Period LIBOR/SOFR rate
            
        Returns:
            FeeCalculationResult with all calculation results
        """
        result = FeeCalculationResult()
        result.period = period
        self.current_period = period
        
        # Calculate each fee
        for fee_name, calculator in self.fee_calculators.items():
            # Get fee basis for this fee
            fee_basis = fee_basis_amounts.get(fee_name, Decimal('0'))
            
            # Ensure calculator is at correct period
            while calculator.current_period < period:
                calculator.rollforward()
            
            # Calculate fee
            fee_accrued = calculator.calculate_fee(
                begin_date, end_date, fee_basis, libor_rate
            )
            
            # Get detailed results
            fee_result = calculator.get_current_result()
            result.fee_results[fee_name] = fee_result
            
            # Add to totals
            result.total_fees_accrued += fee_accrued
            result.total_unpaid_balance += calculator.get_unpaid_balance()
        
        return result
    
    def apply_fee_payments(self, fee_payments: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """
        Apply fee payments to calculators
        
        Args:
            fee_payments: Payment amounts by fee name
            
        Returns:
            Dictionary with unused amounts by fee name
        """
        unused_amounts = {}
        
        for fee_name, payment_amount in fee_payments.items():
            if fee_name in self.fee_calculators:
                calculator = self.fee_calculators[fee_name]
                unused_amount = calculator.pay_fee(payment_amount)
                if unused_amount > 0:
                    unused_amounts[fee_name] = unused_amount
        
        return unused_amounts
    
    def get_fee_payment_requirements(self, fee_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get fee payment requirements for waterfall payment decisions
        
        Args:
            fee_name: Specific fee (if None, returns all)
            
        Returns:
            Dictionary with fee payment requirements
        """
        requirements = {}
        
        if fee_name:
            # Single fee requirements
            if fee_name in self.fee_calculators:
                calculator = self.fee_calculators[fee_name]
                requirements = {
                    'unpaid_balance': float(calculator.get_unpaid_balance()),
                    'fee_accrued': float(calculator.get_fee_accrued()),
                    'total_amount_due': float(calculator.get_unpaid_balance()),
                    'current_period': calculator.current_period
                }
        else:
            # All fees requirements
            requirements['fees'] = {}
            total_unpaid = Decimal('0')
            total_accrued = Decimal('0')
            
            for name, calculator in self.fee_calculators.items():
                unpaid_balance = calculator.get_unpaid_balance()
                fee_accrued = calculator.get_fee_accrued()
                
                requirements['fees'][name] = {
                    'unpaid_balance': float(unpaid_balance),
                    'fee_accrued': float(fee_accrued),
                    'total_amount_due': float(unpaid_balance)
                }
                
                total_unpaid += unpaid_balance
                total_accrued += fee_accrued
            
            requirements['totals'] = {
                'total_unpaid_balance': float(total_unpaid),
                'total_fees_accrued': float(total_accrued),
                'total_amount_due': float(total_unpaid)
            }
        
        return requirements
    
    def rollforward_all_fees(self):
        """Rollforward all fee calculators to next period"""
        for calculator in self.fee_calculators.values():
            calculator.rollforward()
        self.current_period += 1
    
    def save_fee_results_to_db(self, deal_id: str, period: int, begin_date: date, end_date: date) -> None:
        """
        Save current fee calculation results to database
        
        Args:
            deal_id: CLO deal identifier
            period: Payment period number
            begin_date: Period start date
            end_date: Period end date
        """
        for fee_name, calculator in self.fee_calculators.items():
            # Get fee configuration
            fee = self.session.query(Fee).filter_by(
                deal_id=deal_id, fee_name=fee_name
            ).first()
            
            if fee:
                # Create fee calculation record
                fee_calc = FeeCalculation(
                    fee_id=fee.fee_id,
                    period_number=period,
                    begin_date=begin_date,
                    end_date=end_date,
                    beginning_fee_basis=calculator.beginning_fee_basis,
                    ending_fee_basis=calculator.ending_fee_basis,
                    calculated_fee_basis=calculator.fee_basis[period] or Decimal('0'),
                    total_fee_accrued=calculator.fee_accrued[period],
                    beginning_unpaid_balance=calculator.beginning_balance[period],
                    fee_paid=calculator.fee_paid[period],
                    ending_unpaid_balance=calculator.ending_balance[period]
                )
                
                self.session.add(fee_calc)
        
        self.session.commit()
    
    def get_comprehensive_fee_report(self, deal_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive fee report for all periods
        
        Returns:
            Detailed report with all fee calculations
        """
        report = {
            'deal_id': deal_id,
            'fees': {},
            'summary': {}
        }
        
        # Fee reports
        total_fees_paid = Decimal('0')
        total_unpaid_balance = Decimal('0')
        
        for fee_name, calculator in self.fee_calculators.items():
            fee_report = {
                'fee_name': fee_name,
                'fee_type': calculator.fee_type.value,
                'fee_percentage': float(calculator.fee_percentage),
                'periods': calculator.get_output(),
                'total_fee_paid': float(calculator.get_total_fee_paid()),
                'current_unpaid_balance': float(calculator.get_unpaid_balance()),
                'last_calculated_period': calculator.last_calculated_period
            }
            
            report['fees'][fee_name] = fee_report
            total_fees_paid += calculator.get_total_fee_paid()
            total_unpaid_balance += calculator.get_unpaid_balance()
        
        # Summary statistics
        report['summary'] = {
            'periods_calculated': max(calc.last_calculated_period for calc in self.fee_calculators.values()) if self.fee_calculators else 0,
            'total_fees_paid': float(total_fees_paid),
            'total_unpaid_balance': float(total_unpaid_balance),
            'number_of_fees': len(self.fee_calculators)
        }
        
        return report
    
    def get_fee_basis_requirements(self) -> Dict[str, str]:
        """
        Get fee basis requirements for each fee type
        
        Returns:
            Dictionary mapping fee names to their basis requirements
        """
        requirements = {}
        
        for fee_name, calculator in self.fee_calculators.items():
            if calculator.fee_type == FeeType.BEGINNING:
                requirements[fee_name] = "beginning_balance"
            elif calculator.fee_type == FeeType.AVERAGE:
                requirements[fee_name] = "average_balance"
            else:  # FIXED
                requirements[fee_name] = "fixed_amount"
        
        return requirements
    
    def _create_default_fees(self, deal_id: str, num_periods: int) -> None:
        """
        Create default fee configurations for a deal
        
        Args:
            deal_id: CLO deal identifier
            num_periods: Number of payment periods
        """
        default_fees = [
            {
                'fee_name': 'Senior Management Fee',
                'fee_type': FeeType.BEGINNING.value,
                'fee_percentage': Decimal('0.005'),  # 0.5% annually
                'fixed_amount': Decimal('0'),
                'day_count_convention': DayCountConvention.ACT_360.value,
                'interest_on_fee': False,
                'interest_spread': Decimal('0'),
                'initial_unpaid_fee': Decimal('0')
            },
            {
                'fee_name': 'Subordinate Management Fee',
                'fee_type': FeeType.BEGINNING.value,
                'fee_percentage': Decimal('0.0025'),  # 0.25% annually
                'fixed_amount': Decimal('0'),
                'day_count_convention': DayCountConvention.ACT_360.value,
                'interest_on_fee': True,  # Typically earns interest when deferred
                'interest_spread': Decimal('0.01'),  # 1% spread
                'initial_unpaid_fee': Decimal('0')
            },
            {
                'fee_name': 'Trustee Fee',
                'fee_type': FeeType.FIXED.value,
                'fee_percentage': Decimal('0'),
                'fixed_amount': Decimal('50000'),  # $50K annually
                'day_count_convention': DayCountConvention.ACT_360.value,
                'interest_on_fee': False,
                'interest_spread': Decimal('0'),
                'initial_unpaid_fee': Decimal('0')
            }
        ]
        
        for fee_config in default_fees:
            fee = Fee(
                deal_id=deal_id,
                num_periods=num_periods,
                **fee_config
            )
            self.session.add(fee)
        
        self.session.commit()