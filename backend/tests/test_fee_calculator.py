"""
Tests for Fee Calculator
Comprehensive testing of fee calculation logic converted from VBA Fees.cls
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.fee import Fee, FeeCalculator, FeeType
from app.models.liability import DayCountConvention
from app.core.database import Base, engine


class TestFeeCalculator:
    """Test suite for FeeCalculator class"""
    
    @pytest.fixture
    def fee_config_beginning(self):
        """Create beginning balance fee configuration"""
        return Fee(
            deal_id="TEST_DEAL",
            fee_name="Management Fee",
            fee_type=FeeType.BEGINNING.value,
            fee_percentage=Decimal('0.005'),  # 0.5% annually
            fixed_amount=Decimal('0'),
            day_count_convention=DayCountConvention.ACT_360.value,
            interest_on_fee=False,
            interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'),
            num_periods=48,
            beginning_fee_basis=Decimal('500000000')  # $500M
        )
    
    @pytest.fixture
    def fee_config_average(self):
        """Create average balance fee configuration"""
        return Fee(
            deal_id="TEST_DEAL",
            fee_name="Subordinate Management Fee",
            fee_type=FeeType.AVERAGE.value,
            fee_percentage=Decimal('0.0025'),  # 0.25% annually
            fixed_amount=Decimal('0'),
            day_count_convention=DayCountConvention.ACT_360.value,
            interest_on_fee=True,
            interest_spread=Decimal('0.01'),  # 1% spread
            initial_unpaid_fee=Decimal('100000'),  # $100K unpaid
            num_periods=48,
            beginning_fee_basis=Decimal('500000000')
        )
    
    @pytest.fixture
    def fee_config_fixed(self):
        """Create fixed fee configuration"""
        return Fee(
            deal_id="TEST_DEAL",
            fee_name="Trustee Fee",
            fee_type=FeeType.FIXED.value,
            fee_percentage=Decimal('0'),
            fixed_amount=Decimal('50000'),  # $50K annually
            day_count_convention=DayCountConvention.ACT_365.value,
            interest_on_fee=False,
            interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'),
            num_periods=48,
            beginning_fee_basis=Decimal('0')
        )
    
    def test_fee_calculator_initialization(self, fee_config_beginning):
        """Test fee calculator initialization"""
        calculator = FeeCalculator(fee_config_beginning)
        
        assert calculator.fee_name == "Management Fee"
        assert calculator.fee_type == FeeType.BEGINNING
        assert calculator.fee_percentage == Decimal('0.005')
        assert calculator.num_periods == 48
        assert calculator.current_period == 1
        assert len(calculator.fee_accrued) == 49  # num_periods + 1
    
    def test_beginning_balance_fee_calculation(self, fee_config_beginning):
        """Test beginning balance fee calculation"""
        calculator = FeeCalculator(fee_config_beginning)
        
        # Calculate fee for quarterly period (90 days)
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)  # 90 days
        ending_basis = Decimal('480000000')  # $480M ending
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        # Expected: $500M * 0.5% * (90/360) = $625,000
        expected_fee = Decimal('500000000') * Decimal('0.005') * Decimal('90') / Decimal('360')
        
        assert abs(fee_accrued - expected_fee) < Decimal('1')  # Allow small rounding
        assert calculator.fee_basis[1] == Decimal('500000000')
        assert calculator.last_calculated_period == 1
    
    def test_average_balance_fee_calculation(self, fee_config_average):
        """Test average balance fee calculation"""
        calculator = FeeCalculator(fee_config_average)
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)  # 90 days
        ending_basis = Decimal('450000000')  # $450M ending
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        # Expected: (($500M + $450M) / 2) * 0.25% * (90/360) = $296,875
        average_basis = (Decimal('500000000') + Decimal('450000000')) / 2
        expected_fee = average_basis * Decimal('0.0025') * Decimal('90') / Decimal('360')
        
        assert abs(fee_accrued - expected_fee) < Decimal('1')
        assert calculator.fee_basis[1] == average_basis
    
    def test_fixed_fee_calculation(self, fee_config_fixed):
        """Test fixed fee calculation"""
        calculator = FeeCalculator(fee_config_fixed)
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)  # 90 days
        ending_basis = Decimal('0')  # Not used for fixed fees
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        # Expected: $50,000 * (90/365) = $12,328.77
        expected_fee = Decimal('50000') * Decimal('90') / Decimal('365')
        
        assert abs(fee_accrued - expected_fee) < Decimal('0.01')
    
    def test_interest_on_unpaid_fee(self, fee_config_average):
        """Test interest calculation on unpaid fees"""
        calculator = FeeCalculator(fee_config_average)
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)  # 90 days
        ending_basis = Decimal('450000000')
        libor_rate = Decimal('0.03')  # 3% LIBOR
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis, libor_rate)
        
        # Base fee calculation
        average_basis = (Decimal('500000000') + Decimal('450000000')) / 2
        base_fee = average_basis * Decimal('0.0025') * Decimal('90') / Decimal('360')
        
        # Interest on unpaid fee: $100K * (3% + 1%) * (90/360) = $1,000
        unpaid_balance = Decimal('100000')
        interest_rate = libor_rate + Decimal('0.01')  # LIBOR + spread
        interest_on_unpaid = unpaid_balance * interest_rate * Decimal('90') / Decimal('360')
        
        expected_total = base_fee + interest_on_unpaid
        
        assert abs(fee_accrued - expected_total) < Decimal('1')
    
    def test_fee_payment_full(self, fee_config_beginning):
        """Test full fee payment"""
        calculator = FeeCalculator(fee_config_beginning)
        
        # Calculate fee first
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        ending_basis = Decimal('480000000')
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        # Pay full amount
        payment_amount = fee_accrued + Decimal('10000')  # Pay more than due
        unused_amount = calculator.pay_fee(payment_amount)
        
        assert calculator.fee_paid[1] == fee_accrued
        assert unused_amount == Decimal('10000')
    
    def test_fee_payment_partial(self, fee_config_beginning):
        """Test partial fee payment"""
        calculator = FeeCalculator(fee_config_beginning)
        
        # Calculate fee first
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        ending_basis = Decimal('480000000')
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        # Pay partial amount
        payment_amount = fee_accrued / 2
        unused_amount = calculator.pay_fee(payment_amount)
        
        assert calculator.fee_paid[1] == payment_amount
        assert unused_amount == Decimal('0')
        assert calculator.get_unpaid_balance() == fee_accrued / 2
    
    def test_rollforward_logic(self, fee_config_beginning):
        """Test period rollforward"""
        calculator = FeeCalculator(fee_config_beginning)
        
        # Period 1
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        ending_basis = Decimal('480000000')
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        partial_payment = fee_accrued / 2
        calculator.pay_fee(partial_payment)
        
        # Rollforward
        calculator.rollforward()
        
        # Check rollforward results
        expected_ending_balance = fee_accrued - partial_payment
        assert calculator.ending_balance[1] == expected_ending_balance
        assert calculator.current_period == 2
        assert calculator.beginning_balance[2] == expected_ending_balance
        assert calculator.beginning_fee_basis == Decimal('480000000')
    
    def test_multiple_periods(self, fee_config_beginning):
        """Test multiple period calculations"""
        calculator = FeeCalculator(fee_config_beginning)
        
        periods_data = [
            (date(2023, 1, 1), date(2023, 4, 1), Decimal('480000000')),
            (date(2023, 4, 1), date(2023, 7, 1), Decimal('460000000')),
            (date(2023, 7, 1), date(2023, 10, 1), Decimal('440000000'))
        ]
        
        total_fees_paid = Decimal('0')
        
        for begin_date, end_date, ending_basis in periods_data:
            fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
            calculator.pay_fee(fee_accrued)  # Full payment
            total_fees_paid += fee_accrued
            
            if calculator.current_period < len(periods_data):
                calculator.rollforward()
        
        assert calculator.get_total_fee_paid() == total_fees_paid
        assert calculator.last_calculated_period == 3
    
    def test_day_count_conventions(self):
        """Test different day count conventions"""
        # Test ACT/360
        fee_config_360 = Fee(
            deal_id="TEST", fee_name="Test", fee_type=FeeType.FIXED.value,
            fee_percentage=Decimal('0'), fixed_amount=Decimal('100000'),
            day_count_convention=DayCountConvention.ACT_360.value,
            interest_on_fee=False, interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'), num_periods=4,
            beginning_fee_basis=Decimal('0')
        )
        
        calculator_360 = FeeCalculator(fee_config_360)
        
        # 90-day period
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        
        fee_360 = calculator_360.calculate_fee(begin_date, end_date, Decimal('0'))
        expected_360 = Decimal('100000') * Decimal('90') / Decimal('360')
        
        assert abs(fee_360 - expected_360) < Decimal('0.01')
        
        # Test ACT/365
        fee_config_365 = Fee(
            deal_id="TEST", fee_name="Test", fee_type=FeeType.FIXED.value,
            fee_percentage=Decimal('0'), fixed_amount=Decimal('100000'),
            day_count_convention=DayCountConvention.ACT_365.value,
            interest_on_fee=False, interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'), num_periods=4,
            beginning_fee_basis=Decimal('0')
        )
        
        calculator_365 = FeeCalculator(fee_config_365)
        fee_365 = calculator_365.calculate_fee(begin_date, end_date, Decimal('0'))
        expected_365 = Decimal('100000') * Decimal('90') / Decimal('365')
        
        assert abs(fee_365 - expected_365) < Decimal('0.01')
        assert fee_360 > fee_365  # ACT/360 should be higher
    
    def test_thirty_360_day_count(self):
        """Test 30/360 day count convention"""
        fee_config = Fee(
            deal_id="TEST", fee_name="Test", fee_type=FeeType.FIXED.value,
            fee_percentage=Decimal('0'), fixed_amount=Decimal('100000'),
            day_count_convention=DayCountConvention.THIRTY_360.value,
            interest_on_fee=False, interest_spread=Decimal('0'),
            initial_unpaid_fee=Decimal('0'), num_periods=4,
            beginning_fee_basis=Decimal('0')
        )
        
        calculator = FeeCalculator(fee_config)
        
        # Test exact 3-month period (should be 90 days in 30/360)
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, Decimal('0'))
        expected_fee = Decimal('100000') * Decimal('90') / Decimal('360')  # Exactly 3 months = 90 days
        
        assert abs(fee_accrued - expected_fee) < Decimal('0.01')
    
    def test_zero_fee_basis(self, fee_config_beginning):
        """Test behavior with zero fee basis"""
        calculator = FeeCalculator(fee_config_beginning)
        
        begin_date = date(2023, 1, 1)
        end_date = date(2023, 4, 1)
        ending_basis = Decimal('0')  # Zero ending basis
        
        fee_accrued = calculator.calculate_fee(begin_date, end_date, ending_basis)
        
        assert fee_accrued == Decimal('0')
        assert calculator.last_calculated_period == 0  # Should not have calculated
    
    def test_get_output_format(self, fee_config_beginning):
        """Test output format matches VBA Output() function"""
        calculator = FeeCalculator(fee_config_beginning)
        
        # Calculate a few periods
        periods_data = [
            (date(2023, 1, 1), date(2023, 4, 1), Decimal('480000000')),
            (date(2023, 4, 1), date(2023, 7, 1), Decimal('460000000'))
        ]
        
        for begin_date, end_date, ending_basis in periods_data:
            calculator.calculate_fee(begin_date, end_date, ending_basis)
            calculator.pay_fee(calculator.get_fee_accrued() / 2)  # Partial payment
            calculator.rollforward()
        
        output = calculator.get_output()
        
        assert len(output) == 2  # Two periods calculated
        
        # Check first period structure
        period1 = output[0]
        assert period1['period'] == 1
        assert 'fee_basis' in period1
        assert 'beginning_balance' in period1
        assert 'fee_accrued' in period1
        assert 'fee_paid' in period1
        assert 'ending_balance' in period1
        
        # Verify balance continuity
        assert output[0]['ending_balance'] > 0  # Should have unpaid balance
        assert abs(output[0]['ending_balance'] - output[0]['fee_accrued'] + output[0]['fee_paid']) < 0.01
    
    def test_complex_scenario(self):
        """Test complex scenario with all features"""
        # Complex fee with interest on unpaid amounts
        fee_config = Fee(
            deal_id="COMPLEX_DEAL",
            fee_name="Complex Management Fee",
            fee_type=FeeType.AVERAGE.value,
            fee_percentage=Decimal('0.004'),  # 0.4% annually
            fixed_amount=Decimal('25000'),    # Plus $25K fixed
            day_count_convention=DayCountConvention.ACT_360.value,
            interest_on_fee=True,
            interest_spread=Decimal('0.015'),  # 1.5% spread
            initial_unpaid_fee=Decimal('200000'),  # $200K unpaid
            num_periods=48,
            beginning_fee_basis=Decimal('750000000')  # $750M
        )
        
        calculator = FeeCalculator(fee_config)
        
        # Period 1: High LIBOR, partial payment
        fee1 = calculator.calculate_fee(
            date(2023, 1, 1), date(2023, 4, 1),
            Decimal('720000000'),  # $720M ending
            Decimal('0.04')  # 4% LIBOR
        )
        
        # Should include base fee, fixed fee, and interest on unpaid
        average_basis = (Decimal('750000000') + Decimal('720000000')) / 2
        expected_base = (average_basis * Decimal('0.004') + Decimal('25000')) * Decimal('90') / Decimal('360')
        expected_interest = Decimal('200000') * (Decimal('0.04') + Decimal('0.015')) * Decimal('90') / Decimal('360')
        expected_total = expected_base + expected_interest
        
        assert abs(fee1 - expected_total) < Decimal('1')
        
        # Partial payment
        calculator.pay_fee(fee1 / 3)
        calculator.rollforward()
        
        # Period 2: Lower basis, different payment
        fee2 = calculator.calculate_fee(
            date(2023, 4, 1), date(2023, 7, 1),
            Decimal('700000000'),  # $700M ending
            Decimal('0.035')  # 3.5% LIBOR
        )
        
        # Full payment this time
        calculator.pay_fee(fee2)
        
        # Verify state
        assert calculator.get_total_fee_paid() == fee1 / 3 + fee2
        assert calculator.current_period == 2
        assert calculator.get_unpaid_balance() == Decimal('0')  # Fully paid this period