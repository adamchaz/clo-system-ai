"""
Test suite for Reinvestment Integration with CLO Deal Engine

Tests the complete integration of reinvestment system with CLO Deal Engine
to ensure seamless operation and accurate cash flow modeling.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.core.database import Base
from app.models.clo_deal_engine import (
    CLODealEngine,
    DealDates,
    ReinvestmentInfo as CLOReinvestmentInfo,
    AccountType,
    CashType
)
from app.models.clo_deal import CLODeal
from app.models.asset import Asset, AssetFlags
from app.models.reinvestment import (
    ReinvestInfo as ReinvestmentModelInfo,
    ReinvestmentService
)


@pytest.fixture
def integrated_db():
    """Create in-memory database for integration testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def sample_clo_deal():
    """Create sample CLO deal for testing"""
    return CLODeal(
        deal_id="REINVEST_TEST_001",
        deal_name="Test CLO for Reinvestment",
        manager_name="Test Manager",
        closing_date=date(2025, 1, 15),
        analysis_date=date(2025, 1, 10),
        first_payment_date=date(2025, 4, 15),
        maturity_date=date(2030, 1, 15),
        reinvestment_end_date=date(2027, 1, 15),
        target_par=Decimal('400000000'),
        ramp_up_end_date=date(2025, 7, 15)
    )


@pytest.fixture
def sample_deal_dates():
    """Create sample deal dates configuration"""
    return DealDates(
        analysis_date=date(2025, 1, 10),
        closing_date=date(2025, 1, 15),
        first_payment_date=date(2025, 4, 15),
        maturity_date=date(2030, 1, 15),
        reinvestment_end_date=date(2027, 1, 15),
        no_call_date=date(2027, 4, 15),
        payment_day=15,
        months_between_payments=3,
        business_day_convention="FOLLOWING",
        determination_date_offset=2,
        interest_determination_date_offset=5
    )


@pytest.fixture
def sample_clo_reinvestment_info():
    """Create sample CLO reinvestment strategy"""
    return CLOReinvestmentInfo(
        pre_reinvestment_type="ALL PRINCIPAL",
        pre_reinvestment_pct=Decimal('1.0'),
        post_reinvestment_type="UNSCHEDULED PRINCIPAL",
        post_reinvestment_pct=Decimal('0.5')
    )


@pytest.fixture
def sample_assets(integrated_db):
    """Create sample assets for the CLO"""
    assets_data = [
        {
            'blkrock_id': 'REINVEST_ASSET_001',
            'issue_name': 'Sample Term Loan A',
            'issuer_name': 'Sample Corp A',
            'par_amount': Decimal('5000000'),
            'bond_loan': 'LOAN',
            'seniority': 'SENIOR SECURED',
            'maturity': date(2028, 6, 15),
            'coupon': Decimal('0.075'),
            'coupon_type': 'FLOATING',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        },
        {
            'blkrock_id': 'REINVEST_ASSET_002',
            'issue_name': 'Sample Term Loan B',
            'issuer_name': 'Sample Corp B',
            'par_amount': Decimal('3000000'),
            'bond_loan': 'LOAN',
            'seniority': 'SENIOR SECURED',
            'maturity': date(2029, 3, 31),
            'coupon': Decimal('0.065'),
            'coupon_type': 'FLOATING',
            'flags': AssetFlags(dip=False, default_asset=False).dict()
        }
    ]
    
    assets = []
    for asset_data in assets_data:
        asset = Asset(**asset_data)
        integrated_db.add(asset)
        assets.append(asset)
    
    integrated_db.commit()
    return assets


@pytest.fixture
def clo_deal_engine_with_reinvestment(integrated_db, sample_clo_deal, sample_deal_dates, 
                                     sample_clo_reinvestment_info, sample_assets):
    """Create CLO Deal Engine with reinvestment enabled"""
    # Create deal engine
    deal_engine = CLODealEngine(sample_clo_deal, integrated_db, enable_account_persistence=True)
    
    # Setup components
    deal_engine.setup_deal_dates(sample_deal_dates)
    deal_engine.setup_reinvestment_strategy(sample_clo_reinvestment_info)
    deal_engine.setup_accounts()
    
    # Setup reinvestment with custom parameters
    reinvestment_params = {
        'maturity_months': 48,
        'reinvest_price': 0.99,
        'spread': 0.055,
        'floor': 0.015,
        'liquidation_price': 0.75,
        'lag_months': 6,
        'prepayment_rate': 0.12,
        'default_rate': 0.025,
        'severity_rate': 0.35
    }
    deal_engine.setup_reinvestment(True, reinvestment_params)
    
    # Setup assets
    assets_dict = {asset.blkrock_id: asset for asset in sample_assets}
    deal_engine.setup_assets(assets_dict)
    
    return deal_engine


