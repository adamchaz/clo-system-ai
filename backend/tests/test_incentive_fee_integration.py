"""
Test suite for Incentive Fee Integration with CLO Deal Engine

Tests the complete integration of incentive fee system with CLO Deal Engine
to ensure seamless operation and accurate fee calculations.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.core.database import Base
from app.models.clo_deal_engine import (
    CLODealEngine,
    DealDates,
    ReinvestmentInfo as CLOReinvestmentInfo,
    AccountType,
    CashType
)
from app.models.clo_deal import CLODeal
from app.services.incentive_fee import IncentiveFee, IncentiveFeeService
from app.models.incentive_fee import (
    IncentiveFeeStructure,
    SubordinatedPayment,
    IncentiveFeeCalculation
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
    """Create sample CLO deal for incentive fee testing"""
    return CLODeal(
        deal_id="INCENTIVE_TEST_001",
        deal_name="Test CLO for Incentive Fee",
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
def sample_subordinated_payments():
    """Sample historical subordinated payments"""
    return {
        date(2024, 4, 15): 1000000.0,   # $1M
        date(2024, 7, 15): 1200000.0,   # $1.2M
        date(2024, 10, 15): 950000.0,   # $950K
        date(2025, 1, 15): 1100000.0    # $1.1M
    }


@pytest.fixture
def clo_deal_engine_with_incentive_fee(integrated_db, sample_clo_deal, sample_deal_dates, 
                                       sample_subordinated_payments):
    """Create CLO Deal Engine with incentive fee enabled"""
    # Create deal engine
    deal_engine = CLODealEngine(sample_clo_deal, integrated_db, enable_account_persistence=True)
    
    # Setup components
    deal_engine.setup_deal_dates(sample_deal_dates)
    deal_engine.setup_accounts()
    
    # Setup incentive fee with custom parameters
    deal_engine.setup_incentive_fee(
        enable=True,
        hurdle_rate=0.08,  # 8%
        incentive_fee_rate=0.20,  # 20%
        fee_structure_name="Test Incentive Fee",
        subordinated_payments=sample_subordinated_payments
    )
    
    return deal_engine


class TestIncentiveFeeSetupIntegration:
    """Test incentive fee setup integration with CLO Deal Engine"""
    
    def test_incentive_fee_setup_integration(self, clo_deal_engine_with_incentive_fee):
        """Test incentive fee setup integrates correctly with CLO Deal Engine"""
        deal_engine = clo_deal_engine_with_incentive_fee
        
        # Verify incentive fee is properly configured
        assert deal_engine.enable_incentive_fee == True
        assert deal_engine.incentive_fee is not None
        assert deal_engine.incentive_fee_service is not None
        assert deal_engine.incentive_fee_structure_id is not None
        
        # Check incentive fee parameters
        assert deal_engine.incentive_fee.cls_fee_hurdle_rate == 0.08
        assert deal_engine.incentive_fee.cls_incent_fee == 0.20
        assert deal_engine.incentive_fee._is_setup == True
        assert deal_engine.incentive_fee._is_deal_setup == True
        
        # Verify database persistence
        structure = integrated_db.query(IncentiveFeeStructure).filter_by(
            fee_structure_id=deal_engine.incentive_fee_structure_id
        ).first()
        assert structure is not None
        assert structure.deal_id == deal_engine.deal.deal_id
    
    def test_incentive_fee_disabled_behavior(self, integrated_db, sample_clo_deal, sample_deal_dates):
        """Test behavior when incentive fee is disabled"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        deal_engine.setup_accounts()
        
        # Setup incentive fee as disabled
        deal_engine.setup_incentive_fee(enable=False)
        
        # Verify disabled state
        assert deal_engine.enable_incentive_fee == False
        assert deal_engine.incentive_fee is None
        assert deal_engine.incentive_fee_service is None
        assert deal_engine.incentive_fee_structure_id is None
        
        # Should return default values for disabled state
        summary = deal_engine.get_incentive_fee_summary()
        assert summary['incentive_fee_enabled'] == False
        assert summary['total_fees_paid'] == 0.0
        assert summary['threshold_reached'] == False
    
    def test_load_existing_incentive_fee_structure(self, integrated_db, sample_clo_deal, 
                                                   sample_deal_dates, sample_subordinated_payments):
        """Test loading existing incentive fee structure"""
        # Create initial structure
        deal_engine1 = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine1.setup_deal_dates(sample_deal_dates)
        deal_engine1.setup_incentive_fee(
            hurdle_rate=0.10,
            incentive_fee_rate=0.25,
            subordinated_payments=sample_subordinated_payments
        )
        
        original_structure_id = deal_engine1.incentive_fee_structure_id
        
        # Create new engine and load existing structure
        deal_engine2 = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine2.setup_deal_dates(sample_deal_dates)
        deal_engine2.load_incentive_fee_structure(original_structure_id)
        
        # Verify loaded correctly
        assert deal_engine2.enable_incentive_fee == True
        assert deal_engine2.incentive_fee_structure_id == original_structure_id
        assert deal_engine2.incentive_fee.cls_fee_hurdle_rate == 0.10
        assert deal_engine2.incentive_fee.cls_incent_fee == 0.25
    
    def test_incentive_fee_setup_without_deal_dates(self, integrated_db, sample_clo_deal):
        """Test incentive fee setup behavior without deal dates"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        
        # Setup incentive fee without deal dates
        deal_engine.setup_incentive_fee(hurdle_rate=0.08, incentive_fee_rate=0.20)
        
        # Should create incentive fee instance but not complete deal setup
        assert deal_engine.enable_incentive_fee == True
        assert deal_engine.incentive_fee is not None
        assert deal_engine.incentive_fee._is_setup == True
        assert deal_engine.incentive_fee._is_deal_setup == False  # Should be False without deal dates


class TestIncentiveFeeCalculationIntegration:
    """Test incentive fee calculation integration within deal processing"""
    
    def test_process_incentive_fee_for_period(self, clo_deal_engine_with_incentive_fee):
        """Test processing incentive fee for a specific period"""
        deal_engine = clo_deal_engine_with_incentive_fee
        
        # Calculate payment dates first
        deal_engine.calculate_payment_dates()
        
        # Process incentive fee for period 2
        period = 2
        deal_engine.process_incentive_fee_for_period(period)
        
        # Should have called calc() on the incentive fee
        # Verify that current calculation is setup
        assert deal_engine.incentive_fee.cls_curr_date is not None
        
        # Verify period calculation was setup
        if period < len(deal_engine.incentive_fee.cls_threshold):
            # Threshold should be calculated
            assert deal_engine.incentive_fee.cls_threshold[period] != 0.0 or deal_engine.incentive_fee.cls_threshold_reach
    
    def test_record_subordinated_payment_without_threshold(self, clo_deal_engine_with_incentive_fee):
        """Test recording subordinated payment when threshold not reached"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process period setup
        period = 2
        deal_engine.process_incentive_fee_for_period(period)
        
        # Ensure threshold not reached initially
        deal_engine.incentive_fee.cls_threshold_reach = False
        
        # Record subordinated payment
        payment_amount = 500000.0  # $500k
        net_payment = deal_engine.record_subordinated_payment(period, payment_amount)
        
        # Should return full amount (no fee deduction)
        assert net_payment == payment_amount
        assert deal_engine.incentive_fee.cls_curr_sub_payments == payment_amount
    
    def test_record_subordinated_payment_with_threshold_reached(self, clo_deal_engine_with_incentive_fee):
        """Test recording subordinated payment when threshold is reached"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process period setup
        period = 2
        deal_engine.process_incentive_fee_for_period(period)
        
        # Force threshold reached
        deal_engine.incentive_fee.cls_threshold_reach = True
        
        # Record subordinated payment
        payment_amount = 1000000.0  # $1M
        net_payment = deal_engine.record_subordinated_payment(period, payment_amount)
        
        # Should deduct 20% fee
        expected_fee = payment_amount * 0.20
        expected_net = payment_amount * 0.80
        
        assert abs(net_payment - expected_net) < 0.01
        assert abs(deal_engine.incentive_fee.cls_curr_incetive_payments - expected_fee) < 0.01
    
    def test_finalize_incentive_fee_period(self, clo_deal_engine_with_incentive_fee):
        """Test finalizing incentive fee calculations for a period"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process complete period cycle
        period = 2
        deal_engine.process_incentive_fee_for_period(period)
        deal_engine.record_subordinated_payment(period, 800000.0)
        
        initial_period = deal_engine.incentive_fee.cls_period
        
        # Finalize period
        deal_engine.finalize_incentive_fee_period(period)
        
        # Should have advanced period and reset current amounts
        assert deal_engine.incentive_fee.cls_period == initial_period + 1
        assert deal_engine.incentive_fee.cls_curr_sub_payments == 0.0
        assert deal_engine.incentive_fee.cls_curr_incetive_payments == 0.0
        
        # Should have updated subordinated payments dictionary
        assert deal_engine.incentive_fee.cls_curr_date in deal_engine.incentive_fee.cls_sub_payments_dict
    
    def test_threshold_calculation_integration(self, clo_deal_engine_with_incentive_fee):
        """Test threshold calculation integration"""
        deal_engine = clo_deal_engine_with_incentive_fee
        
        # Get current threshold
        threshold = deal_engine.get_current_incentive_fee_threshold()
        
        # Should match direct incentive fee calculation
        direct_threshold = deal_engine.incentive_fee.incentive_fee_threshold()
        assert abs(threshold - direct_threshold) < 0.01
        
        # Test threshold reached status
        threshold_reached = deal_engine.is_incentive_fee_threshold_reached()
        assert threshold_reached == deal_engine.incentive_fee.cls_threshold_reach


