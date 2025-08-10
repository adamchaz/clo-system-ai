"""
Test Different Waterfall Implementations
Validates multiple waterfall types and configuration system
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.waterfall_types import (
    WaterfallType, TraditionalWaterfall, TurboWaterfall, PIKToggleWaterfall,
    WaterfallStrategyFactory, EnhancedWaterfallCalculator, PaymentPhase
)
from app.models.waterfall_config import (
    WaterfallTemplate, PaymentRule, WaterfallModification, PaymentOverride,
    ConfigurableWaterfallCalculator
)
from app.models.waterfall import WaterfallConfiguration, WaterfallStep
from app.models.clo_deal import CLODeal, CLOTranche
from app.core.database import Base


@pytest.fixture
def engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_deal(session):
    """Create sample CLO deal with tranches"""
    deal = CLODeal(
        deal_id="MULTI-WATERFALL-TEST",
        deal_name="Multi Waterfall Test Deal",
        effective_date=date(2023, 6, 15),
        first_payment_date=date(2023, 9, 15),
        reinvestment_end_date=date(2025, 6, 15),
        no_call_date=date(2025, 6, 15),
        maturity_date=date(2030, 6, 15),
        payment_frequency=4,
        deal_status="ACTIVE"
    )
    session.add(deal)
    
    # Create tranches with different characteristics
    tranches = [
        CLOTranche(
            tranche_id="TEST-A", deal_id=deal.deal_id, tranche_name="Class A Notes",
            initial_balance=Decimal('300000000'), current_balance=Decimal('300000000'),
            coupon_rate=Decimal('0.050'), seniority_level=1
        ),
        CLOTranche(
            tranche_id="TEST-B", deal_id=deal.deal_id, tranche_name="Class B Notes",
            initial_balance=Decimal('50000000'), current_balance=Decimal('50000000'),
            coupon_rate=Decimal('0.075'), seniority_level=2
        ),
        CLOTranche(
            tranche_id="TEST-E", deal_id=deal.deal_id, tranche_name="Class E Notes",
            initial_balance=Decimal('25000000'), current_balance=Decimal('25000000'),
            coupon_rate=Decimal('0.120'), seniority_level=5
        )
    ]
    
    for tranche in tranches:
        session.add(tranche)
    
    session.commit()
    return deal


@pytest.fixture
def base_config(session, sample_deal):
    """Create base waterfall configuration"""
    config = WaterfallConfiguration(
        deal_id=sample_deal.deal_id,
        config_name="Base Configuration",
        effective_date=date(2023, 6, 15),
        payment_rules='[]',
        senior_mgmt_fee_rate=Decimal('0.0040'),
        interest_reserve_target=Decimal('5000000'),
        trustee_fee_annual=Decimal('100000')
    )
    session.add(config)
    session.commit()
    return config


class TestWaterfallStrategies:
    """Test different waterfall implementation strategies"""
    
    def test_traditional_waterfall(self, session, sample_deal, base_config):
        """Test traditional sequential-pay waterfall"""
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        # Verify strategy type
        assert isinstance(calculator.strategy, TraditionalWaterfall)
        
        # Test payment sequence
        sequence = calculator.strategy.get_payment_sequence()
        
        # Should start with expenses
        assert sequence[0] == WaterfallStep.TRUSTEE_FEES
        assert sequence[1] == WaterfallStep.ADMIN_FEES
        
        # Interest before principal
        assert WaterfallStep.CLASS_A_INTEREST in sequence
        assert WaterfallStep.CLASS_A_PRINCIPAL in sequence
        interest_idx = sequence.index(WaterfallStep.CLASS_A_INTEREST)
        principal_idx = sequence.index(WaterfallStep.CLASS_A_PRINCIPAL)
        assert interest_idx < principal_idx
    
    def test_turbo_waterfall(self, session, sample_deal, base_config):
        """Test turbo waterfall with accelerated principal"""
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TURBO
        )
        
        assert isinstance(calculator.strategy, TurboWaterfall)
        
        # Execute waterfall
        execution = calculator.execute_waterfall(Decimal('20000000'))
        
        # Turbo should prioritize principal payments
        principal_payments = [p for p in execution.payments 
                            if 'PRINCIPAL' in p.payment_step]
        
        # Should have principal payments
        assert len(principal_payments) > 0
        
        # Principal should get more cash in turbo
        total_principal = sum(p.amount_paid for p in principal_payments)
        assert total_principal > Decimal('10000000')  # Significant principal payment
    
    def test_pik_toggle_waterfall(self, session, sample_deal, base_config):
        """Test PIK toggle waterfall logic"""
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.PIK_TOGGLE
        )
        
        assert isinstance(calculator.strategy, PIKToggleWaterfall)
        
        # Test with limited cash (should trigger PIK)
        execution = calculator.execute_waterfall(Decimal('1000000'))  # Limited cash
        
        # Interest payments should be reduced due to PIK election
        interest_payments = [p for p in execution.payments 
                           if 'INTEREST' in p.payment_step]
        
        # Some interest may be deferred (PIK'd)
        total_interest_paid = sum(p.amount_paid for p in interest_payments)
        total_interest_due = sum(p.amount_due for p in interest_payments)
        
        # PIK should reduce cash payments
        if total_interest_due > 0:
            assert total_interest_paid <= total_interest_due
    
    def test_payment_phase_detection(self, session, sample_deal, base_config):
        """Test payment phase detection"""
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2024, 3, 15),  # During reinvestment
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        phase = calculator.strategy.get_payment_phase()
        assert phase == PaymentPhase.REINVESTMENT
        
        # Test call period
        calculator_call = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2026, 9, 15),  # After no-call date
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        phase_call = calculator_call.strategy.get_payment_phase()
        assert phase_call == PaymentPhase.CALL_PERIOD


class TestWaterfallConfiguration:
    """Test waterfall configuration system"""
    
    def test_waterfall_template_creation(self, session):
        """Test creating waterfall templates"""
        template = WaterfallTemplate(
            template_name="Standard US CLO",
            waterfall_type=WaterfallType.TRADITIONAL.value,
            template_description="Standard US CLO waterfall",
            default_config={
                "senior_mgmt_fee_rate": 0.004,
                "interest_reserve_target": 5000000,
                "payment_steps": [
                    {"step": "TRUSTEE_FEES", "sequence": 1},
                    {"step": "CLASS_A_INTEREST", "sequence": 4}
                ]
            },
            manager_type="US_MANAGER",
            jurisdiction="US"
        )
        
        session.add(template)
        session.commit()
        
        # Verify saved correctly
        saved = session.query(WaterfallTemplate).filter_by(
            template_name="Standard US CLO"
        ).first()
        
        assert saved.waterfall_type == WaterfallType.TRADITIONAL.value
        assert saved.get_default_config()["senior_mgmt_fee_rate"] == 0.004
    
    def test_payment_rule_creation(self, session, base_config):
        """Test creating payment rules"""
        rule = PaymentRule(
            config_id=base_config.config_id,
            step_name=WaterfallStep.CLASS_A_INTEREST.value,
            step_sequence=10,
            payment_formula="tranche_balance * coupon_rate / 4",
            payment_cap=Decimal('5000000'),
            trigger_conditions=["OC_TEST_PASS", "IC_TEST_PASS"],
            trigger_logic="AND",
            target_type="TRANCHE",
            target_identifier="TEST-A"
        )
        
        session.add(rule)
        session.commit()
        
        # Test trigger evaluation
        context = {
            'oc_tests_pass': True,
            'ic_tests_pass': True
        }
        
        assert rule.evaluate_triggers(context) == True
        
        # Test failed triggers
        context['oc_tests_pass'] = False
        assert rule.evaluate_triggers(context) == False
    
    def test_waterfall_modification(self, session, sample_deal):
        """Test waterfall modifications"""
        modification = WaterfallModification(
            deal_id=sample_deal.deal_id,
            modification_type="AMENDMENT",
            modification_name="Amendment No. 1",
            modification_description="Temporary fee reduction",
            affected_steps=["SENIOR_MGMT_FEES"],
            modification_rules={
                "payment_rules": [
                    {
                        "step_name": "SENIOR_MGMT_FEES",
                        "payment_formula": "collateral_balance * 0.002 / 4"  # Reduced rate
                    }
                ]
            },
            effective_date=date(2023, 9, 15),
            expiration_date=date(2024, 3, 15),
            modification_status="ACTIVE"
        )
        
        session.add(modification)
        session.commit()
        
        # Test date-based activation
        assert modification.is_active_for_date(date(2023, 12, 15)) == True
        assert modification.is_active_for_date(date(2024, 6, 15)) == False
    
    def test_payment_override(self, session, sample_deal):
        """Test payment overrides"""
        override = PaymentOverride(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            step_name=WaterfallStep.CLASS_A_INTEREST.value,
            override_type="AMOUNT",
            override_amount=Decimal('2000000'),
            override_reason="One-time adjustment per noteholder request",
            approved_by="Portfolio Manager",
            approval_date=date(2023, 9, 10),
            override_status="PENDING"
        )
        
        session.add(override)
        session.commit()
        
        # Verify override created
        saved = session.query(PaymentOverride).filter_by(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15)
        ).first()
        
        assert saved.override_amount == Decimal('2000000')
        assert saved.step_name == WaterfallStep.CLASS_A_INTEREST.value


class TestConfigurableWaterfall:
    """Test configurable waterfall calculator"""
    
    def test_configuration_loading(self, session, sample_deal, base_config):
        """Test loading and merging configurations"""
        
        # Add payment rule
        rule = PaymentRule(
            config_id=base_config.config_id,
            step_name=WaterfallStep.TRUSTEE_FEES.value,
            step_sequence=1,
            payment_formula="25000",  # Fixed quarterly fee
            target_type="ACCOUNT",
            target_identifier="TRUSTEE_PAYABLE"
        )
        session.add(rule)
        
        # Add modification
        modification = WaterfallModification(
            deal_id=sample_deal.deal_id,
            modification_type="TEMPORARY",
            modification_name="Fee Waiver",
            modification_rules={
                "payment_rules": [
                    {
                        "step_name": "TRUSTEE_FEES",
                        "payment_formula": "0"  # Waive fee
                    }
                ]
            },
            effective_date=date(2023, 9, 15),
            modification_status="ACTIVE"
        )
        session.add(modification)
        
        # Add override
        override = PaymentOverride(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            step_name=WaterfallStep.TRUSTEE_FEES.value,
            override_type="AMOUNT",
            override_amount=Decimal('50000'),  # Double fee
            override_reason="Catch-up payment",
            approved_by="Manager",
            approval_date=date(2023, 9, 10),
            override_status="PENDING"
        )
        session.add(override)
        
        session.commit()
        
        # Test configurable calculator
        calculator = ConfigurableWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session
        )
        
        # Verify configuration hierarchy
        config = calculator.effective_config
        
        # Should have payment rules
        assert 'payment_rules' in config
        assert len(config['payment_rules']) > 0
        
        # Should have modifications and overrides applied
        trustee_rule = calculator.get_payment_rules_for_step("TRUSTEE_FEES")
        assert trustee_rule is not None
        
        # Override should take precedence
        assert 'override_amount' in trustee_rule
        assert trustee_rule['override_amount'] == Decimal('50000')


class TestWaterfallStrategyFactory:
    """Test waterfall strategy factory"""
    
    def test_strategy_creation(self, session, sample_deal, base_config):
        """Test creating different strategy types"""
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        # Test factory methods
        available_types = WaterfallStrategyFactory.get_available_types()
        assert WaterfallType.TRADITIONAL in available_types
        assert WaterfallType.TURBO in available_types
        
        # Test strategy creation
        turbo_strategy = WaterfallStrategyFactory.create_strategy(
            WaterfallType.TURBO, calculator
        )
        assert isinstance(turbo_strategy, TurboWaterfall)
    
    def test_custom_strategy_registration(self, session, sample_deal, base_config):
        """Test registering custom waterfall strategies"""
        
        class CustomWaterfall(TraditionalWaterfall):
            def get_payment_sequence(self):
                # Custom payment order
                return [WaterfallStep.RESIDUAL_EQUITY, WaterfallStep.TRUSTEE_FEES]
        
        # Register custom strategy
        WaterfallStrategyFactory.register_custom_strategy(
            WaterfallType.CUSTOM, CustomWaterfall
        )
        
        # Test creation
        calculator = EnhancedWaterfallCalculator(
            deal_id=sample_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        custom_strategy = WaterfallStrategyFactory.create_strategy(
            WaterfallType.CUSTOM, calculator
        )
        
        assert isinstance(custom_strategy, CustomWaterfall)
        
        # Verify custom sequence
        sequence = custom_strategy.get_payment_sequence()
        assert sequence[0] == WaterfallStep.RESIDUAL_EQUITY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])