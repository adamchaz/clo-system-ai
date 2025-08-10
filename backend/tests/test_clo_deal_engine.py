"""
Test Suite for CLO Deal Engine
Comprehensive testing of master orchestration functionality
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

from ..app.models.clo_deal_engine import (
    CLODealEngine, PaymentDates, DealDates, ReinvestmentInfo, 
    Account, AccountType, CashType
)
from ..app.models.clo_deal import CLODeal
from ..app.models.liability import Liability, DayCountConvention, CouponType
from ..app.models.dynamic_waterfall import DynamicWaterfallStrategy


@pytest.fixture
def session():
    """Create test database session"""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def test_clo_deal(session):
    """Create test CLO deal"""
    deal = CLODeal(
        deal_id="TEST-ENGINE-001",
        deal_name="Test CLO Deal Engine",
        manager_name="Test Manager",
        pricing_date=date(2023, 1, 15),
        closing_date=date(2023, 2, 15),
        effective_date=date(2023, 2, 15),
        first_payment_date=date(2023, 5, 15),
        maturity_date=date(2025, 5, 15),
        reinvestment_end_date=date(2024, 5, 15),
        no_call_date=date(2024, 2, 15),
        target_par_amount=Decimal('500000000'),
        payment_frequency=4  # Quarterly
    )
    return deal


@pytest.fixture
def test_deal_dates():
    """Create test deal dates configuration"""
    return DealDates(
        analysis_date=date(2023, 3, 1),
        closing_date=date(2023, 2, 15),
        first_payment_date=date(2023, 5, 15),
        maturity_date=date(2025, 5, 15),
        reinvestment_end_date=date(2024, 5, 15),
        no_call_date=date(2024, 2, 15),
        payment_day=15,
        months_between_payments=3,
        business_day_convention="FOLLOWING",
        determination_date_offset=2,
        interest_determination_date_offset=2
    )


@pytest.fixture
def test_reinvestment_info():
    """Create test reinvestment configuration"""
    return ReinvestmentInfo(
        pre_reinvestment_type="ALL PRINCIPAL",
        pre_reinvestment_pct=Decimal('1.0'),  # 100%
        post_reinvestment_type="UNSCHEDULED PRINCIPAL", 
        post_reinvestment_pct=Decimal('0.5')  # 50%
    )


@pytest.fixture
def test_liabilities(session, test_clo_deal):
    """Create test liability structure"""
    liabilities = {}
    
    # Class A - Senior tranche
    class_a = Liability(
        deal_id=test_clo_deal.deal_id,
        tranche_name="Class A",
        original_balance=Decimal('300000000'),
        current_balance=Decimal('300000000'),
        libor_spread=Decimal('0.0150'),  # 150 bps
        coupon_type=CouponType.FLOATING,
        day_count_convention=DayCountConvention.ACT_360,
        is_pikable=False,
        is_equity_tranche=False
    )
    
    # Class B - Mezzanine tranche
    class_b = Liability(
        deal_id=test_clo_deal.deal_id,
        tranche_name="Class B",
        original_balance=Decimal('50000000'),
        current_balance=Decimal('50000000'),
        libor_spread=Decimal('0.0300'),  # 300 bps
        coupon_type=CouponType.FLOATING,
        day_count_convention=DayCountConvention.ACT_360,
        is_pikable=False,
        is_equity_tranche=False
    )
    
    # Sub Notes - Subordinated
    sub_notes = Liability(
        deal_id=test_clo_deal.deal_id,
        tranche_name="Sub Notes",
        original_balance=Decimal('50000000'),
        current_balance=Decimal('50000000'),
        libor_spread=Decimal('0.1200'),  # 1200 bps
        coupon_type=CouponType.FLOATING,
        day_count_convention=DayCountConvention.ACT_360,
        is_pikable=True,
        is_equity_tranche=False
    )
    
    liabilities = {
        "Class A": class_a,
        "Class B": class_b,
        "Sub Notes": sub_notes
    }
    
    return liabilities


@pytest.fixture
def mock_waterfall_strategy():
    """Create mock waterfall strategy"""
    strategy = Mock(spec=DynamicWaterfallStrategy)
    strategy.setup_deal = Mock()
    strategy.setup_waterfall_execution = Mock()
    strategy.calculate_period = Mock()
    strategy.execute_interest_waterfall = Mock()
    strategy.execute_principal_waterfall = Mock()
    strategy.execute_note_payment_sequence = Mock()
    strategy.execute_eod_waterfall = Mock()
    return strategy


@pytest.fixture
def clo_deal_engine(session, test_clo_deal, test_deal_dates, test_reinvestment_info, 
                   test_liabilities, mock_waterfall_strategy):
    """Create configured CLO Deal Engine"""
    engine = CLODealEngine(test_clo_deal, session)
    
    # Setup configuration
    engine.setup_deal_dates(test_deal_dates)
    engine.setup_reinvestment_info(test_reinvestment_info)
    engine.setup_accounts()
    engine.setup_liabilities(test_liabilities)
    engine.setup_waterfall_strategy(mock_waterfall_strategy)
    
    # Setup inputs
    clo_inputs = {
        "Current LIBOR": 0.05,
        "Analysis Date": date(2023, 3, 1),
        "Deal Name": "Test CLO",
        "Event of Default": False,
        "Purchase Finance Accrued Interest": 1000000.0
    }
    
    cf_inputs = {
        "Call when Quarterly Sub Dist <": 0.05,
        "Liquidation Price": 0.70,
        "CCC Liquidation Price": 0.50,
        "CCC Asset Haircut Percent": 0.10
    }
    
    engine.setup_inputs(clo_inputs, cf_inputs)
    
    return engine


class TestCLODealEngine:
    """Test basic CLO Deal Engine functionality"""
    
    def test_engine_initialization(self, clo_deal_engine):
        """Test engine initialization"""
        assert clo_deal_engine.deal.deal_id == "TEST-ENGINE-001"
        assert clo_deal_engine.deal_name == "Test CLO Deal Engine"
        assert len(clo_deal_engine.liabilities) == 3
        assert AccountType.COLLECTION in clo_deal_engine.accounts
        assert clo_deal_engine.deal_dates is not None
        assert clo_deal_engine.reinvestment_info is not None
    
    def test_payment_date_calculation(self, clo_deal_engine):
        """Test payment date calculation"""
        clo_deal_engine.calculate_payment_dates()
        
        payment_dates = clo_deal_engine.payment_dates
        
        # Should have multiple payment periods
        assert len(payment_dates) > 0
        assert len(payment_dates) <= 10  # Reasonable number for 2-year deal
        
        # Check first payment date
        first_payment = payment_dates[0]
        assert first_payment.payment_date == date(2023, 5, 15)
        assert first_payment.collection_begin_date == date(2023, 2, 15)  # Closing date
        
        # Check payment dates are quarterly
        if len(payment_dates) > 1:
            second_payment = payment_dates[1]
            months_diff = (second_payment.payment_date.year - first_payment.payment_date.year) * 12 + \
                         second_payment.payment_date.month - first_payment.payment_date.month
            assert months_diff == 3  # Quarterly payments
    
    def test_deal_setup(self, clo_deal_engine):
        """Test deal setup process"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Check arrays initialized
        assert len(clo_deal_engine.interest_proceeds) > 0
        assert len(clo_deal_engine.principal_proceeds) > 0
        assert len(clo_deal_engine.notes_payable) > 0
        assert len(clo_deal_engine.libor_rates) > 0
        
        # Check liability calculators created
        assert len(clo_deal_engine.liability_calculators) == 3
        assert "Class A" in clo_deal_engine.liability_calculators
        assert "Class B" in clo_deal_engine.liability_calculators
        assert "Sub Notes" in clo_deal_engine.liability_calculators
        
        # Check waterfall strategy setup called
        clo_deal_engine.waterfall_strategy.setup_deal.assert_called_once()