class TestIncentiveFeeCompleteWorkflow:
    """Test complete incentive fee workflow integration"""
    
    def test_multiple_period_incentive_fee_workflow(self, clo_deal_engine_with_incentive_fee):
        """Test incentive fee workflow across multiple periods"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process multiple periods
        period_payments = [750000.0, 1200000.0, 900000.0, 1500000.0]
        total_fees_paid = 0.0
        
        for i, payment_amount in enumerate(period_payments, 1):
            period = i + 1
            
            # Process period
            deal_engine.process_incentive_fee_for_period(period)
            
            # Record payment
            net_payment = deal_engine.record_subordinated_payment(period, payment_amount)
            
            # Calculate fee for this period
            period_fee = payment_amount - net_payment
            total_fees_paid += period_fee
            
            # Finalize period
            deal_engine.finalize_incentive_fee_period(period)
        
        # Verify final state
        final_summary = deal_engine.get_incentive_fee_summary()
        assert final_summary['incentive_fee_enabled'] == True
        assert final_summary['current_period'] == len(period_payments) + 1
        
        # Total fees should match accumulated fees
        assert abs(final_summary['total_fees_paid'] - total_fees_paid) < 0.01
    
    def test_incentive_fee_summary_generation(self, clo_deal_engine_with_incentive_fee):
        """Test comprehensive incentive fee summary"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process a few periods
        for period in range(2, 5):
            deal_engine.process_incentive_fee_for_period(period)
            deal_engine.record_subordinated_payment(period, 1000000.0)
            deal_engine.finalize_incentive_fee_period(period)
        
        # Get comprehensive summary
        summary = deal_engine.get_incentive_fee_summary()
        
        # Verify summary structure
        expected_keys = [
            'incentive_fee_enabled', 'fee_structure_id', 'hurdle_rate', 'incentive_fee_rate',
            'threshold_reached', 'current_period', 'total_fees_paid', 
            'cumulative_discounted_payments', 'closing_date', 'output_data',
            'subordinated_payments_count', 'period_calculations'
        ]
        
        for key in expected_keys:
            assert key in summary
        
        # Verify values
        assert summary['incentive_fee_enabled'] == True
        assert summary['hurdle_rate'] == 0.08
        assert summary['incentive_fee_rate'] == 0.20
        assert summary['current_period'] > 1
        assert len(summary['period_calculations']) > 0
        
        # Verify output data format (VBA equivalent)
        output_data = summary['output_data']
        assert len(output_data) > 1  # Header + data rows
        assert output_data[0] == ["Threshold", "Fee Paid", "IRR"]  # VBA header
    
    def test_irr_calculation_integration(self, clo_deal_engine_with_incentive_fee):
        """Test IRR calculation integration within CLO context"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process periods with varying payment amounts
        payments = [800000.0, 1200000.0, 950000.0, 1300000.0, 1100000.0]
        
        for i, payment in enumerate(payments, 1):
            period = i + 1
            deal_engine.process_incentive_fee_for_period(period)
            deal_engine.record_subordinated_payment(period, payment)
            deal_engine.finalize_incentive_fee_period(period)
        
        # Check IRR calculations
        summary = deal_engine.get_incentive_fee_summary()
        
        # Should have IRR calculations for processed periods
        for calc in summary['period_calculations']:
            if calc['period'] > 1:  # IRR needs multiple cash flows
                assert isinstance(calc['irr'], (int, float))
        
        # Verify VBA output format includes IRR
        output_data = summary['output_data']
        if len(output_data) > 1:
            for row in output_data[1:]:  # Skip header
                irr_value = row[2]  # IRR column
                assert "%" in str(irr_value)  # Should be formatted as percentage


class TestIncentiveFeeDatabaseIntegration:
    """Test database persistence for incentive fee within CLO context"""
    
    def test_incentive_fee_persistence_through_periods(self, clo_deal_engine_with_incentive_fee):
        """Test incentive fee data persists correctly through period processing"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        original_structure_id = deal_engine.incentive_fee_structure_id
        
        # Process multiple periods
        for period in range(2, 5):
            deal_engine.process_incentive_fee_for_period(period)
            deal_engine.record_subordinated_payment(period, 1000000.0)
            deal_engine.finalize_incentive_fee_period(period)
        
        # Verify database persistence
        structure = deal_engine.session.query(IncentiveFeeStructure).filter_by(
            fee_structure_id=original_structure_id
        ).first()
        
        assert structure is not None
        assert structure.deal_id == deal_engine.deal.deal_id
        
        # Verify subordinated payments were recorded
        payments = deal_engine.session.query(SubordinatedPayment).filter_by(
            fee_structure_id=original_structure_id
        ).all()
        assert len(payments) > 0  # Should have historical + new payments
        
        # Verify calculations were recorded
        calculations = deal_engine.session.query(IncentiveFeeCalculation).filter_by(
            fee_structure_id=original_structure_id
        ).all()
        assert len(calculations) > 0  # Should have period calculations
    
    def test_incentive_fee_state_recovery(self, integrated_db, sample_clo_deal, 
                                          sample_deal_dates, sample_subordinated_payments):
        """Test recovering incentive fee state from database"""
        # Create and process initial deal
        deal_engine1 = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine1.setup_deal_dates(sample_deal_dates)
        deal_engine1.setup_incentive_fee(
            hurdle_rate=0.08,
            incentive_fee_rate=0.20,
            subordinated_payments=sample_subordinated_payments
        )
        deal_engine1.calculate_payment_dates()
        
        # Process some periods
        for period in range(2, 4):
            deal_engine1.process_incentive_fee_for_period(period)
            deal_engine1.record_subordinated_payment(period, 900000.0)
            deal_engine1.finalize_incentive_fee_period(period)
        
        original_structure_id = deal_engine1.incentive_fee_structure_id
        original_summary = deal_engine1.get_incentive_fee_summary()
        
        # Create new engine and recover state
        deal_engine2 = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine2.setup_deal_dates(sample_deal_dates)
        deal_engine2.load_incentive_fee_structure(original_structure_id)
        
        # Verify recovered state matches original
        recovered_summary = deal_engine2.get_incentive_fee_summary()
        
        assert recovered_summary['fee_structure_id'] == original_summary['fee_structure_id']
        assert recovered_summary['hurdle_rate'] == original_summary['hurdle_rate']
        assert recovered_summary['incentive_fee_rate'] == original_summary['incentive_fee_rate']
        assert recovered_summary['threshold_reached'] == original_summary['threshold_reached']
        assert abs(recovered_summary['total_fees_paid'] - original_summary['total_fees_paid']) < 0.01


