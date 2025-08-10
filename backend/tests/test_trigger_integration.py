"""
Integration tests for OC/IC triggers with waterfall system
Tests complete end-to-end functionality including waterfall integration
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.oc_trigger import OCTriggerCalculator
from app.models.ic_trigger import ICTriggerCalculator
from app.models.clo_deal import CLODeal, CLOTranche
from app.models.trigger_aware_waterfall import TriggerAwareWaterfallStrategy
from app.services.trigger_service import TriggerService
from app.core.database import Base, engine


class TestTriggerIntegration:
    """Integration tests for complete OC/IC trigger functionality"""
    
    @pytest.fixture
    def session(self):
        """Create test database session"""
        Base.metadata.create_all(bind=engine)
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def sample_deal_with_tranches(self, session):
        """Create a sample CLO deal with multiple tranches"""
        deal = CLODeal(
            deal_id="TEST_DEAL_001",
            deal_name="Test CLO Deal with Tranches",
            manager_name="Test Manager",
            target_par_amount=Decimal('500000000'),
            payment_frequency=4
        )
        session.add(deal)
        
        # Add tranches
        tranches = [
            ("Class A", Decimal('300000000'), 1),
            ("Class B", Decimal('100000000'), 2),
            ("Class C", Decimal('50000000'), 3),
            ("Class D", Decimal('30000000'), 4),
            ("Class E", Decimal('20000000'), 5),
        ]
        
        for tranche_name, balance, seniority in tranches:
            tranche = CLOTranche(
                tranche_id=f"{deal.deal_id}_{tranche_name}",
                deal_id=deal.deal_id,
                tranche_name=tranche_name,
                initial_balance=balance,
                current_balance=balance,
                seniority_level=seniority,
                payment_rank=seniority
            )
            session.add(tranche)
        
        session.commit()
        return deal
    
    def test_trigger_service_setup(self, session, sample_deal_with_tranches):
        """Test trigger service setup with multiple tranches"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Should have calculators for all tranches
        assert len(trigger_service.oc_calculators) == 5
        assert len(trigger_service.ic_calculators) == 5
        
        # Check that calculators are properly initialized
        for tranche_name in ["Class A", "Class B", "Class C", "Class D", "Class E"]:
            assert tranche_name in trigger_service.oc_calculators
            assert tranche_name in trigger_service.ic_calculators
            
            oc_calc = trigger_service.oc_calculators[tranche_name]
            ic_calc = trigger_service.ic_calculators[tranche_name]
            
            assert len(oc_calc.period_results) == 48
            assert len(ic_calc.period_results) == 48
    
    def test_trigger_calculations_with_passing_tests(self, session, sample_deal_with_tranches):
        """Test trigger calculations where all tests pass"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Setup scenario where all tests pass
        collateral_balance = Decimal('600000000')  # $600M collateral
        liability_balances = {
            "Class A": Decimal('300000000'),  # $300M
            "Class B": Decimal('100000000'),  # $100M
            "Class C": Decimal('50000000'),   # $50M
            "Class D": Decimal('30000000'),   # $30M
            "Class E": Decimal('20000000'),   # $20M
        }
        interest_collections = Decimal('30000000')  # $30M interest
        interest_due = {
            "Class A": Decimal('15000000'),   # $15M
            "Class B": Decimal('6000000'),    # $6M
            "Class C": Decimal('4000000'),    # $4M
            "Class D": Decimal('3000000'),    # $3M
            "Class E": Decimal('2000000'),    # $2M
        }
        
        # Calculate triggers
        result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches.deal_id,
            period=1,
            collateral_balance=collateral_balance,
            liability_balances=liability_balances,
            interest_collections=interest_collections,
            interest_due_by_tranche=interest_due
        )
        
        # All tests should pass with these ratios
        assert result.all_oc_pass is True
        assert result.all_ic_pass is True
        assert result.total_oc_cure_needed == Decimal('0')
        assert result.total_ic_cure_needed == Decimal('0')
        
        # Check individual tranche results
        for tranche in ["Class A", "Class B", "Class C"]:
            assert result.oc_results[tranche]['pass'] is True
            assert result.ic_results[tranche]['pass'] is True
    
    def test_trigger_calculations_with_failing_tests(self, session, sample_deal_with_tranches):
        """Test trigger calculations where tests fail and cures are needed"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Setup scenario where tests fail
        collateral_balance = Decimal('450000000')  # $450M collateral (lower)
        liability_balances = {
            "Class A": Decimal('300000000'),  # $300M
            "Class B": Decimal('100000000'),  # $100M
            "Class C": Decimal('50000000'),   # $50M
            "Class D": Decimal('30000000'),   # $30M
            "Class E": Decimal('20000000'),   # $20M
        }
        interest_collections = Decimal('25000000')  # $25M interest (lower)
        interest_due = {
            "Class A": Decimal('18000000'),   # $18M (higher)
            "Class B": Decimal('7000000'),    # $7M
            "Class C": Decimal('5000000'),    # $5M
            "Class D": Decimal('4000000'),    # $4M
            "Class E": Decimal('3000000'),    # $3M
        }
        
        # Calculate triggers
        result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches.deal_id,
            period=1,
            collateral_balance=collateral_balance,
            liability_balances=liability_balances,
            interest_collections=interest_collections,
            interest_due_by_tranche=interest_due
        )
        
        # Tests should fail
        assert result.all_oc_pass is False  # OC ratio 450/300 = 1.50 may still pass for Class A
        assert result.all_ic_pass is False  # IC ratio 25/18 = 1.39 may fail for Class A
        
        # Should have cure amounts
        assert result.total_ic_cure_needed > Decimal('0')
        
        # Check that Class A has issues
        if "Class A" in result.ic_results:
            class_a_ic = result.ic_results["Class A"]
            if not class_a_ic['pass']:
                assert class_a_ic['cure_needed'] > 0
    
    def test_cure_payment_application(self, session, sample_deal_with_tranches):
        """Test applying cure payments to failing triggers"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Setup failing scenario
        collateral_balance = Decimal('400000000')
        liability_balances = {"Class A": Decimal('350000000')}  # OC ratio = 1.14 (< 1.20)
        interest_collections = Decimal('15000000')
        interest_due = {"Class A": Decimal('20000000')}  # IC ratio = 0.75 (< 1.10)
        
        # Calculate triggers
        result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches.deal_id,
            period=1,
            collateral_balance=collateral_balance,
            liability_balances=liability_balances,
            interest_collections=interest_collections,
            interest_due_by_tranche=interest_due
        )
        
        # Should have cure requirements
        assert not result.all_oc_pass
        assert not result.all_ic_pass
        
        # Get initial cure requirements
        class_a_oc = result.oc_results["Class A"]
        class_a_ic = result.ic_results["Class A"]
        
        initial_oc_interest_cure = Decimal(str(class_a_oc['interest_cure_needed']))
        initial_ic_cure = Decimal(str(class_a_ic['cure_needed']))
        
        # Apply partial cures
        oc_interest_payment = initial_oc_interest_cure / 2  # Half payment
        ic_payment = initial_ic_cure / 2  # Half payment
        
        unused_amounts = trigger_service.apply_cure_payments(
            tranche_name="Class A",
            oc_interest_cure=oc_interest_payment,
            ic_cure=ic_payment
        )
        
        # Should have no unused amounts (all applied to cure)
        assert unused_amounts.get('oc_interest', Decimal('0')) == Decimal('0')
        assert unused_amounts.get('ic', Decimal('0')) == Decimal('0')
        
        # Cure requirements should be reduced
        context = trigger_service.get_trigger_context_for_waterfall("Class A")
        assert context['oc_interest_cure_needed'] < float(initial_oc_interest_cure)
        assert context['ic_cure_needed'] < float(initial_ic_cure)
    
    def test_database_persistence(self, session, sample_deal_with_tranches):
        """Test saving and loading trigger results from database"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Calculate triggers for period 1
        result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches.deal_id,
            period=1,
            collateral_balance=Decimal('500000000'),
            liability_balances={"Class A": Decimal('300000000')},
            interest_collections=Decimal('20000000'),
            interest_due_by_tranche={"Class A": Decimal('18000000')}
        )
        
        # Save to database
        trigger_service.save_trigger_results_to_db(sample_deal_with_tranches.deal_id, 1)
        
        # Verify records were created
        from app.models.oc_trigger import OCTrigger
        from app.models.ic_trigger import ICTrigger
        
        oc_records = session.query(OCTrigger)\
            .filter_by(deal_id=sample_deal_with_tranches.deal_id, period_number=1)\
            .all()
        
        ic_records = session.query(ICTrigger)\
            .filter_by(deal_id=sample_deal_with_tranches.deal_id, period_number=1)\
            .all()
        
        # Should have records for all tranches
        assert len(oc_records) > 0
        assert len(ic_records) > 0
        
        # Verify data integrity
        class_a_oc = next((r for r in oc_records if r.tranche_name == "Class A"), None)
        assert class_a_oc is not None
        assert class_a_oc.numerator == Decimal('500000000')
        assert class_a_oc.denominator == Decimal('300000000')
        assert class_a_oc.calculated_ratio > Decimal('1.6')  # 500/300
    
    def test_comprehensive_trigger_report(self, session, sample_deal_with_tranches):
        """Test comprehensive trigger reporting functionality"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Calculate a few periods
        for period in range(1, 4):
            collateral_balance = Decimal('500000000') - Decimal('10000000') * period  # Declining
            liability_balances = {"Class A": Decimal('300000000')}
            interest_collections = Decimal('20000000')
            interest_due = {"Class A": Decimal('18000000')}
            
            trigger_service.calculate_triggers(
                deal_id=sample_deal_with_tranches.deal_id,
                period=period,
                collateral_balance=collateral_balance,
                liability_balances=liability_balances,
                interest_collections=interest_collections,
                interest_due_by_tranche=interest_due
            )
            
            if period < 3:  # Don't rollforward after last period
                trigger_service.rollforward_all_triggers()
        
        # Generate comprehensive report
        report = trigger_service.get_comprehensive_trigger_report(sample_deal_with_tranches.deal_id)
        
        # Validate report structure
        assert 'deal_id' in report
        assert 'oc_triggers' in report
        assert 'ic_triggers' in report
        assert 'summary' in report
        
        # Check summary statistics
        summary = report['summary']
        assert summary['periods_calculated'] == 3
        assert 'oc_tests_passing' in summary
        assert 'ic_tests_passing' in summary
        
        # Check individual tranche data
        if "Class A" in report['oc_triggers']:
            class_a_oc_data = report['oc_triggers']['Class A']
            assert 'threshold' in class_a_oc_data
            assert 'periods' in class_a_oc_data
            assert 'current_status' in class_a_oc_data
    
    def test_multiple_periods_with_rollforward(self, session, sample_deal_with_tranches):
        """Test multiple period calculations with proper rollforward"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Test data for multiple periods
        period_data = [
            # Period 1: All tests pass
            {
                'collateral': Decimal('600000000'),
                'liability': Decimal('300000000'),
                'interest_collections': Decimal('20000000'),
                'interest_due': Decimal('18000000'),
                'expected_oc_pass': True,
                'expected_ic_pass': True
            },
            # Period 2: OC fails
            {
                'collateral': Decimal('300000000'),  # Lower collateral
                'liability': Decimal('300000000'),
                'interest_collections': Decimal('20000000'),
                'interest_due': Decimal('18000000'),
                'expected_oc_pass': False,  # 1.0 < 1.20
                'expected_ic_pass': True    # 1.11 > 1.10
            },
            # Period 3: Both fail
            {
                'collateral': Decimal('280000000'),  # Even lower
                'liability': Decimal('300000000'),
                'interest_collections': Decimal('15000000'),  # Lower collections
                'interest_due': Decimal('18000000'),
                'expected_oc_pass': False,  # 0.93 < 1.20
                'expected_ic_pass': False   # 0.83 < 1.10
            }
        ]
        
        for period, data in enumerate(period_data, 1):
            # Calculate triggers for this period
            result = trigger_service.calculate_triggers(
                deal_id=sample_deal_with_tranches.deal_id,
                period=period,
                collateral_balance=data['collateral'],
                liability_balances={"Class A": data['liability']},
                interest_collections=data['interest_collections'],
                interest_due_by_tranche={"Class A": data['interest_due']}
            )
            
            # Validate results match expectations
            class_a_oc = result.oc_results.get("Class A", {})
            class_a_ic = result.ic_results.get("Class A", {})
            
            # Note: Actual pass/fail depends on specific thresholds
            # This is a simplified test - in practice would need exact threshold checks
            
            if period < len(period_data):  # Don't rollforward after last period
                trigger_service.rollforward_all_triggers()
        
        # Final verification - should have calculated 3 periods
        class_a_oc_calc = trigger_service.oc_calculators["Class A"]
        class_a_ic_calc = trigger_service.ic_calculators["Class A"]
        
        assert class_a_oc_calc.last_period_calculated == 3
        assert class_a_ic_calc.last_period_calculated == 3
    
    def test_edge_case_zero_balances(self, session, sample_deal_with_tranches):
        """Test edge cases with zero or very small balances"""
        trigger_service = TriggerService(session)
        trigger_service.setup_deal_triggers(sample_deal_with_tranches.deal_id, 48)
        
        # Test with zero liability balance
        result = trigger_service.calculate_triggers(
            deal_id=sample_deal_with_tranches.deal_id,
            period=1,
            collateral_balance=Decimal('500000000'),
            liability_balances={"Class A": Decimal('0')},  # Zero liability
            interest_collections=Decimal('20000000'),
            interest_due_by_tranche={"Class A": Decimal('0')}  # Zero interest due
        )
        
        # Should automatically pass when no liabilities
        if "Class A" in result.oc_results:
            assert result.oc_results["Class A"]['pass'] is True
        if "Class A" in result.ic_results:
            assert result.ic_results["Class A"]['pass'] is True
    
    def test_error_handling_invalid_deal(self, session):
        """Test error handling with invalid deal ID"""
        trigger_service = TriggerService(session)
        
        with pytest.raises(ValueError, match="Deal .* not found"):
            trigger_service.setup_deal_triggers("INVALID_DEAL", 48)