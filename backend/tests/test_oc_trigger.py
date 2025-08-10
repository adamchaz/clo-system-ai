"""
Tests for OCTrigger model and calculator
Validates VBA OCTrigger.cls conversion accuracy
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.oc_trigger import OCTrigger, OCTriggerCalculator, OCTriggerResult
from app.models.clo_deal import CLODeal
from app.core.database import Base, engine


class TestOCTriggerCalculator:
    """Test suite for OCTriggerCalculator class"""
    
    def test_oc_trigger_initialization(self):
        """Test basic OCTrigger initialization"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        
        assert calculator.name == "Class A OC"
        assert calculator.trigger_threshold == Decimal('1.20')
        assert calculator.current_period == 1
        assert calculator.last_period_calculated == 0
        assert len(calculator.period_results) == 0
    
    def test_deal_setup(self):
        """Test deal setup with multiple periods"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(48)  # 48 quarterly payments
        
        assert len(calculator.period_results) == 48
        assert calculator.current_period == 1
        
        # All periods should be initialized with default values
        for period in range(1, 49):
            result = calculator.period_results[period]
            assert isinstance(result, OCTriggerResult)
            assert result.pass_fail is True
            assert result.numerator == Decimal('0')
    
    def test_oc_calculation_passing(self):
        """Test OC calculation when test passes"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Test passing scenario: 120M collateral vs 100M liability = 1.20 ratio
        collateral_balance = Decimal('120000000')  # $120M
        liability_balance = Decimal('100000000')   # $100M
        
        result = calculator.calculate(collateral_balance, liability_balance)
        
        assert result is True  # Test passes
        assert calculator.get_pass_fail() is True
        assert calculator.get_interest_cure_amount() == Decimal('0')
        assert calculator.get_principal_cure_amount() == Decimal('0')
        
        current_result = calculator.get_current_result()
        assert current_result.calculated_ratio == Decimal('1.200000')
        assert current_result.pass_fail is True
    
    def test_oc_calculation_failing(self):
        """Test OC calculation when test fails"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Test failing scenario: 110M collateral vs 100M liability = 1.10 ratio (< 1.20)
        collateral_balance = Decimal('110000000')  # $110M
        liability_balance = Decimal('100000000')   # $100M
        
        result = calculator.calculate(collateral_balance, liability_balance)
        
        assert result is False  # Test fails
        assert calculator.get_pass_fail() is False
        
        # Validate cure amounts (from VBA logic)
        current_result = calculator.get_current_result()
        assert current_result.calculated_ratio == Decimal('1.100000')
        
        # Interest cure: (1 - 1.10/1.20) * 100M = (1 - 0.9167) * 100M = 8.33M
        expected_interest_cure = Decimal('8333333.33')
        assert abs(current_result.interest_cure_amount - expected_interest_cure) < Decimal('0.01')
        
        # Principal cure: (1.20 * 100M - 110M) / (1.20 - 1) = 10M / 0.20 = 50M
        expected_principal_cure = Decimal('50000000.00')
        assert abs(current_result.principal_cure_amount - expected_principal_cure) < Decimal('0.01')
    
    def test_zero_denominator_edge_case(self):
        """Test edge case with zero liability balance"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        result = calculator.calculate(Decimal('100000000'), Decimal('0'))
        
        # Should automatically pass when no liabilities
        assert result is True
        assert calculator.get_pass_fail() is True
        assert calculator.get_interest_cure_amount() == Decimal('0')
    
    def test_interest_cure_payment(self):
        """Test interest cure payment application"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        
        # Apply partial interest cure
        interest_payment = Decimal('5000000')  # $5M
        remaining = calculator.pay_interest(interest_payment)
        
        # Should reduce cure requirement
        current_result = calculator.get_current_result()
        assert current_result.interest_cure_paid == interest_payment
        assert remaining == Decimal('0')  # All payment applied to cure
        
        # Principal cure should be recalculated
        assert current_result.principal_cure_amount > Decimal('0')
    
    def test_full_interest_cure_eliminates_principal_cure(self):
        """Test that full interest cure eliminates principal cure requirement"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        
        # Get required interest cure amount
        interest_cure_needed = calculator.get_interest_cure_amount()
        
        # Apply full interest cure
        remaining = calculator.pay_interest(interest_cure_needed)
        
        current_result = calculator.get_current_result()
        
        # Principal cure should be eliminated (VBA logic)
        assert current_result.principal_cure_amount == Decimal('0')
        assert calculator.get_principal_cure_amount() == Decimal('0')
        assert remaining == Decimal('0')
    
    def test_principal_cure_payment(self):
        """Test principal cure payment application"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        
        # Apply principal cure
        principal_payment = Decimal('25000000')  # $25M
        remaining = calculator.pay_principal(principal_payment)
        
        current_result = calculator.get_current_result()
        assert current_result.principal_cure_paid == principal_payment
        assert remaining == Decimal('0')  # All payment applied to cure
    
    def test_prior_cure_payments(self):
        """Test prior cure payment tracking"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Setup failing test
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        
        # Add prior cures
        prior_interest = Decimal('3000000')  # $3M
        prior_principal = Decimal('10000000')  # $10M
        
        remaining_interest = calculator.add_prior_interest_cure(prior_interest)
        remaining_principal = calculator.add_prior_principal_cure(prior_principal)
        
        assert remaining_interest == Decimal('0')
        assert remaining_principal == Decimal('0')
        
        current_result = calculator.get_current_result()
        assert current_result.prior_interest_cure == prior_interest
        assert current_result.prior_principal_cure == prior_principal
        
        # Net cure amounts should be reduced
        assert calculator.get_interest_cure_amount() < current_result.interest_cure_amount
        assert calculator.get_principal_cure_amount() < current_result.principal_cure_amount
    
    def test_rollforward_functionality(self):
        """Test period rollforward"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Calculate period 1
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        assert calculator.current_period == 1
        
        # Rollforward to period 2
        calculator.rollforward()
        assert calculator.current_period == 2
        
        # Calculate period 2
        calculator.calculate(Decimal('115000000'), Decimal('100000000'))
        
        # Should have results for both periods
        assert 1 in calculator.period_results
        assert 2 in calculator.period_results
        assert calculator.last_period_calculated == 2
    
    def test_output_generation(self):
        """Test output array generation for reporting"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Calculate a few periods
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        calculator.rollforward()
        calculator.calculate(Decimal('120000000'), Decimal('100000000'))
        
        output = calculator.get_output()
        
        # Should have header + 2 data rows
        assert len(output) == 3
        assert len(output[0]) == 11  # 11 columns per VBA
        
        # Check header
        expected_headers = ["Numerator", "Denominator", "Result", "Threshold", "Pass/Fail",
                          "Prior Int Cure", "Prior Prin Cure", "Int Cure Amount", "Int Cure Paid",
                          "Prin Cure Amount", "Prin Cure Paid"]
        assert output[0] == expected_headers
        
        # Check data formatting
        assert isinstance(output[1][0], float)  # Numerator
        assert "%" in output[1][2]  # Result formatted as percentage
        assert isinstance(output[1][4], bool)  # Pass/Fail boolean
    
    def test_cure_status_summary(self):
        """Test cure status summary generation"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Test failing scenario
        calculator.calculate(Decimal('110000000'), Decimal('100000000'))
        
        summary = calculator.get_cure_status_summary()
        
        assert summary["period"] == 1
        assert summary["oc_ratio"] == 1.1
        assert summary["oc_threshold"] == 1.2
        assert summary["test_passing"] is False
        assert summary["cures_needed"] is True
        assert summary["interest_cure_needed"] > 0
        assert summary["principal_cure_needed"] > 0
    
    def test_multiple_threshold_scenarios(self):
        """Test various threshold scenarios"""
        test_cases = [
            # (threshold, collateral, liability, should_pass)
            (Decimal('1.10'), Decimal('110000000'), Decimal('100000000'), True),   # Exactly at threshold
            (Decimal('1.15'), Decimal('110000000'), Decimal('100000000'), False),  # Below threshold
            (Decimal('1.05'), Decimal('110000000'), Decimal('100000000'), True),   # Above threshold
            (Decimal('2.00'), Decimal('150000000'), Decimal('100000000'), False),  # Well below high threshold
        ]
        
        for threshold, collateral, liability, should_pass in test_cases:
            calculator = OCTriggerCalculator("Test OC", threshold)
            calculator.setup_deal(12)
            
            result = calculator.calculate(collateral, liability)
            assert result == should_pass, f"Failed for threshold {threshold}"
    
    def test_edge_case_very_small_amounts(self):
        """Test edge cases with very small amounts"""
        calculator = OCTriggerCalculator("Class A OC", Decimal('1.20'))
        calculator.setup_deal(12)
        
        # Very small amounts
        result = calculator.calculate(Decimal('1.10'), Decimal('1.00'))
        
        assert result is False
        assert calculator.get_current_result().calculated_ratio == Decimal('1.100000')
        
        # Cure amounts should still be calculated correctly
        interest_cure = calculator.get_interest_cure_amount()
        principal_cure = calculator.get_principal_cure_amount()
        
        assert interest_cure > Decimal('0')
        assert principal_cure > Decimal('0')


class TestOCTriggerModel:
    """Test suite for OCTrigger SQLAlchemy model"""
    
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
    
    def test_oc_trigger_model_creation(self, session, sample_deal):
        """Test creating OCTrigger model instance"""
        oc_trigger = OCTrigger(
            deal_id=sample_deal.deal_id,
            tranche_name="Class A",
            trigger_name="Class A OC Test",
            oc_threshold=Decimal('1.20'),
            period_number=1,
            numerator=Decimal('120000000'),
            denominator=Decimal('100000000'),
            calculated_ratio=Decimal('1.200000'),
            pass_fail=True,
            interest_cure_amount=Decimal('0'),
            principal_cure_amount=Decimal('0')
        )
        
        session.add(oc_trigger)
        session.commit()
        
        # Retrieve and validate
        retrieved = session.query(OCTrigger).filter_by(deal_id=sample_deal.deal_id).first()
        assert retrieved is not None
        assert retrieved.tranche_name == "Class A"
        assert retrieved.oc_threshold == Decimal('1.20')
        assert retrieved.pass_fail is True
    
    def test_oc_trigger_relationships(self, session, sample_deal):
        """Test OCTrigger relationships with CLODeal"""
        oc_trigger = OCTrigger(
            deal_id=sample_deal.deal_id,
            tranche_name="Class A",
            trigger_name="Class A OC Test",
            oc_threshold=Decimal('1.20'),
            period_number=1
        )
        
        session.add(oc_trigger)
        session.commit()
        
        # Test relationship access
        assert oc_trigger.deal_id == sample_deal.deal_id
        assert oc_trigger.deal == sample_deal
        assert oc_trigger in sample_deal.oc_triggers
    
    def test_multiple_periods_same_tranche(self, session, sample_deal):
        """Test multiple OC trigger records for different periods"""
        periods_data = [
            (1, Decimal('120000000'), Decimal('100000000'), True),
            (2, Decimal('115000000'), Decimal('100000000'), False),
            (3, Decimal('125000000'), Decimal('100000000'), True),
        ]
        
        for period, numerator, denominator, pass_fail in periods_data:
            oc_trigger = OCTrigger(
                deal_id=sample_deal.deal_id,
                tranche_name="Class A",
                trigger_name="Class A OC Test",
                oc_threshold=Decimal('1.20'),
                period_number=period,
                numerator=numerator,
                denominator=denominator,
                calculated_ratio=numerator / denominator,
                pass_fail=pass_fail
            )
            session.add(oc_trigger)
        
        session.commit()
        
        # Retrieve all periods
        triggers = session.query(OCTrigger)\
            .filter_by(deal_id=sample_deal.deal_id, tranche_name="Class A")\
            .order_by(OCTrigger.period_number)\
            .all()
        
        assert len(triggers) == 3
        assert triggers[0].period_number == 1
        assert triggers[0].pass_fail is True
        assert triggers[1].pass_fail is False
        assert triggers[2].pass_fail is True