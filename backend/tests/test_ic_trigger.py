"""
Tests for ICTrigger model and calculator
Validates VBA ICTrigger.cls conversion accuracy
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.ic_trigger import ICTrigger, ICTriggerCalculator, ICTriggerResult
from app.models.clo_deal import CLODeal
from app.core.database import Base, engine


class TestICTriggerCalculator:
    """Test suite for ICTriggerCalculator class"""
    
    def test_ic_trigger_initialization(self):
        """Test basic ICTrigger initialization"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        
        assert calculator.name == "Class A IC"
        assert calculator.trigger_threshold == Decimal('1.10')
        assert calculator.current_period == 1
        assert calculator.last_period_calculated == 0
        assert len(calculator.period_results) == 0
    
    def test_deal_setup(self):
        """Test deal setup with multiple periods"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(48)  # 48 quarterly payments
        
        assert len(calculator.period_results) == 48
        assert calculator.current_period == 1
        
        # All periods should be initialized with default values
        for period in range(1, 49):
            result = calculator.period_results[period]
            assert isinstance(result, ICTriggerResult)
            assert result.pass_fail is True
            assert result.numerator == Decimal('0')
    
    def test_ic_calculation_passing(self):
        """Test IC calculation when test passes"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Test passing scenario: 11M interest collections vs 10M interest due = 1.10 ratio
        interest_collections = Decimal('11000000')   # $11M
        interest_due = Decimal('10000000')           # $10M
        liability_balance = Decimal('100000000')     # $100M
        
        result = calculator.calculate(interest_collections, interest_due, liability_balance)
        
        assert result is True  # Test passes
        assert calculator.get_pass_fail() is True
        assert calculator.get_cure_amount() == Decimal('0')
        
        current_result = calculator.get_current_result()
        assert current_result.calculated_ratio == Decimal('1.100000')
        assert current_result.pass_fail is True
        assert current_result.cure_amount == Decimal('0')
    
    def test_ic_calculation_failing(self):
        """Test IC calculation when test fails"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Test failing scenario: 9M collections vs 10M due = 0.90 ratio (< 1.10)
        interest_collections = Decimal('9000000')    # $9M
        interest_due = Decimal('10000000')           # $10M
        liability_balance = Decimal('100000000')     # $100M
        
        result = calculator.calculate(interest_collections, interest_due, liability_balance)
        
        assert result is False  # Test fails
        assert calculator.get_pass_fail() is False
        
        current_result = calculator.get_current_result()
        assert current_result.calculated_ratio == Decimal('0.900000')
        
        # Validate cure amount (from VBA logic)
        # Cure = (1 - 0.90/1.10) * 100M = (1 - 0.8182) * 100M = 18.18M
        expected_cure = (Decimal('1') - Decimal('0.900000') / Decimal('1.10')) * liability_balance
        assert abs(current_result.cure_amount - expected_cure) < Decimal('0.01')
        assert calculator.get_cure_amount() > Decimal('18000000')
    
    def test_zero_denominator_edge_case(self):
        """Test edge case with zero interest due"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        result = calculator.calculate(Decimal('5000000'), Decimal('0'), Decimal('100000000'))
        
        # Should automatically pass when no interest due
        assert result is True
        assert calculator.get_pass_fail() is True
        assert calculator.get_cure_amount() == Decimal('0')
    
    def test_cure_payment_application(self):
        """Test cure payment application"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        
        # Get initial cure amount
        initial_cure = calculator.get_cure_amount()
        assert initial_cure > Decimal('0')
        
        # Apply partial cure payment
        cure_payment = Decimal('5000000')  # $5M
        remaining = calculator.pay_cure(cure_payment)
        
        # Should reduce cure requirement
        current_result = calculator.get_current_result()
        assert current_result.cure_amount_paid == cure_payment
        assert remaining == Decimal('0')  # All payment applied
        assert calculator.get_cure_amount() == initial_cure - cure_payment
    
    def test_full_cure_payment(self):
        """Test full cure payment eliminates cure requirement"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        
        # Get required cure amount
        cure_needed = calculator.get_cure_amount()
        
        # Apply full cure
        remaining = calculator.pay_cure(cure_needed)
        
        assert calculator.get_cure_amount() == Decimal('0')
        assert remaining == Decimal('0')
        
        current_result = calculator.get_current_result()
        assert current_result.cure_amount_paid == cure_needed
    
    def test_excess_cure_payment(self):
        """Test excess cure payment returns unused amount"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        
        # Get required cure amount
        cure_needed = calculator.get_cure_amount()
        
        # Apply excess cure
        excess_payment = cure_needed + Decimal('5000000')
        remaining = calculator.pay_cure(excess_payment)
        
        assert calculator.get_cure_amount() == Decimal('0')
        assert remaining == Decimal('5000000')  # Unused amount returned
    
    def test_prior_cure_payments(self):
        """Test prior cure payment tracking"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        
        # Add prior cure
        prior_cure = Decimal('3000000')  # $3M
        remaining = calculator.add_prior_cure(prior_cure)
        
        assert remaining == Decimal('0')
        
        current_result = calculator.get_current_result()
        assert current_result.prior_cure_payments == prior_cure
        
        # Net cure amount should be reduced
        assert calculator.get_cure_amount() < current_result.cure_amount
    
    def test_prior_cure_excess(self):
        """Test prior cure payment with excess amount"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Setup failing test with small cure amount
        calculator.calculate(Decimal('10500000'), Decimal('10000000'), Decimal('10000000'))
        
        cure_needed = calculator.get_cure_amount()
        
        # Add excess prior cure
        excess_prior = cure_needed + Decimal('1000000')
        remaining = calculator.add_prior_cure(excess_prior)
        
        # Should only use what's needed
        current_result = calculator.get_current_result()
        assert current_result.prior_cure_payments == cure_needed
        assert remaining == Decimal('1000000')  # Excess returned
        assert calculator.get_cure_amount() == Decimal('0')
    
    def test_rollforward_functionality(self):
        """Test period rollforward"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Calculate period 1
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        assert calculator.current_period == 1
        
        # Rollforward to period 2
        calculator.rollforward()
        assert calculator.current_period == 2
        
        # Calculate period 2
        calculator.calculate(Decimal('11000000'), Decimal('10000000'), Decimal('100000000'))
        
        # Should have results for both periods
        assert 1 in calculator.period_results
        assert 2 in calculator.period_results
        assert calculator.last_period_calculated == 2
    
    def test_output_generation(self):
        """Test output array generation for reporting"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Calculate a few periods
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        calculator.rollforward()
        calculator.calculate(Decimal('11000000'), Decimal('10000000'), Decimal('100000000'))
        
        output = calculator.get_output()
        
        # Should have header + 2 data rows
        assert len(output) == 3
        assert len(output[0]) == 9  # 9 columns per VBA
        
        # Check header
        expected_headers = ["Numerator", "Denominator", "Liability Balance", "Results", 
                          "Threshold", "Pass/Fail", "Prior Cure Payments", "Cure Amount", "Cure Paid"]
        assert output[0] == expected_headers
        
        # Check data formatting
        assert isinstance(output[1][0], float)  # Numerator
        assert "%" in output[1][3]  # Results formatted as percentage
        assert isinstance(output[1][5], bool)  # Pass/Fail boolean
    
    def test_cure_status_summary(self):
        """Test cure status summary generation"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Test failing scenario
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        
        summary = calculator.get_cure_status_summary()
        
        assert summary["period"] == 1
        assert summary["ic_ratio"] == 0.9
        assert summary["ic_threshold"] == 1.1
        assert summary["test_passing"] is False
        assert summary["cure_needed"] is True
        assert summary["cure_amount_needed"] > 0
        assert summary["numerator"] == 9000000.0
        assert summary["denominator"] == 10000000.0
        assert summary["liability_balance"] == 100000000.0
    
    def test_period_results_retrieval(self):
        """Test period results retrieval functionality"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Calculate multiple periods
        test_data = [
            (Decimal('9000000'), Decimal('10000000')),
            (Decimal('11000000'), Decimal('10000000')),
            (Decimal('10500000'), Decimal('10000000')),
        ]
        
        for collections, due in test_data:
            calculator.calculate(collections, due, Decimal('100000000'))
            calculator.rollforward()
        
        # Test period range retrieval
        results = calculator.get_period_results(1, 3)
        assert len(results) == 3
        assert 1 in results
        assert 2 in results
        assert 3 in results
        
        # Test all results
        all_results = calculator.get_period_results()
        assert len(all_results) == 3
    
    def test_utility_methods(self):
        """Test utility methods"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Test with passing scenario
        calculator.calculate(Decimal('11000000'), Decimal('10000000'), Decimal('100000000'))
        assert not calculator.is_test_failing()
        
        # Test with failing scenario
        calculator.rollforward()
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        assert calculator.is_test_failing()
        
        # Add some cure payments
        calculator.pay_cure(Decimal('5000000'))
        total_paid = calculator.get_total_cure_paid()
        assert total_paid == Decimal('5000000')
        
        outstanding = calculator.get_total_cure_outstanding()
        assert outstanding > Decimal('0')
    
    def test_validation_methods(self):
        """Test input validation methods"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        
        # Test valid inputs
        errors = calculator.validate_calculation_inputs(
            Decimal('10000000'), Decimal('9000000'), Decimal('100000000'))
        assert len(errors) == 0
        
        # Test negative numerator
        errors = calculator.validate_calculation_inputs(
            Decimal('-1000000'), Decimal('9000000'), Decimal('100000000'))
        assert len(errors) == 1
        assert "negative" in errors[0].lower()
        
        # Test negative denominator
        errors = calculator.validate_calculation_inputs(
            Decimal('10000000'), Decimal('-9000000'), Decimal('100000000'))
        assert len(errors) == 1
        
        # Test multiple errors
        errors = calculator.validate_calculation_inputs(
            Decimal('-1000000'), Decimal('-9000000'), Decimal('-100000000'))
        assert len(errors) == 3
    
    def test_multiple_threshold_scenarios(self):
        """Test various threshold scenarios"""
        test_cases = [
            # (threshold, collections, due, should_pass)
            (Decimal('1.10'), Decimal('11000000'), Decimal('10000000'), True),   # Exactly at threshold
            (Decimal('1.15'), Decimal('11000000'), Decimal('10000000'), False),  # Below threshold
            (Decimal('1.05'), Decimal('11000000'), Decimal('10000000'), True),   # Above threshold
            (Decimal('2.00'), Decimal('15000000'), Decimal('10000000'), False),  # Well below high threshold
        ]
        
        for threshold, collections, due, should_pass in test_cases:
            calculator = ICTriggerCalculator("Test IC", threshold)
            calculator.setup_deal(12)
            
            result = calculator.calculate(collections, due, Decimal('100000000'))
            assert result == should_pass, f"Failed for threshold {threshold}"
    
    def test_reset_period_calculations(self):
        """Test resetting period calculations"""
        calculator = ICTriggerCalculator("Class A IC", Decimal('1.10'))
        calculator.setup_deal(12)
        
        # Calculate period 1
        calculator.calculate(Decimal('9000000'), Decimal('10000000'), Decimal('100000000'))
        assert calculator.period_results[1].calculated_ratio == Decimal('0.900000')
        
        # Reset period 1
        calculator.reset_period_calculations(1)
        
        # Should be back to default values
        result = calculator.period_results[1]
        assert result.calculated_ratio == Decimal('0')
        assert result.pass_fail is True
        assert result.cure_amount == Decimal('0')


class TestICTriggerModel:
    """Test suite for ICTrigger SQLAlchemy model"""
    
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
    def sample_deal(self, session):
        """Create a sample CLO deal for testing"""
        deal = CLODeal(
            deal_id="TEST_DEAL_001",
            deal_name="Test CLO Deal",
            manager_name="Test Manager",
            target_par_amount=Decimal('500000000'),
            payment_frequency=4
        )
        session.add(deal)
        session.commit()
        return deal
    
    def test_ic_trigger_model_creation(self, session, sample_deal):
        """Test creating ICTrigger model instance"""
        ic_trigger = ICTrigger(
            deal_id=sample_deal.deal_id,
            tranche_name="Class A",
            trigger_name="Class A IC Test",
            ic_threshold=Decimal('1.10'),
            period_number=1,
            numerator=Decimal('11000000'),
            denominator=Decimal('10000000'),
            liability_balance=Decimal('100000000'),
            calculated_ratio=Decimal('1.100000'),
            pass_fail=True,
            cure_amount=Decimal('0')
        )
        
        session.add(ic_trigger)
        session.commit()
        
        # Retrieve and validate
        retrieved = session.query(ICTrigger).filter_by(deal_id=sample_deal.deal_id).first()
        assert retrieved is not None
        assert retrieved.tranche_name == "Class A"
        assert retrieved.ic_threshold == Decimal('1.10')
        assert retrieved.pass_fail is True
    
    def test_ic_trigger_relationships(self, session, sample_deal):
        """Test ICTrigger relationships with CLODeal"""
        ic_trigger = ICTrigger(
            deal_id=sample_deal.deal_id,
            tranche_name="Class A",
            trigger_name="Class A IC Test",
            ic_threshold=Decimal('1.10'),
            period_number=1
        )
        
        session.add(ic_trigger)
        session.commit()
        
        # Test relationship access
        assert ic_trigger.deal_id == sample_deal.deal_id
        assert ic_trigger.deal == sample_deal
        assert ic_trigger in sample_deal.ic_triggers
    
    def test_multiple_periods_same_tranche(self, session, sample_deal):
        """Test multiple IC trigger records for different periods"""
        periods_data = [
            (1, Decimal('11000000'), Decimal('10000000'), True),
            (2, Decimal('9000000'), Decimal('10000000'), False),
            (3, Decimal('12000000'), Decimal('10000000'), True),
        ]
        
        for period, numerator, denominator, pass_fail in periods_data:
            ic_trigger = ICTrigger(
                deal_id=sample_deal.deal_id,
                tranche_name="Class A",
                trigger_name="Class A IC Test",
                ic_threshold=Decimal('1.10'),
                period_number=period,
                numerator=numerator,
                denominator=denominator,
                liability_balance=Decimal('100000000'),
                calculated_ratio=numerator / denominator,
                pass_fail=pass_fail
            )
            session.add(ic_trigger)
        
        session.commit()
        
        # Retrieve all periods
        triggers = session.query(ICTrigger)\
            .filter_by(deal_id=sample_deal.deal_id, tranche_name="Class A")\
            .order_by(ICTrigger.period_number)\
            .all()
        
        assert len(triggers) == 3
        assert triggers[0].period_number == 1
        assert triggers[0].pass_fail is True
        assert triggers[1].pass_fail is False
        assert triggers[2].pass_fail is True
        
    def test_multiple_tranches_same_period(self, session, sample_deal):
        """Test multiple tranches in the same period"""
        tranches_data = [
            ("Class A", Decimal('1.10'), Decimal('11000000'), True),
            ("Class B", Decimal('1.05'), Decimal('10000000'), False),
            ("Class C", Decimal('1.00'), Decimal('9500000'), False),
        ]
        
        for tranche, threshold, numerator, pass_fail in tranches_data:
            ic_trigger = ICTrigger(
                deal_id=sample_deal.deal_id,
                tranche_name=tranche,
                trigger_name=f"{tranche} IC Test",
                ic_threshold=threshold,
                period_number=1,
                numerator=numerator,
                denominator=Decimal('10000000'),
                liability_balance=Decimal('100000000'),
                calculated_ratio=numerator / Decimal('10000000'),
                pass_fail=pass_fail
            )
            session.add(ic_trigger)
        
        session.commit()
        
        # Retrieve all tranches for period 1
        triggers = session.query(ICTrigger)\
            .filter_by(deal_id=sample_deal.deal_id, period_number=1)\
            .order_by(ICTrigger.tranche_name)\
            .all()
        
        assert len(triggers) == 3
        assert triggers[0].tranche_name == "Class A"
        assert triggers[1].tranche_name == "Class B"
        assert triggers[2].tranche_name == "Class C"