class TestAccountManagement:
    """Test account management functionality"""
    
    def test_account_creation(self):
        """Test account creation and operations"""
        account = Account(AccountType.COLLECTION)
        
        assert account.account_type == AccountType.COLLECTION
        assert account.interest_balance == Decimal('0')
        assert account.principal_balance == Decimal('0')
        
        # Test adding cash
        account.add(CashType.INTEREST, Decimal('1000000'))
        account.add(CashType.PRINCIPAL, Decimal('5000000'))
        
        assert account.interest_proceeds == Decimal('1000000')
        assert account.principal_proceeds == Decimal('5000000')
        assert account.total_proceeds == Decimal('6000000')
    
    def test_account_setup_with_initial_balances(self, clo_deal_engine):
        """Test account setup with initial balances"""
        initial_balances = {
            AccountType.RAMP_UP: (Decimal('0'), Decimal('10000000')),
            AccountType.INTEREST_RESERVE: (Decimal('0'), Decimal('5000000'))
        }
        
        clo_deal_engine.setup_accounts(initial_balances)
        
        # Check initial balances set
        ramp_up = clo_deal_engine.accounts[AccountType.RAMP_UP]
        assert ramp_up.principal_proceeds == Decimal('10000000')
        
        interest_reserve = clo_deal_engine.accounts[AccountType.INTEREST_RESERVE]
        assert interest_reserve.principal_proceeds == Decimal('5000000')


