"""
Test Suite for Liability Model
Comprehensive testing of CLO liability/tranche calculations
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append('..')

from app.models.liability import (
    Liability, LiabilityCashFlow, LiabilityCalculator,
    DayCountConvention, CouponType, generate_output_report
)
from app.models.clo_deal import CLODeal


class MockYieldCurve:
    """Mock yield curve for testing"""
    
    def zero_rate(self, analysis_date: date, payment_date: date) -> float:
        """Return a simple flat curve"""
        return 0.05  # 5% flat curve


@pytest.fixture
def session():
    """Create test database session"""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def test_deal(session):
    """Create test CLO deal"""
    deal = CLODeal(
        deal_id="TEST-LIABILITY-001",
        deal_name="Test Liability Deal",
        manager_name="Test Manager",
        pricing_date=date(2023, 1, 15),
        effective_date=date(2023, 2, 15),
        first_payment_date=date(2023, 5, 15),
        target_par_amount=Decimal('500000000'),
        payment_frequency=4
    )
    session.add(deal)
    session.commit()
    return deal


@pytest.fixture
def floating_rate_liability(session, test_deal):
    """Create floating rate liability for testing"""
    liability = Liability(
        deal_id=test_deal.deal_id,
        tranche_name="CLASS_A",
        original_balance=Decimal('300000000'),
        current_balance=Decimal('300000000'),
        deferred_balance=Decimal('0'),
        is_pikable=False,
        is_equity_tranche=False,
        libor_spread=Decimal('0.0150'),  # 150 bps
        coupon_type=CouponType.FLOATING.value,
        day_count_convention=DayCountConvention.ACT_360.value,
        input_price=Decimal('1.0'),
        input_discount_margin=Decimal('0.0100'),  # 100 bps
        analysis_date=date(2023, 2, 15)
    )
    session.add(liability)
    session.commit()
    return liability


@pytest.fixture
def pik_liability(session, test_deal):
    """Create PIK-able liability for testing"""
    liability = Liability(
        deal_id=test_deal.deal_id,
        tranche_name="CLASS_E",
        original_balance=Decimal('25000000'),
        current_balance=Decimal('20000000'),
        deferred_balance=Decimal('5000000'),  # $5M in PIK balance
        is_pikable=True,
        is_equity_tranche=False,
        libor_spread=Decimal('0.0800'),  # 800 bps
        coupon_type=CouponType.FLOATING.value,
        day_count_convention=DayCountConvention.ACT_360.value,
        input_price=Decimal('0.85'),
        input_discount_margin=Decimal('0.1000'),  # 1000 bps
        analysis_date=date(2023, 2, 15)
    )
    session.add(liability)
    session.commit()
    return liability


@pytest.fixture
def equity_tranche(session, test_deal):
    """Create equity tranche for testing"""
    liability = Liability(
        deal_id=test_deal.deal_id,
        tranche_name="EQUITY",
        original_balance=Decimal('50000000'),
        current_balance=Decimal('50000000'),
        deferred_balance=Decimal('0'),
        is_pikable=False,
        is_equity_tranche=True,
        libor_spread=Decimal('0'),
        coupon_type=CouponType.FLOATING.value,
        day_count_convention=DayCountConvention.ACT_360.value,
        input_price=Decimal('1.0'),
        analysis_date=date(2023, 2, 15)
    )
    session.add(liability)
    session.commit()
    return liability


@pytest.fixture
def payment_dates():
    """Standard quarterly payment dates"""
    return [
        date(2023, 5, 15),
        date(2023, 8, 15),
        date(2023, 11, 15),
        date(2024, 2, 15),
        date(2024, 5, 15),
        date(2024, 8, 15),
        date(2024, 11, 15),
        date(2025, 2, 15)
    ]


class TestLiabilityModel:
    """Test basic Liability model functionality"""
    
    def test_liability_creation(self, floating_rate_liability):
        """Test basic liability creation"""
        assert floating_rate_liability.tranche_name == "CLASS_A"
        assert floating_rate_liability.original_balance == Decimal('300000000')
        assert floating_rate_liability.current_balance == Decimal('300000000')
        assert not floating_rate_liability.is_equity_tranche
        assert not floating_rate_liability.is_pikable
        assert floating_rate_liability.libor_spread == Decimal('0.0150')
    
    def test_pik_liability_creation(self, pik_liability):
        """Test PIK liability creation"""
        assert pik_liability.tranche_name == "CLASS_E"
        assert pik_liability.deferred_balance == Decimal('5000000')
        assert pik_liability.is_pikable
        assert pik_liability.libor_spread == Decimal('0.0800')
    
    def test_equity_tranche_creation(self, equity_tranche):
        """Test equity tranche creation"""
        assert equity_tranche.tranche_name == "EQUITY"
        assert equity_tranche.is_equity_tranche
        assert not equity_tranche.is_pikable


class TestLiabilityCalculator:
    """Test LiabilityCalculator functionality"""
    
    def test_calculator_initialization(self, floating_rate_liability, payment_dates):
        """Test calculator initialization"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        assert calculator.liability == floating_rate_liability
        assert calculator.payment_dates == payment_dates
        assert calculator.current_period == 1
        assert len(calculator.liability.cash_flows) == len(payment_dates)
    
    def test_cash_flow_initialization(self, floating_rate_liability, payment_dates):
        """Test cash flow record initialization"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Check first period
        first_cf = calculator._get_cash_flow(1)
        assert first_cf is not None
        assert first_cf.period_number == 1
        assert first_cf.payment_date == payment_dates[0]
        assert first_cf.beginning_balance == Decimal('300000000')
        
        # Check subsequent periods
        second_cf = calculator._get_cash_flow(2)
        assert second_cf is not None
        assert second_cf.beginning_balance == Decimal('0')  # Will be set by roll forward
    
    def test_period_calculation(self, floating_rate_liability, payment_dates):
        """Test interest calculation for a period"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Calculate first period with 3% LIBOR
        libor_rate = Decimal('0.03')
        prev_date = date(2023, 2, 15)
        next_date = payment_dates[0]
        
        calculator.calculate_period(1, libor_rate, prev_date, next_date)
        
        first_cf = calculator._get_cash_flow(1)
        
        # Expected coupon = 3% LIBOR + 1.5% spread = 4.5%
        expected_coupon = Decimal('0.045')
        assert first_cf.coupon_rate == expected_coupon
        
        # Expected interest = $300M * (89/360) * 4.5% = approximately $3.34M
        days = (next_date - prev_date).days  # 89 days
        expected_interest = Decimal('300000000') * Decimal(str(days)) / Decimal('360') * expected_coupon
        
        assert abs(first_cf.interest_accrued - expected_interest) < Decimal('1000')  # Within $1K
    
    def test_interest_payment(self, floating_rate_liability, payment_dates):
        """Test interest payment processing"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Setup period calculation
        calculator.calculate_period(1, Decimal('0.03'), date(2023, 2, 15), payment_dates[0])
        
        first_cf = calculator._get_cash_flow(1)
        interest_accrued = first_cf.interest_accrued
        
        # Pay full interest
        remaining = calculator.pay_interest(1, interest_accrued)
        
        assert first_cf.interest_paid == interest_accrued
        assert remaining == Decimal('0')
        
        # Pay partial interest
        calculator._get_cash_flow(1).interest_paid = Decimal('0')  # Reset
        partial_payment = interest_accrued / 2
        
        remaining = calculator.pay_interest(1, partial_payment)
        
        assert first_cf.interest_paid == partial_payment
        assert remaining == Decimal('0')
    
    def test_principal_payment(self, floating_rate_liability, payment_dates):
        """Test principal payment processing"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        first_cf = calculator._get_cash_flow(1)
        beginning_balance = first_cf.beginning_balance
        
        # Pay partial principal
        principal_payment = Decimal('50000000')  # $50M
        remaining = calculator.pay_principal(1, principal_payment)
        
        assert first_cf.principal_paid == principal_payment
        assert remaining == Decimal('0')
        
        # Pay more than remaining balance
        remaining_balance = beginning_balance - principal_payment
        overpayment = remaining_balance + Decimal('10000000')  # $10M extra
        
        remaining = calculator.pay_principal(1, overpayment)
        
        assert first_cf.principal_paid == beginning_balance  # Full balance paid
        assert remaining == Decimal('10000000')  # $10M returned
    
    def test_pik_interest_payment(self, pik_liability, payment_dates):
        """Test PIK interest payment processing"""
        calculator = LiabilityCalculator(pik_liability, payment_dates)
        
        # Setup period calculation
        calculator.calculate_period(1, Decimal('0.02'), date(2023, 2, 15), payment_dates[0])
        
        first_cf = calculator._get_cash_flow(1)
        
        # PIK balance due includes deferred balance plus accrued interest
        pik_balance = (
            first_cf.deferred_beginning_balance + 
            first_cf.deferred_interest_accrued
        )
        
        # Pay PIK balance
        remaining = calculator.pay_pik_interest(1, pik_balance)
        
        assert first_cf.deferred_principal_paid == pik_balance
        assert remaining == Decimal('0')
    
    def test_roll_forward(self, floating_rate_liability, payment_dates):
        """Test balance roll forward to next period"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Setup first period with payments
        calculator.calculate_period(1, Decimal('0.03'), date(2023, 2, 15), payment_dates[0])
        first_cf = calculator._get_cash_flow(1)
        
        # Make some payments
        calculator.pay_interest(1, first_cf.interest_accrued)
        calculator.pay_principal(1, Decimal('20000000'))  # $20M principal
        
        # Roll forward
        calculator.roll_forward(1)
        
        # Check ending balances
        assert first_cf.ending_balance == Decimal('280000000')  # $300M - $20M
        
        # Check next period beginning balance
        second_cf = calculator._get_cash_flow(2)
        assert second_cf.beginning_balance == Decimal('280000000')
        
        # Check deferred balance (unpaid interest becomes PIK)
        unpaid_interest = first_cf.interest_accrued - first_cf.interest_paid
        assert second_cf.deferred_beginning_balance == unpaid_interest
    
    def test_equity_tranche_payments(self, equity_tranche, payment_dates):
        """Test equity tranche payment handling"""
        calculator = LiabilityCalculator(equity_tranche, payment_dates)
        
        # Equity doesn't calculate interest
        calculator.calculate_period(1, Decimal('0.03'), date(2023, 2, 15), payment_dates[0])
        first_cf = calculator._get_cash_flow(1)
        
        assert first_cf.coupon_rate is None
        assert first_cf.interest_accrued == Decimal('0') or first_cf.interest_accrued is None
        
        # Equity receives all available cash
        payment_amount = Decimal('5000000')
        
        remaining_interest = calculator.pay_interest(1, payment_amount)
        assert remaining_interest == Decimal('0')
        assert first_cf.interest_paid == payment_amount
        
        remaining_principal = calculator.pay_principal(1, payment_amount)
        assert remaining_principal == Decimal('0')
        assert first_cf.principal_paid == payment_amount


class TestRiskMeasures:
    """Test risk measure calculations"""
    
    def test_date_fraction_calculation(self, floating_rate_liability, payment_dates):
        """Test day count fraction calculations"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        start_date = date(2023, 2, 15)
        end_date = date(2023, 5, 15)  # 89 days
        
        # ACT/360
        fraction_360 = calculator._calculate_date_fraction(
            start_date, end_date, DayCountConvention.ACT_360
        )
        expected_360 = Decimal('89') / Decimal('360')
        assert abs(fraction_360 - expected_360) < Decimal('0.0001')
        
        # ACT/365
        fraction_365 = calculator._calculate_date_fraction(
            start_date, end_date, DayCountConvention.ACT_365
        )
        expected_365 = Decimal('89') / Decimal('365')
        assert abs(fraction_365 - expected_365) < Decimal('0.0001')
        
        # 30/360
        fraction_30_360 = calculator._calculate_date_fraction(
            start_date, end_date, DayCountConvention.THIRTY_360
        )
        # Should be same as ACT/360 for this test
        assert abs(fraction_30_360 - expected_360) < Decimal('0.0001')
    
    def test_risk_measures_calculation(self, floating_rate_liability, payment_dates):
        """Test risk measures calculation"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        yield_curve = MockYieldCurve()
        
        # Setup multiple periods with payments
        libor_rate = Decimal('0.03')
        
        for period in range(1, 5):  # First 4 periods
            prev_date = date(2023, 2, 15) if period == 1 else payment_dates[period - 2]
            next_date = payment_dates[period - 1]
            
            calculator.calculate_period(period, libor_rate, prev_date, next_date)
            
            # Make payments
            cf = calculator._get_cash_flow(period)
            calculator.pay_interest(period, cf.interest_accrued)
            calculator.pay_principal(period, Decimal('10000000'))  # $10M each period
            
            calculator.roll_forward(period)
        
        # Calculate risk measures
        analysis_date = date(2023, 2, 15)
        risk_measures = calculator.calculate_risk_measures(yield_curve, analysis_date)
        
        assert 'calculated_yield' in risk_measures
        assert 'weighted_average_life' in risk_measures
        assert 'macaulay_duration' in risk_measures
        assert 'modified_duration' in risk_measures
        
        # Basic sanity checks
        assert risk_measures['weighted_average_life'] > Decimal('0')
        assert risk_measures['macaulay_duration'] > Decimal('0')
        assert risk_measures['modified_duration'] > Decimal('0')


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_current_balance(self, floating_rate_liability, payment_dates):
        """Test current balance calculation"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Initial balance
        current_balance = calculator.get_current_balance(1)
        assert current_balance == Decimal('300000000')
        
        # After principal payment
        calculator.pay_principal(1, Decimal('50000000'))
        # Note: balance doesn't change until roll forward
        current_balance = calculator.get_current_balance(1)
        assert current_balance == Decimal('300000000')
    
    def test_get_current_balance_with_pik(self, pik_liability, payment_dates):
        """Test current balance calculation with PIK"""
        calculator = LiabilityCalculator(pik_liability, payment_dates)
        
        # Should include PIK balance
        current_balance = calculator.get_current_balance(1)
        expected = Decimal('20000000') + Decimal('5000000')  # Current + PIK
        assert current_balance == expected
    
    def test_get_interest_due(self, floating_rate_liability, payment_dates):
        """Test interest due calculation"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Calculate interest
        calculator.calculate_period(1, Decimal('0.03'), date(2023, 2, 15), payment_dates[0])
        
        interest_due = calculator.get_interest_due(1)
        first_cf = calculator._get_cash_flow(1)
        
        assert interest_due == first_cf.interest_accrued
        
        # After partial payment
        calculator.pay_interest(1, interest_due / 2)
        interest_due = calculator.get_interest_due(1)
        
        assert interest_due == first_cf.interest_accrued / 2
    
    def test_distribution_percentage(self, floating_rate_liability, payment_dates):
        """Test current distribution percentage calculation"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Make payments
        calculator.pay_interest(1, Decimal('3000000'))  # $3M interest
        calculator.pay_principal(1, Decimal('10000000'))  # $10M principal
        
        percentage = calculator.get_current_distribution_percentage(1)
        expected = (Decimal('3000000') + Decimal('10000000')) / Decimal('300000000')
        
        assert abs(percentage - expected) < Decimal('0.0001')