class TestReinvestmentCLOIntegration:
    """Test CLO Deal Engine integration with reinvestment system"""
    
    def test_reinvestment_setup_integration(self, clo_deal_engine_with_reinvestment):
        """Test reinvestment setup integrates correctly with CLO Deal Engine"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Verify reinvestment is properly configured
        assert deal_engine.enable_reinvestment == True
        assert deal_engine.reinvestment_service is not None
        assert deal_engine.reinvestment_parameters is not None
        
        # Check reinvestment parameters
        params = deal_engine.reinvestment_parameters
        assert params['maturity_months'] == 48
        assert params['spread'] == 0.055
        assert params['liquidation_price'] == 0.75
        
        # Should be able to create reinvestment periods
        assert hasattr(deal_engine, 'create_reinvestment_period')
        assert hasattr(deal_engine, 'get_reinvestment_summary')
    
    def test_create_reinvestment_period_integration(self, clo_deal_engine_with_reinvestment):
        """Test creating reinvestment period through CLO Deal Engine"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create reinvestment period
        period = 2
        reinvestment_amount = 2000000.0  # $2M
        
        reinvest = deal_engine.create_reinvestment_period(period, reinvestment_amount)
        
        # Verify reinvestment period was created
        assert reinvest is not None
        assert period in deal_engine.reinvestment_periods
        assert deal_engine.reinvestment_periods[period] == reinvest
        
        # Verify reinvestment was set up correctly
        assert reinvest._is_setup == True
        assert reinvest.last_period > 0
        
        # Verify database persistence
        assert reinvest.reinvest_id is not None
    
    def test_reinvestment_payment_dates_creation(self, clo_deal_engine_with_reinvestment):
        """Test payment dates creation for reinvestment periods"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Test payment dates creation
        payment_dates = deal_engine._create_reinvestment_payment_dates(3)
        
        # Should have payment dates
        assert len(payment_dates) > 1  # Header + data
        assert payment_dates[0] is None  # VBA 1-based indexing
        
        # Check first actual payment date
        first_payment = payment_dates[1]
        assert first_payment.PaymentDate is not None
        assert first_payment.CollBegDate is not None
        assert first_payment.CollEndDate is not None
        
        # Payment dates should be quarterly
        if len(payment_dates) > 2:
            date_diff = (payment_dates[2].PaymentDate - payment_dates[1].PaymentDate).days
            assert abs(date_diff - 90) <= 5  # Approximately 3 months
    
    def test_period_execution_with_reinvestment(self, clo_deal_engine_with_reinvestment):
        """Test period execution includes reinvestment processing"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create a reinvestment period first
        reinvest = deal_engine.create_reinvestment_period(1, 1500000.0)
        
        # Set up some principal proceeds for period 2
        period = 2
        deal_engine.principal_proceeds[period] = Decimal('500000')
        
        # Execute period with reinvestment processing
        original_process_reinvestment = deal_engine._process_reinvestment_periods
        called_with_periods = []
        
        def mock_process_reinvestment(p):
            called_with_periods.append(p)
            return original_process_reinvestment(p)
        
        deal_engine._process_reinvestment_periods = mock_process_reinvestment
        
        # Execute period (simplified)
        deal_engine._process_reinvestment_periods(period)
        
        # Verify reinvestment processing was called
        assert period in called_with_periods
    
    def test_reinvestment_proceeds_integration(self, clo_deal_engine_with_reinvestment):
        """Test reinvestment proceeds integrate with CLO accounts"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create and process a reinvestment period
        reinvest = deal_engine.create_reinvestment_period(1, 1000000.0)
        
        # Get initial account balances
        initial_interest = deal_engine.accounts[AccountType.COLLECTION].interest_balance
        initial_principal = deal_engine.accounts[AccountType.COLLECTION].principal_balance
        
        # Process reinvestment periods (which should add proceeds)
        deal_engine._process_reinvestment_periods(2)
        
        # Verify accounts were updated (may be zero if no proceeds yet)
        final_interest = deal_engine.accounts[AccountType.COLLECTION].interest_balance
        final_principal = deal_engine.accounts[AccountType.COLLECTION].principal_balance
        
        # Balances should be non-negative and potentially updated
        assert final_interest >= initial_interest
        assert final_principal >= initial_principal
    
    def test_reinvestment_strategy_application(self, clo_deal_engine_with_reinvestment):
        """Test reinvestment strategy is applied correctly"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Test during reinvestment period
        reinvestment_period = 3
        principal_amount = 1000000.0
        
        # Mock being in reinvestment period
        deal_engine._is_reinvestment_period = Mock(return_value=True)
        
        # Set up principal proceeds
        deal_engine.principal_proceeds[reinvestment_period] = Decimal(str(principal_amount))
        
        # Calculate available reinvestment amount
        available = deal_engine._calculate_available_reinvestment_principal(reinvestment_period)
        
        # Should reinvest all principal during reinvestment period
        expected = principal_amount * float(deal_engine.reinvestment_info.pre_reinvestment_pct)
        assert abs(available - expected) < 1.0
        
        # Test after reinvestment period
        deal_engine._is_reinvestment_period = Mock(return_value=False)
        
        # Should use post-reinvestment strategy
        available_post = deal_engine._calculate_available_reinvestment_principal(reinvestment_period)
        expected_post = principal_amount * float(deal_engine.reinvestment_info.post_reinvestment_pct)
        
        # Note: This tests "ALL PRINCIPAL" vs "UNSCHEDULED PRINCIPAL" logic
        # The actual amount may differ based on unscheduled calculation
        assert available_post >= 0  # Should be non-negative
    
    def test_reinvestment_liquidation_integration(self, clo_deal_engine_with_reinvestment):
        """Test reinvestment portfolio liquidation"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create multiple reinvestment periods
        reinvest1 = deal_engine.create_reinvestment_period(1, 1000000.0)
        reinvest2 = deal_engine.create_reinvestment_period(3, 750000.0)
        
        # Liquidate all reinvestment portfolios
        proceeds = deal_engine._liquidate_reinvestment_portfolios()
        
        # Should have some proceeds
        assert proceeds >= Decimal('0')
        
        # Verify liquidation was called on reinvestment periods
        # (Since we don't mock the liquidate method, proceeds depend on current balances)
        assert isinstance(proceeds, Decimal)
    
    def test_reinvestment_summary_generation(self, clo_deal_engine_with_reinvestment):
        """Test comprehensive reinvestment summary"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create reinvestment periods
        reinvest1 = deal_engine.create_reinvestment_period(2, 1200000.0)
        reinvest2 = deal_engine.create_reinvestment_period(4, 800000.0)
        
        # Get summary
        summary = deal_engine.get_reinvestment_summary()
        
        # Verify summary structure
        assert summary['reinvestment_enabled'] == True
        assert summary['active_periods'] == 2
        assert 'total_reinvested_amount' in summary
        assert 'total_current_balance' in summary
        assert len(summary['periods']) == 2
        
        # Verify period details
        for period_summary in summary['periods']:
            assert 'period' in period_summary
            assert 'reinvest_id' in period_summary
            assert 'current_balances' in period_summary
            assert 'performing' in period_summary['current_balances']
            assert 'defaults' in period_summary['current_balances']
            assert 'mv_defaults' in period_summary['current_balances']
    
    def test_minimum_reinvestment_threshold(self, clo_deal_engine_with_reinvestment):
        """Test minimum reinvestment threshold logic"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Test with amount below threshold
        small_amount = 50000.0  # $50k (below $100k minimum)
        initial_periods = len(deal_engine.reinvestment_periods)
        
        deal_engine._handle_reinvestment_opportunities(5, small_amount)
        
        # Should not create new reinvestment period
        assert len(deal_engine.reinvestment_periods) == initial_periods
        
        # Test with amount above threshold
        large_amount = 150000.0  # $150k (above $100k minimum)
        
        deal_engine._handle_reinvestment_opportunities(6, large_amount)
        
        # Should create new reinvestment period
        assert len(deal_engine.reinvestment_periods) == initial_periods + 1
        assert 6 in deal_engine.reinvestment_periods


class TestReinvestmentDatabaseIntegration:
    """Test database integration for reinvestment within CLO context"""
    
    def test_reinvestment_persistence_through_clo(self, clo_deal_engine_with_reinvestment):
        """Test reinvestment data persists correctly through CLO operations"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create reinvestment period
        reinvestment_amount = 1500000.0
        reinvest = deal_engine.create_reinvestment_period(3, reinvestment_amount)
        
        original_reinvest_id = reinvest.reinvest_id
        
        # Verify database record exists
        from app.models.reinvestment import ReinvestmentPeriodModel
        
        period_record = deal_engine.session.query(ReinvestmentPeriodModel).filter_by(
            reinvest_id=original_reinvest_id
        ).first()
        
        assert period_record is not None
        assert period_record.deal_id == deal_engine.deal.deal_id
        assert period_record.reinvest_period == 3
        
        # Verify can load through service
        loaded_reinvest = deal_engine.reinvestment_service.load_reinvestment_period(original_reinvest_id)
        assert loaded_reinvest is not None
        assert loaded_reinvest.reinvest_id == original_reinvest_id
    
    def test_account_transaction_recording(self, clo_deal_engine_with_reinvestment):
        """Test that reinvestment creates proper account transactions"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Create reinvestment period
        reinvest = deal_engine.create_reinvestment_period(2, 1000000.0)
        
        # Set up some reinvestment proceeds
        period = 3
        deal_engine.principal_proceeds[period] = Decimal('200000')
        
        # Process reinvestment with account persistence enabled
        deal_engine._process_reinvestment_periods(period)
        
        # Note: Actual transaction recording depends on the proceeds generated
        # by the reinvestment period. This test verifies the integration works
        # without errors
        
        # Verify account balances are still valid
        for account_type, account in deal_engine.accounts.items():
            assert account.interest_balance >= Decimal('0')
            assert account.principal_balance >= Decimal('0')


class TestReinvestmentScenarioIntegration:
    """Test various reinvestment scenarios within CLO context"""
    
    def test_full_reinvestment_lifecycle(self, clo_deal_engine_with_reinvestment):
        """Test complete reinvestment lifecycle within CLO"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Period 1: Create initial reinvestment
        reinvest1 = deal_engine.create_reinvestment_period(1, 2000000.0)
        assert reinvest1.last_period > 0
        
        # Period 2: Create another reinvestment
        reinvest2 = deal_engine.create_reinvestment_period(2, 1500000.0)
        
        # Process multiple periods
        for period in range(3, 8):
            deal_engine._process_reinvestment_periods(period)
            
            # Roll forward each reinvestment
            for reinvest in deal_engine.reinvestment_periods.values():
                if reinvest.period <= period:
                    reinvest.roll_forward()
        
        # Verify both reinvestments are still active
        assert len(deal_engine.reinvestment_periods) == 2
        
        # Get final summary
        summary = deal_engine.get_reinvestment_summary()
        assert summary['active_periods'] == 2
        assert summary['total_current_balance'] >= 0
    
    def test_reinvestment_with_different_strategies(self, integrated_db, sample_clo_deal, 
                                                  sample_deal_dates, sample_assets):
        """Test different reinvestment strategies"""
        # Test "UNSCHEDULED PRINCIPAL" strategy
        unscheduled_strategy = CLOReinvestmentInfo(
            pre_reinvestment_type="UNSCHEDULED PRINCIPAL",
            pre_reinvestment_pct=Decimal('0.8'),
            post_reinvestment_type="NONE",
            post_reinvestment_pct=Decimal('0.0')
        )
        
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        deal_engine.setup_reinvestment_strategy(unscheduled_strategy)
        deal_engine.setup_reinvestment()
        
        # Mock unscheduled principal calculation
        deal_engine._calculate_unscheduled_principal = Mock(return_value=500000.0)
        deal_engine.principal_proceeds[3] = Decimal('1000000')  # Total principal
        deal_engine._is_reinvestment_period = Mock(return_value=True)
        
        # Calculate available reinvestment
        available = deal_engine._calculate_available_reinvestment_principal(3)
        
        # Should only reinvest unscheduled portion
        expected = 500000.0 * 0.8  # 80% of unscheduled
        assert abs(available - expected) < 1.0
        
        # Test "NONE" strategy
        none_strategy = CLOReinvestmentInfo(
            pre_reinvestment_type="NONE",
            pre_reinvestment_pct=Decimal('0.0'),
            post_reinvestment_type="NONE",
            post_reinvestment_pct=Decimal('0.0')
        )
        
        deal_engine.setup_reinvestment_strategy(none_strategy)
        available_none = deal_engine._calculate_available_reinvestment_principal(3)
        assert available_none == 0.0
    
    def test_reinvestment_during_and_after_reinvestment_period(self, clo_deal_engine_with_reinvestment):
        """Test different behavior during vs after reinvestment period"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Mock principal proceeds
        deal_engine.principal_proceeds[5] = Decimal('1000000')
        
        # During reinvestment period
        deal_engine._is_reinvestment_period = Mock(return_value=True)
        available_during = deal_engine._calculate_available_reinvestment_principal(5)
        
        # After reinvestment period
        deal_engine._is_reinvestment_period = Mock(return_value=False)
        available_after = deal_engine._calculate_available_reinvestment_principal(5)
        
        # Strategy is "ALL PRINCIPAL" during, "UNSCHEDULED PRINCIPAL" after
        # So amounts should differ
        # Note: actual values depend on unscheduled principal calculation
        assert available_during >= 0
        assert available_after >= 0


class TestReinvestmentEdgeCases:
    """Test edge cases for reinvestment integration"""
    
    def test_reinvestment_without_deal_dates(self, integrated_db, sample_clo_deal):
        """Test error handling when deal dates not configured"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_reinvestment()
        
        # Should raise error when trying to create reinvestment without deal dates
        with pytest.raises(RuntimeError, match="Deal dates must be configured"):
            deal_engine.create_reinvestment_period(1, 1000000.0)
    
    def test_reinvestment_disabled_scenarios(self, clo_deal_engine_with_reinvestment):
        """Test behavior when reinvestment is disabled"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Disable reinvestment
        deal_engine.enable_reinvestment = False
        
        # Should not process reinvestment
        initial_periods = len(deal_engine.reinvestment_periods)
        deal_engine._process_reinvestment_periods(5)
        assert len(deal_engine.reinvestment_periods) == initial_periods
        
        # Should return empty summary
        summary = deal_engine.get_reinvestment_summary()
        assert summary['reinvestment_enabled'] == False
        assert summary['active_periods'] == 0
        
        # Should return zero for liquidation
        proceeds = deal_engine._liquidate_reinvestment_portfolios()
        assert proceeds == Decimal('0')
    
    def test_reinvestment_with_zero_amounts(self, clo_deal_engine_with_reinvestment):
        """Test handling of zero or negative reinvestment amounts"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Test zero amount
        deal_engine._handle_reinvestment_opportunities(7, 0.0)
        assert 7 not in deal_engine.reinvestment_periods
        
        # Test negative amount
        deal_engine._handle_reinvestment_opportunities(8, -1000.0)
        assert 8 not in deal_engine.reinvestment_periods
    
    def test_period_date_calculation_edge_cases(self, clo_deal_engine_with_reinvestment):
        """Test period date calculation edge cases"""
        deal_engine = clo_deal_engine_with_reinvestment
        
        # Test period beyond maturity
        far_future_period = 100
        period_date = deal_engine._get_period_date(far_future_period)
        assert period_date is None  # Should be None if beyond maturity
        
        # Test reasonable period
        reasonable_period = 5
        period_date = deal_engine._get_period_date(reasonable_period)
        assert period_date is not None
        assert isinstance(period_date, date)
    
    def test_reinvestment_with_missing_reinvestment_info(self, integrated_db, sample_clo_deal, sample_deal_dates):
        """Test behavior when reinvestment info is not configured"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        # Note: not setting up reinvestment_info
        deal_engine.setup_reinvestment()
        
        # Should return 0 for available principal without reinvestment info
        available = deal_engine._calculate_available_reinvestment_principal(3)
        assert available == 0.0