class TestPeriodCalculations:
    """Test period-specific calculations"""
    
    def test_reinvestment_calculation(self, clo_deal_engine):
        """Test reinvestment amount calculation"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Set some principal proceeds
        clo_deal_engine.principal_proceeds[1] = Decimal('20000000')
        
        # Test pre-reinvestment period (100% of all principal)
        reinvestment = clo_deal_engine.calculate_reinvestment_amount(1, liquidate=False)
        assert reinvestment == Decimal('20000000')  # 100% of principal
        
        # Test post-reinvestment period (would need to mock unscheduled principal)
        # For now, test liquidation scenario
        reinvestment_liquidate = clo_deal_engine.calculate_reinvestment_amount(1, liquidate=True)
        assert reinvestment_liquidate == Decimal('0')  # No reinvestment when liquidating
    
    def test_period_calculation_basic(self, clo_deal_engine):
        """Test basic period calculation"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Add some cash to collection account
        collection_account = clo_deal_engine.accounts[AccountType.COLLECTION]
        collection_account.add(CashType.INTEREST, Decimal('3000000'))
        collection_account.add(CashType.PRINCIPAL, Decimal('10000000'))
        
        # Calculate first period
        clo_deal_engine.calculate_period(1)
        
        # Check LIBOR rate set
        assert clo_deal_engine.libor_rates[1] > 0
        
        # Check proceeds extracted
        assert clo_deal_engine.interest_proceeds[1] >= Decimal('3000000')
        assert clo_deal_engine.principal_proceeds[1] >= Decimal('10000000')
        
        # Check liability calculators called (mock would track this)
        # In real implementation, verify interest calculations occurred


class TestWaterfallIntegration:
    """Test waterfall strategy integration"""
    
    def test_waterfall_setup_integration(self, clo_deal_engine):
        """Test waterfall strategy setup integration"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Verify waterfall setup was called with correct parameters
        strategy = clo_deal_engine.waterfall_strategy
        strategy.setup_deal.assert_called_once()
        
        # Check setup call had payment dates
        call_args = strategy.setup_deal.call_args
        assert call_args is not None
        assert 'payment_dates' in call_args.kwargs or len(call_args.args) > 0
    
    def test_waterfall_execution_methods(self, clo_deal_engine):
        """Test waterfall execution method calls"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Mock some proceeds
        clo_deal_engine.interest_proceeds[1] = Decimal('5000000')
        clo_deal_engine.principal_proceeds[1] = Decimal('15000000')
        clo_deal_engine.notes_payable[1] = Decimal('0')
        
        # Test interest waterfall
        clo_deal_engine._execute_interest_waterfall(1)
        clo_deal_engine.waterfall_strategy.execute_interest_waterfall.assert_called_once()
        
        # Test principal waterfall
        clo_deal_engine._execute_principal_waterfall(1, Decimal('10000000'))
        clo_deal_engine.waterfall_strategy.execute_principal_waterfall.assert_called_once()
        
        # Test note payment sequence
        clo_deal_engine._execute_note_payment_sequence(1)
        clo_deal_engine.waterfall_strategy.execute_note_payment_sequence.assert_called_once()


