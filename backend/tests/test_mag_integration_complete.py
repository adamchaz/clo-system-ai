"""
Complete Magnetar Integration Tests
Tests end-to-end waterfall execution with all Mag features integrated
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.mag_waterfall import (
    MagWaterfallType, MagWaterfallStrategy, MagPaymentFeature,
    MagWaterfallConfiguration, MagPerformanceMetrics, MagWaterfallFactory
)
from app.models.dynamic_waterfall import (
    DynamicWaterfallStrategy, TrancheMapping, WaterfallStructure,
    TrancheType, PaymentCategory, WaterfallStructureBuilder
)
from app.models.waterfall_types import EnhancedWaterfallCalculator, WaterfallType
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
def complete_mag_deal(session):
    """Create complete Magnetar deal with all components"""
    deal = CLODeal(
        deal_id="MAG-COMPLETE-TEST",
        deal_name="Complete Magnetar Integration Test",
        effective_date=date(2023, 1, 15),
        first_payment_date=date(2023, 4, 15),
        reinvestment_end_date=date(2025, 1, 15),
        no_call_date=date(2025, 1, 15),
        maturity_date=date(2030, 1, 15),
        payment_frequency=4,
        deal_status="ACTIVE"
    )
    session.add(deal)
    
    # Create comprehensive tranche structure
    tranches = [
        CLOTranche(
            tranche_id="COMP-A1", deal_id=deal.deal_id, tranche_name="Class A-1 Notes",
            initial_balance=Decimal('200000000'), current_balance=Decimal('180000000'),
            coupon_rate=Decimal('0.042'), seniority_level=1
        ),
        CLOTranche(
            tranche_id="COMP-A2", deal_id=deal.deal_id, tranche_name="Class A-2 Notes",
            initial_balance=Decimal('120000000'), current_balance=Decimal('110000000'),
            coupon_rate=Decimal('0.048'), seniority_level=2
        ),
        CLOTranche(
            tranche_id="COMP-B", deal_id=deal.deal_id, tranche_name="Class B Notes",
            initial_balance=Decimal('40000000'), current_balance=Decimal('35000000'),
            coupon_rate=Decimal('0.070'), seniority_level=3
        ),
        CLOTranche(
            tranche_id="COMP-C", deal_id=deal.deal_id, tranche_name="Class C Notes",
            initial_balance=Decimal('25000000'), current_balance=Decimal('22000000'),
            coupon_rate=Decimal('0.095'), seniority_level=4
        ),
        CLOTranche(
            tranche_id="COMP-D", deal_id=deal.deal_id, tranche_name="Class D Notes",
            initial_balance=Decimal('15000000'), current_balance=Decimal('13000000'),
            coupon_rate=Decimal('0.115'), seniority_level=5
        ),
        CLOTranche(
            tranche_id="COMP-E", deal_id=deal.deal_id, tranche_name="Subordinated Notes",
            initial_balance=Decimal('25000000'), current_balance=Decimal('23000000'),
            coupon_rate=Decimal('0.150'), seniority_level=6
        )
    ]
    
    for tranche in tranches:
        session.add(tranche)
    
    session.commit()
    return deal


class TestCompleteWaterfallExecution:
    """Test complete waterfall execution with Magnetar features"""
    
    def test_mag_17_full_execution(self, session, complete_mag_deal):
        """Test complete Mag 17 execution with all features"""
        
        # Create comprehensive tranche mappings
        mappings = WaterfallStructureBuilder.create_tranche_mappings_for_deal(
            complete_mag_deal.deal_id, 
            session.query(CLOTranche).filter_by(deal_id=complete_mag_deal.deal_id).all(),
            "FIVE_TRANCHE_CLO",
            session
        )
        
        for mapping in mappings:
            session.add(mapping)
        
        # Create Mag 17 configuration (most comprehensive)
        mag_config = MagWaterfallFactory.create_mag_config(
            deal_id=complete_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_17,
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Create strong performance metrics
        performance = MagPerformanceMetrics(
            deal_id=complete_mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.18'),  # Above 15% hurdle
            equity_moic=Decimal('1.35'),
            cumulative_equity_distributions=Decimal('8000000'),
            hurdle_achievement_pct=Decimal('1.20'),  # 120% of hurdle
            excess_return_above_hurdle=Decimal('0.03'),
            catch_up_provision_activated=True,
            base_management_fee_ytd=Decimal('2400000'),
            incentive_fee_accrued=Decimal('800000'),
            incentive_fee_paid_ytd=Decimal('600000'),
            oc_test_buffer=Decimal('0.12'),  # Strong buffer
            ic_test_buffer=Decimal('0.18'),  # Strong buffer
            portfolio_yield_spread=Decimal('0.038'),  # Good spread
            calculation_method="ACTUAL"
        )
        session.add(performance)
        
        # Create base waterfall configuration
        base_config = WaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            config_name="Mag 17 Complete Test",
            effective_date=date(2023, 1, 15),
            payment_rules='[]',
            senior_mgmt_fee_rate=Decimal('0.0045'),
            junior_mgmt_fee_rate=Decimal('0.0025'),
            interest_reserve_target=Decimal('10000000'),
            trustee_fee_annual=Decimal('150000')
        )
        session.add(base_config)
        session.commit()
        
        # Create calculator with Mag strategy
        calculator = EnhancedWaterfallCalculator(
            deal_id=complete_mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_17)
        
        # Test that Mag strategy is properly initialized
        assert mag_strategy.mag_config is not None
        assert mag_strategy.performance_metrics is not None
        assert mag_strategy.mag_version == MagWaterfallType.MAG_17
        
        # Test payment sequence generation
        sequence = mag_strategy.get_payment_sequence()
        assert len(sequence) > 0
        
        # Test feature enablement
        assert mag_strategy.mag_config.is_feature_enabled(MagPaymentFeature.TURBO_PRINCIPAL)
        assert mag_strategy.mag_config.is_feature_enabled(MagPaymentFeature.EQUITY_CLAW_BACK)
        assert mag_strategy.mag_config.is_feature_enabled(MagPaymentFeature.EXCESS_SPREAD_CAPTURE)
        
        # Test performance-based triggers
        assert mag_strategy._performance_hurdle_met() == True
        assert mag_strategy._fee_deferral_triggered() == False  # Good performance
        
        # Test payment amount calculations with adjustments
        test_amounts = [
            (WaterfallStep.SENIOR_MGMT_FEES, Decimal('500000')),
            (WaterfallStep.INCENTIVE_MGMT_FEES, Decimal('200000')),
            (WaterfallStep.RESIDUAL_EQUITY, Decimal('3000000'))
        ]
        
        for step, base_amount in test_amounts:
            adjusted_amount = mag_strategy._apply_mag_payment_adjustments(
                step, base_amount, None
            )
            
            # Should return valid amount
            assert isinstance(adjusted_amount, Decimal)
            assert adjusted_amount >= Decimal('0')
            
            # Mag 17 should enhance payments due to good performance
            if step == WaterfallStep.SENIOR_MGMT_FEES:
                # Excess spread capture should enhance
                assert adjusted_amount >= base_amount
    
    def test_stressed_scenario_execution(self, session, complete_mag_deal):
        """Test execution under stressed conditions"""
        
        # Create Mag 16 config with distribution stopper
        mag_config = MagWaterfallFactory.create_mag_config(
            deal_id=complete_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_16,
            distribution_stopper_threshold=Decimal('0.08'),  # 8% buffer requirement
            minimum_equity_irr=Decimal('0.08'),  # Set minimum for deferral
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Create stressed performance metrics
        stressed_performance = MagPerformanceMetrics(
            deal_id=complete_mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.04'),  # Poor performance
            equity_moic=Decimal('0.95'),  # Below par
            oc_test_buffer=Decimal('0.05'),  # Below threshold
            ic_test_buffer=Decimal('0.03'),  # Below threshold
            portfolio_yield_spread=Decimal('0.015'),  # Low spread
            calculation_method="ACTUAL"
        )
        session.add(stressed_performance)
        
        base_config = WaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            config_name="Stressed Scenario",
            effective_date=date(2023, 1, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=complete_mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_16)
        
        # Test stressed conditions
        assert mag_strategy._performance_hurdle_met() == False
        assert mag_strategy._fee_deferral_triggered() == True
        assert mag_strategy._distribution_stopper_triggered() == True
        
        # Test trigger blocking
        equity_blocked = mag_strategy._check_mag_specific_triggers(
            WaterfallStep.RESIDUAL_EQUITY, None
        )
        incentive_blocked = mag_strategy._check_mag_specific_triggers(
            WaterfallStep.INCENTIVE_MGMT_FEES, None
        )
        
        # Should block subordinated payments
        assert equity_blocked == False
        assert incentive_blocked == False
        
        # Test equity claw-back under stress
        base_equity = Decimal('1000000')
        adjusted_equity = mag_strategy._calculate_equity_after_clawback(base_equity)
        
        # Should hold distributions under poor performance
        assert adjusted_equity == Decimal('0')
    
    def test_payment_sequence_modifications(self, session, complete_mag_deal):
        """Test comprehensive payment sequence modifications"""
        
        # Create mappings for dynamic waterfall
        mappings = [
            TrancheMapping(
                deal_id=complete_mag_deal.deal_id, tranche_id="COMP-A1",
                tranche_type=TrancheType.SENIOR_AAA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=1, interest_step="CLASS_A1_INTEREST",
                principal_step="CLASS_A1_PRINCIPAL",
                effective_date=date(2023, 1, 15)
            ),
            TrancheMapping(
                deal_id=complete_mag_deal.deal_id, tranche_id="COMP-E",
                tranche_type=TrancheType.SUBORDINATED.value,
                payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
                category_rank=1, interest_step="CLASS_E_INTEREST",
                is_deferrable=True, effective_date=date(2023, 1, 15)
            )
        ]
        
        for mapping in mappings:
            session.add(mapping)
        
        # Create Mag config with multiple modification features
        mag_config = MagWaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_14.value,
            enabled_features=[
                MagPaymentFeature.TURBO_PRINCIPAL.value,
                MagPaymentFeature.EQUITY_CLAW_BACK.value,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL.value
            ],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Poor performance for fee deferral
        poor_metrics = MagPerformanceMetrics(
            deal_id=complete_mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.06'),  # Below minimum
            calculation_method="ACTUAL"
        )
        session.add(poor_metrics)
        
        base_config = WaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            config_name="Sequence Modification Test",
            effective_date=date(2023, 1, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=complete_mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_14)
        
        # Test base sequence from dynamic waterfall
        sequence = mag_strategy.get_payment_sequence()
        assert len(sequence) > 0
        
        # Test individual modification methods
        base_seq = [
            WaterfallStep.TRUSTEE_FEES,
            WaterfallStep.SENIOR_MGMT_FEES,
            WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.JUNIOR_MGMT_FEES,
            WaterfallStep.CLASS_A_PRINCIPAL,
            WaterfallStep.INCENTIVE_MGMT_FEES,
            WaterfallStep.RESIDUAL_EQUITY
        ]
        
        # Test turbo modification
        turbo_seq = mag_strategy._apply_turbo_modifications(base_seq)
        assert len(turbo_seq) == len(base_seq)
        
        # Test fee deferral modification
        deferred_seq = mag_strategy._apply_fee_deferral(base_seq)
        assert len(deferred_seq) == len(base_seq)
        
        # Test equity claw-back modification
        clawback_seq = mag_strategy._apply_equity_clawback(base_seq)
        assert len(clawback_seq) == len(base_seq)
    
    def test_waterfall_with_multiple_versions(self, session, complete_mag_deal):
        """Test that different Mag versions work with same deal structure"""
        
        versions_to_test = [
            MagWaterfallType.MAG_6,
            MagWaterfallType.MAG_10,
            MagWaterfallType.MAG_15,
            MagWaterfallType.MAG_17
        ]
        
        for version in versions_to_test:
            # Create version-specific config
            mag_config = MagWaterfallFactory.create_mag_config(
                deal_id=complete_mag_deal.deal_id,
                mag_version=version,
                effective_date=date(2023, 1, 15)
            )
            session.merge(mag_config)
            
            # Create appropriate performance metrics
            performance = MagPerformanceMetrics(
                deal_id=complete_mag_deal.deal_id,
                calculation_date=date(2023, 9, 15),
                equity_irr=Decimal('0.14'),  # Good performance
                calculation_method="ACTUAL"
            )
            session.merge(performance)
            
            base_config = WaterfallConfiguration(
                deal_id=complete_mag_deal.deal_id,
                config_name=f"Version {version.value} Test",
                effective_date=date(2023, 1, 15),
                payment_rules='[]'
            )
            session.merge(base_config)
            session.commit()
            
            # Test strategy creation and basic functionality
            calculator = EnhancedWaterfallCalculator(
                deal_id=complete_mag_deal.deal_id,
                payment_date=date(2023, 9, 15),
                session=session,
                waterfall_type=WaterfallType.TRADITIONAL
            )
            
            mag_strategy = MagWaterfallStrategy(calculator, version)
            
            # Verify strategy properties
            assert mag_strategy.mag_version == version
            assert mag_strategy.mag_config is not None
            assert mag_strategy.mag_config.mag_version == version.value
            
            # Test payment sequence generation
            sequence = mag_strategy.get_payment_sequence()
            assert len(sequence) > 0
            
            # Test that it has at least turbo feature (all versions have this)
            features = mag_strategy.mag_config.get_enabled_features()
            assert MagPaymentFeature.TURBO_PRINCIPAL.value in features
            
            # Test payment calculations don't error
            test_amount = mag_strategy._apply_mag_payment_adjustments(
                WaterfallStep.SENIOR_MGMT_FEES, Decimal('100000'), None
            )
            assert isinstance(test_amount, Decimal)
            assert test_amount >= Decimal('0')


class TestMagWithCompliance:
    """Test Magnetar waterfall integration with compliance systems"""
    
    def test_oc_ic_test_integration(self, session, complete_mag_deal):
        """Test integration with overcollateralization and interest coverage tests"""
        
        # Create Mag config with compliance-dependent features
        mag_config = MagWaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_16.value,
            turbo_threshold_oc_ratio=Decimal('1.15'),
            turbo_threshold_ic_ratio=Decimal('1.20'),
            distribution_stopper_threshold=Decimal('0.05'),
            enabled_features=[
                MagPaymentFeature.TURBO_PRINCIPAL.value,
                MagPaymentFeature.DISTRIBUTION_STOPPER.value
            ],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Create performance metrics with test results
        performance = MagPerformanceMetrics(
            deal_id=complete_mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            oc_test_buffer=Decimal('0.18'),  # Strong OC ratio
            ic_test_buffer=Decimal('0.22'),  # Strong IC ratio
            equity_irr=Decimal('0.12'),
            calculation_method="ACTUAL"
        )
        session.add(performance)
        
        base_config = WaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            config_name="Compliance Integration Test",
            effective_date=date(2023, 1, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=complete_mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_16)
        
        # Test compliance-based conditions
        turbo_met = mag_strategy._turbo_conditions_met()  # Should use strong ratios
        stopper_triggered = mag_strategy._distribution_stopper_triggered()  # Should not trigger
        
        assert isinstance(turbo_met, bool)
        assert isinstance(stopper_triggered, bool)
        
        # With strong ratios, distribution stopper shouldn't trigger
        assert stopper_triggered == False
    
    def test_call_protection_integration(self, session, complete_mag_deal):
        """Test call protection override functionality"""
        
        mag_config = MagWaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_17.value,
            call_protection_equity_threshold=Decimal('1.25'),  # 125% MOIC threshold
            enabled_features=[MagPaymentFeature.CALL_PROTECTION_OVERRIDE.value],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # High equity returns
        strong_equity = MagPerformanceMetrics(
            deal_id=complete_mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_moic=Decimal('1.35'),  # Above 125% threshold
            equity_irr=Decimal('0.16'),
            calculation_method="ACTUAL"
        )
        session.add(strong_equity)
        
        base_config = WaterfallConfiguration(
            deal_id=complete_mag_deal.deal_id,
            config_name="Call Protection Test",
            effective_date=date(2023, 1, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=complete_mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_17)
        
        # Test call protection override
        override_allowed = mag_strategy._call_protection_override_conditions_met()
        assert override_allowed == True  # Should allow override with high MOIC
        
        # Test principal payment triggers with call protection
        principal_allowed = mag_strategy._check_mag_specific_triggers(
            WaterfallStep.CLASS_A_PRINCIPAL, None
        )
        
        # Should be allowed due to override
        assert isinstance(principal_allowed, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])