class TestOutputGeneration:
    """Test output report generation"""
    
    def test_equity_output_generation(self, equity_tranche, payment_dates):
        """Test equity tranche output generation"""
        calculator = LiabilityCalculator(equity_tranche, payment_dates)
        
        # Make some payments
        calculator.pay_interest(1, Decimal('2000000'))
        calculator.pay_principal(1, Decimal('5000000'))
        
        output = generate_output_report(equity_tranche, calculator)
        
        assert len(output) > 1  # Header + data rows
        assert output[0] == ["Period", "Beg Balance", "Prin Paid", "Int Paid", "Current Percent"]
        
        # Check first data row
        assert output[1][0] == 1  # Period
        assert output[1][1] == 50000000.0  # Beginning balance
    
    def test_debt_output_generation(self, floating_rate_liability, payment_dates):
        """Test debt tranche output generation"""
        calculator = LiabilityCalculator(floating_rate_liability, payment_dates)
        
        # Calculate and make payments
        calculator.calculate_period(1, Decimal('0.03'), date(2023, 2, 15), payment_dates[0])
        first_cf = calculator._get_cash_flow(1)
        calculator.pay_interest(1, first_cf.interest_accrued)
        calculator.pay_principal(1, Decimal('20000000'))
        
        output = generate_output_report(floating_rate_liability, calculator)
        
        assert len(output) > 1
        
        # Check headers
        expected_headers = ["Period", "Coupon", "Beg Balance", "Int Accrued", "Int Paid", 
                          "Prin Paid", "End Balance", "Def Beg Balance", "Def Prin Paid", "Def End Balance"]
        assert output[0] == expected_headers
        
        # Check first data row
        assert output[1][0] == 1  # Period
        assert "%" in output[1][1]  # Coupon formatted as percentage
    
    def test_pik_output_generation(self, pik_liability, payment_dates):
        """Test PIK tranche output generation"""
        calculator = LiabilityCalculator(pik_liability, payment_dates)
        
        # Calculate period
        calculator.calculate_period(1, Decimal('0.02'), date(2023, 2, 15), payment_dates[0])
        
        output = generate_output_report(pik_liability, calculator)
        
        # PIK tranches should have additional columns
        headers = output[0]
        assert "Def Int Accrued" in headers
        assert "Def Int Paid" in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])