class TestOutputGeneration:
    """Test output generation functionality"""
    
    def test_deal_output_generation(self, clo_deal_engine):
        """Test deal output report generation"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Set some calculated values
        clo_deal_engine.last_calculated_period = 2
        clo_deal_engine.interest_proceeds[1] = Decimal('5000000')
        clo_deal_engine.principal_proceeds[1] = Decimal('20000000')
        clo_deal_engine.notes_payable[1] = Decimal('18000000')
        clo_deal_engine.reinvestment_amounts[1] = Decimal('15000000')
        clo_deal_engine.libor_rates[1] = Decimal('0.05')
        
        output = clo_deal_engine.generate_deal_output()
        
        # Check output structure
        assert len(output) >= 2  # Header + at least one data row
        
        # Check header
        header = output[0]
        expected_headers = [
            "Period", "Payment Date", "Collection Begin Date", "Collection End Date",
            "Interest Proceeds", "Principal Proceeds", "Payment of Principal", 
            "Proceeds Reinvested", "LIBOR"
        ]
        assert header == expected_headers
        
        # Check first data row
        if len(output) > 1:
            first_row = output[1]
            assert first_row[0] == 1  # Period
            assert first_row[4] == 5000000.0  # Interest proceeds
            assert first_row[5] == 20000000.0  # Principal proceeds
            assert "%" in first_row[8]  # LIBOR formatted as percentage


class TestLiquidationLogic:
    """Test liquidation and call logic"""
    
    def test_liquidation_triggers(self, clo_deal_engine):
        """Test liquidation trigger conditions"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Test maturity trigger
        last_period = len(clo_deal_engine.payment_dates) - 1
        should_liquidate = clo_deal_engine._check_liquidation_triggers(last_period)
        assert should_liquidate  # Should liquidate before maturity
        
        # Test early period (should not liquidate)
        should_liquidate_early = clo_deal_engine._check_liquidation_triggers(1)
        assert not should_liquidate_early  # Should not liquidate early periods


class TestRiskMeasures:
    """Test risk measure calculations"""
    
    def test_risk_measure_calculation(self, clo_deal_engine):
        """Test risk measure calculation for liabilities"""
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Mock yield curve
        clo_deal_engine.yield_curve = Mock()
        
        # Calculate risk measures
        clo_deal_engine.calculate_risk_measures()
        
        # Verify calculators were called
        # In real implementation, check that risk measures were calculated
        # for each liability
        assert len(clo_deal_engine.liability_calculators) > 0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_deal_dates_error(self, session, test_clo_deal):
        """Test error when deal dates not set"""
        engine = CLODealEngine(test_clo_deal, session)
        
        with pytest.raises(ValueError, match="Deal dates must be set"):
            engine.calculate_payment_dates()
    
    def test_missing_payment_dates_error(self, clo_deal_engine):
        """Test error when payment dates not calculated"""
        with pytest.raises(ValueError, match="Payment dates must be calculated"):
            clo_deal_engine.deal_setup()
    
    def test_empty_liabilities_handling(self, session, test_clo_deal, test_deal_dates):
        """Test handling of empty liabilities"""
        engine = CLODealEngine(test_clo_deal, session)
        engine.setup_deal_dates(test_deal_dates)
        engine.setup_accounts()
        engine.setup_liabilities({})  # Empty liabilities
        
        # Should not crash
        engine.calculate_payment_dates()
        engine.deal_setup()
        
        assert len(engine.liability_calculators) == 0


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def test_simple_deal_execution(self, clo_deal_engine):
        """Test simple complete deal execution"""
        # Setup some initial cash
        collection = clo_deal_engine.accounts[AccountType.COLLECTION]
        collection.add(CashType.INTEREST, Decimal('5000000'))
        collection.add(CashType.PRINCIPAL, Decimal('20000000'))
        
        # Note: Full execution would require all components implemented
        # For now, test setup and initial calculations
        clo_deal_engine.calculate_payment_dates()
        clo_deal_engine.deal_setup()
        
        # Verify basic setup completed
        assert len(clo_deal_engine.payment_dates) > 0
        assert len(clo_deal_engine.liability_calculators) > 0
        assert clo_deal_engine.waterfall_strategy.setup_deal.called
        
        # Test first period calculation
        clo_deal_engine.calculate_period(1)
        
        assert clo_deal_engine.libor_rates[1] > 0
        assert clo_deal_engine.interest_proceeds[1] >= 0
        assert clo_deal_engine.principal_proceeds[1] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])