class TestIncentiveFeeEdgeCases:
    """Test edge cases for incentive fee integration"""
    
    def test_incentive_fee_with_no_subordinated_payments(self, integrated_db, sample_clo_deal, sample_deal_dates):
        """Test incentive fee with no historical subordinated payments"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        
        # Setup with no historical payments
        deal_engine.setup_incentive_fee(
            hurdle_rate=0.08,
            incentive_fee_rate=0.20,
            subordinated_payments={}  # Empty
        )
        
        assert deal_engine.enable_incentive_fee == True
        assert len(deal_engine.incentive_fee.cls_sub_payments_dict) == 0
        assert deal_engine.incentive_fee.cls_cum_dicounted_sub_payments == 0.0
        assert deal_engine.incentive_fee.cls_threshold_reach == False
    
    def test_incentive_fee_disabled_methods(self, integrated_db, sample_clo_deal, sample_deal_dates):
        """Test incentive fee methods when system is disabled"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        deal_engine.setup_incentive_fee(enable=False)
        
        # All methods should handle disabled state gracefully
        deal_engine.process_incentive_fee_for_period(2)  # Should not error
        
        # Should return original amounts
        net_payment = deal_engine.record_subordinated_payment(2, 1000000.0)
        assert net_payment == 1000000.0
        
        # Should not error on finalization
        deal_engine.finalize_incentive_fee_period(2)
        
        # Should return zero/default values
        assert deal_engine.get_current_incentive_fee_threshold() == 0.0
        assert deal_engine.is_incentive_fee_threshold_reached() == False
    
    def test_incentive_fee_with_extreme_values(self, integrated_db, sample_clo_deal, sample_deal_dates):
        """Test incentive fee with extreme parameter values"""
        deal_engine = CLODealEngine(sample_clo_deal, integrated_db)
        deal_engine.setup_deal_dates(sample_deal_dates)
        
        # Test with very high hurdle rate and fee
        deal_engine.setup_incentive_fee(
            hurdle_rate=0.25,  # 25% hurdle
            incentive_fee_rate=0.50,  # 50% fee
            subordinated_payments={date(2024, 1, 15): -1000000.0}  # Negative historical payment
        )
        deal_engine.calculate_payment_dates()
        
        # Should handle extreme values without error
        deal_engine.process_incentive_fee_for_period(2)
        
        # With negative historical payment, threshold should be negative
        assert deal_engine.incentive_fee.cls_cum_dicounted_sub_payments < 0
        
        # Test large payment
        net_payment = deal_engine.record_subordinated_payment(2, 10000000.0)  # $10M
        
        if deal_engine.incentive_fee.cls_threshold_reach:
            # Should deduct 50% fee
            expected_net = 10000000.0 * 0.50
            assert abs(net_payment - expected_net) < 1.0
        
    def test_incentive_fee_period_date_edge_cases(self, clo_deal_engine_with_incentive_fee):
        """Test edge cases with period date calculations"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Test processing period beyond available payment dates
        far_future_period = 1000
        deal_engine.process_incentive_fee_for_period(far_future_period)  # Should not error
        
        # Test with period 0 or negative
        deal_engine.process_incentive_fee_for_period(0)  # Should handle gracefully
        
        # Normal period should work
        deal_engine.process_incentive_fee_for_period(2)
        assert deal_engine.incentive_fee.cls_curr_date is not None
    
    def test_incentive_fee_memory_management(self, clo_deal_engine_with_incentive_fee):
        """Test memory management for large number of periods"""
        deal_engine = clo_deal_engine_with_incentive_fee
        deal_engine.calculate_payment_dates()
        
        # Process many periods (stress test)
        for period in range(2, 50):  # 48 periods
            deal_engine.process_incentive_fee_for_period(period)
            deal_engine.record_subordinated_payment(period, 1000000.0)
            deal_engine.finalize_incentive_fee_period(period)
        
        # Should still function correctly
        summary = deal_engine.get_incentive_fee_summary()
        assert summary['current_period'] == 50
        assert len(summary['period_calculations']) == 48  # All processed periods
        
        # Arrays should be properly sized
        assert len(deal_engine.incentive_fee.cls_threshold) >= 50
        assert len(deal_engine.incentive_fee.cls_fee_paid) >= 50
        assert len(deal_engine.incentive_fee.cls_irr) >= 50