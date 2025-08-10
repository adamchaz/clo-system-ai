"""
Test Magnetar (Mag) Waterfall Implementations
Validates Mag 6-17 waterfall variations with performance-based features
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
    TrancheType, PaymentCategory
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
def mag_deal(session):
    """Create Magnetar CLO deal for testing"""
    deal = CLODeal(
        deal_id="MAG-14-TEST",
        deal_name="Magnetar CLO Test Deal",
        effective_date=date(2023, 1, 15),
        first_payment_date=date(2023, 4, 15),
        reinvestment_end_date=date(2025, 1, 15),
        no_call_date=date(2025, 1, 15),
        maturity_date=date(2030, 1, 15),
        payment_frequency=4,
        deal_status="ACTIVE"
    )
    session.add(deal)
    
    # Create 5-tranche structure typical of Mag deals
    tranches = [
        CLOTranche(
            tranche_id="MAG14-A", deal_id=deal.deal_id, tranche_name="Class A Notes",
            initial_balance=Decimal('320000000'), current_balance=Decimal('300000000'),
            coupon_rate=Decimal('0.045'), seniority_level=1
        ),
        CLOTranche(
            tranche_id="MAG14-B", deal_id=deal.deal_id, tranche_name="Class B Notes",
            initial_balance=Decimal('45000000'), current_balance=Decimal('40000000'),
            coupon_rate=Decimal('0.070'), seniority_level=2
        ),
        CLOTranche(
            tranche_id="MAG14-C", deal_id=deal.deal_id, tranche_name="Class C Notes",
            initial_balance=Decimal('25000000'), current_balance=Decimal('22000000'),
            coupon_rate=Decimal('0.090'), seniority_level=3
        ),
        CLOTranche(
            tranche_id="MAG14-D", deal_id=deal.deal_id, tranche_name="Class D Notes",
            initial_balance=Decimal('15000000'), current_balance=Decimal('13000000'),
            coupon_rate=Decimal('0.110'), seniority_level=4
        ),
        CLOTranche(
            tranche_id="MAG14-E", deal_id=deal.deal_id, tranche_name="Subordinated Notes",
            initial_balance=Decimal('20000000'), current_balance=Decimal('18000000'),
            coupon_rate=Decimal('0.150'), seniority_level=5
        )
    ]
    
    for tranche in tranches:
        session.add(tranche)
    
    session.commit()
    return deal


@pytest.fixture
def base_waterfall_config(session, mag_deal):
    """Create base waterfall configuration"""
    config = WaterfallConfiguration(
        deal_id=mag_deal.deal_id,
        config_name="Mag 14 Base Config",
        effective_date=date(2023, 1, 15),
        payment_rules='[]',
        senior_mgmt_fee_rate=Decimal('0.0045'),
        junior_mgmt_fee_rate=Decimal('0.0025'),
        interest_reserve_target=Decimal('8000000'),
        trustee_fee_annual=Decimal('150000')
    )
    session.add(config)
    session.commit()
    return config


class TestMagWaterfallConfiguration:
    """Test Magnetar waterfall configuration and performance metrics"""
    
    def test_mag_configuration_creation(self, session, mag_deal):
        """Test creating Magnetar-specific configurations"""
        config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_14.value,
            equity_hurdle_rate=Decimal('0.12'),
            equity_catch_up_rate=Decimal('0.80'),
            management_fee_sharing_pct=Decimal('0.75'),
            turbo_threshold_oc_ratio=Decimal('1.15'),
            turbo_threshold_ic_ratio=Decimal('1.25'),
            minimum_equity_irr=Decimal('0.08'),
            reinvestment_overlay_rate=Decimal('0.001'),
            enabled_features=[
                MagPaymentFeature.TURBO_PRINCIPAL.value,
                MagPaymentFeature.EQUITY_CLAW_BACK.value,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL.value,
                MagPaymentFeature.INCENTIVE_FEE_SHARING.value,
                MagPaymentFeature.REINVESTMENT_OVERLAY.value,
                MagPaymentFeature.PERFORMANCE_HURDLE.value
            ],
            effective_date=date(2023, 1, 15)
        )
        
        session.add(config)
        session.commit()
        
        # Verify configuration
        saved = session.query(MagWaterfallConfiguration).filter_by(
            deal_id=mag_deal.deal_id
        ).first()
        
        assert saved.mag_version == MagWaterfallType.MAG_14.value
        assert saved.equity_hurdle_rate == Decimal('0.12')
        assert saved.is_feature_enabled(MagPaymentFeature.TURBO_PRINCIPAL)
        assert saved.is_feature_enabled(MagPaymentFeature.EQUITY_CLAW_BACK)
        assert not saved.is_feature_enabled(MagPaymentFeature.DISTRIBUTION_STOPPER)
    
    def test_performance_metrics_tracking(self, session, mag_deal):
        """Test performance metrics calculation and tracking"""
        metrics = MagPerformanceMetrics(
            deal_id=mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.14'),  # 14% IRR
            equity_moic=Decimal('1.25'),
            cumulative_equity_distributions=Decimal('5000000'),
            hurdle_achievement_pct=Decimal('1.167'),  # 14%/12% = 116.7%
            excess_return_above_hurdle=Decimal('0.02'),
            catch_up_provision_activated=True,
            base_management_fee_ytd=Decimal('1800000'),
            incentive_fee_accrued=Decimal('500000'),
            oc_test_buffer=Decimal('0.08'),
            ic_test_buffer=Decimal('0.12'),
            portfolio_yield_spread=Decimal('0.035'),
            calculation_method="ACTUAL"
        )
        
        session.add(metrics)
        session.commit()
        
        # Verify metrics
        saved = session.query(MagPerformanceMetrics).filter_by(
            deal_id=mag_deal.deal_id
        ).first()
        
        assert saved.equity_irr == Decimal('0.14')
        assert saved.catch_up_provision_activated == True
        assert saved.excess_return_above_hurdle == Decimal('0.02')


class TestMagWaterfallStrategy:
    """Test Magnetar waterfall strategy implementation"""
    
    def test_mag_strategy_initialization(self, session, mag_deal, base_waterfall_config):
        """Test Magnetar strategy initialization"""
        # Create Mag configuration
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_14.value,
            equity_hurdle_rate=Decimal('0.12'),
            enabled_features=[MagPaymentFeature.TURBO_PRINCIPAL.value],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        session.commit()
        
        # Create calculator and strategy
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_14)
        
        # Verify initialization
        assert mag_strategy.mag_version == MagWaterfallType.MAG_14
        assert mag_strategy.mag_config is not None
        assert mag_strategy.mag_config.mag_version == MagWaterfallType.MAG_14.value
    
    def test_mag_payment_sequence_modifications(self, session, mag_deal, base_waterfall_config):
        """Test Magnetar-specific payment sequence modifications"""
        # Create Mag config with turbo feature
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_10.value,
            turbo_threshold_oc_ratio=Decimal('1.10'),
            turbo_threshold_ic_ratio=Decimal('1.20'),
            enabled_features=[
                MagPaymentFeature.TURBO_PRINCIPAL.value,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL.value
            ],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Create performance metrics showing low performance
        metrics = MagPerformanceMetrics(
            deal_id=mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.06'),  # Below minimum
            oc_test_buffer=Decimal('0.15'),  # Good buffer
            ic_test_buffer=Decimal('0.25'),  # Good buffer
            calculation_method="ACTUAL"
        )
        session.add(metrics)
        session.commit()
        
        # Create strategy
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_10)
        
        # Test payment sequence generation
        sequence = mag_strategy.get_payment_sequence()
        
        # Should include standard steps
        assert WaterfallStep.TRUSTEE_FEES in sequence
        assert WaterfallStep.SENIOR_MGMT_FEES in sequence
        
        # Verify modifications applied
        step_values = [step.value for step in sequence]
        assert len(step_values) > 5  # Should have multiple steps
    
    def test_turbo_principal_conditions(self, session, mag_deal, base_waterfall_config):
        """Test turbo principal payment conditions"""
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_8.value,
            turbo_threshold_oc_ratio=Decimal('1.10'),
            turbo_threshold_ic_ratio=Decimal('1.20'),
            enabled_features=[MagPaymentFeature.TURBO_PRINCIPAL.value],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_8)
        
        # Test turbo conditions (using placeholder implementation)
        turbo_met = mag_strategy._turbo_conditions_met()
        
        # Should return boolean
        assert isinstance(turbo_met, bool)
    
    def test_equity_clawback_calculation(self, session, mag_deal, base_waterfall_config):
        """Test equity claw-back payment calculation"""
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_15.value,
            equity_hurdle_rate=Decimal('0.12'),
            equity_catch_up_rate=Decimal('0.80'),
            enabled_features=[MagPaymentFeature.EQUITY_CLAW_BACK.value],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Performance below hurdle
        metrics = MagPerformanceMetrics(
            deal_id=mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.10'),  # Below 12% hurdle
            calculation_method="ACTUAL"
        )
        session.add(metrics)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_15)
        
        # Test equity calculation with claw-back
        base_distribution = Decimal('1000000')
        adjusted_distribution = mag_strategy._calculate_equity_after_clawback(base_distribution)
        
        # Should hold distributions when below hurdle
        assert adjusted_distribution == Decimal('0')
        
        # Update metrics to exceed hurdle
        metrics.equity_irr = Decimal('0.15')  # Above hurdle
        session.commit()
        
        # Reload metrics
        mag_strategy.performance_metrics = mag_strategy._load_performance_metrics()
        
        adjusted_distribution_2 = mag_strategy._calculate_equity_after_clawback(base_distribution)
        
        # Should allow distributions with catch-up
        assert adjusted_distribution_2 > Decimal('0')
    
    def test_management_fee_deferral(self, session, mag_deal, base_waterfall_config):
        """Test management fee deferral logic"""
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_12.value,
            minimum_equity_irr=Decimal('0.08'),
            enabled_features=[MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL.value],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Poor performance metrics
        metrics = MagPerformanceMetrics(
            deal_id=mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            equity_irr=Decimal('0.05'),  # Below minimum
            calculation_method="ACTUAL"
        )
        session.add(metrics)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_12)
        
        # Test fee deferral trigger
        deferral_triggered = mag_strategy._fee_deferral_triggered()
        assert deferral_triggered == True
        
        # Test sequence modification
        base_sequence = [
            WaterfallStep.TRUSTEE_FEES,
            WaterfallStep.JUNIOR_MGMT_FEES,
            WaterfallStep.CLASS_A_INTEREST,
            WaterfallStep.RESIDUAL_EQUITY
        ]
        
        modified_sequence = mag_strategy._apply_fee_deferral(base_sequence)
        
        # Junior fees should be moved later
        assert WaterfallStep.JUNIOR_MGMT_FEES in modified_sequence
        junior_index = modified_sequence.index(WaterfallStep.JUNIOR_MGMT_FEES)
        equity_index = modified_sequence.index(WaterfallStep.RESIDUAL_EQUITY)
        assert junior_index < equity_index  # Still before residual


class TestMagWaterfallFactory:
    """Test Magnetar waterfall factory pattern"""
    
    def test_mag_6_configuration(self, session):
        """Test Mag 6 configuration creation"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id="MAG-6-TEST",
            mag_version=MagWaterfallType.MAG_6,
            effective_date=date(2023, 1, 15)
        )
        
        # Verify Mag 6 defaults
        assert config.equity_hurdle_rate == Decimal('0.08')
        assert MagPaymentFeature.TURBO_PRINCIPAL.value in config.get_enabled_features()
        assert len(config.get_enabled_features()) == 1
    
    def test_mag_17_configuration(self, session):
        """Test Mag 17 configuration (most comprehensive)"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id="MAG-17-TEST",
            mag_version=MagWaterfallType.MAG_17,
            effective_date=date(2023, 1, 15)
        )
        
        # Verify Mag 17 comprehensive features
        assert config.equity_hurdle_rate == Decimal('0.15')
        assert config.minimum_equity_irr == Decimal('0.08')
        assert config.distribution_stopper_threshold == Decimal('0.05')
        
        enabled_features = config.get_enabled_features()
        assert MagPaymentFeature.TURBO_PRINCIPAL.value in enabled_features
        assert MagPaymentFeature.EQUITY_CLAW_BACK.value in enabled_features
        assert MagPaymentFeature.PERFORMANCE_HURDLE.value in enabled_features
        assert MagPaymentFeature.DISTRIBUTION_STOPPER.value in enabled_features
        assert MagPaymentFeature.EXCESS_SPREAD_CAPTURE.value in enabled_features
        
        # Should have most comprehensive feature set
        assert len(enabled_features) >= 8
    
    def test_features_by_version(self, session):
        """Test feature evolution across Mag versions"""
        # Early versions (Mag 6-7) - basic features
        mag_6_features = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_6)
        assert len(mag_6_features) == 1
        assert MagPaymentFeature.TURBO_PRINCIPAL in mag_6_features
        
        # Mid versions (Mag 10-13) - additional features
        mag_12_features = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_12)
        assert len(mag_12_features) >= 4
        assert MagPaymentFeature.TURBO_PRINCIPAL in mag_12_features
        assert MagPaymentFeature.INCENTIVE_FEE_SHARING in mag_12_features
        
        # Latest versions (Mag 17) - comprehensive features
        mag_17_features = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_17)
        assert len(mag_17_features) >= 9
        assert MagPaymentFeature.EXCESS_SPREAD_CAPTURE in mag_17_features
        assert MagPaymentFeature.SENIOR_MANAGEMENT_CARVE_OUT in mag_17_features
    
    def test_custom_configuration_parameters(self, session):
        """Test custom parameter override in factory"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id="CUSTOM-MAG-TEST",
            mag_version=MagWaterfallType.MAG_14,
            effective_date=date(2023, 1, 15),
            equity_hurdle_rate=Decimal('0.18'),  # Custom hurdle
            management_fee_sharing_pct=Decimal('0.90')  # Custom sharing
        )
        
        # Custom parameters should override defaults
        assert config.equity_hurdle_rate == Decimal('0.18')
        assert config.management_fee_sharing_pct == Decimal('0.90')
        
        # Default features should still be present
        enabled_features = config.get_enabled_features()
        assert MagPaymentFeature.TURBO_PRINCIPAL.value in enabled_features


class TestMagIntegrationWithDynamicWaterfall:
    """Test integration of Magnetar features with dynamic waterfall system"""
    
    def test_mag_strategy_with_dynamic_base(self, session, mag_deal, base_waterfall_config):
        """Test Magnetar strategy extending dynamic waterfall"""
        # Create tranche mappings for dynamic system
        mappings = [
            TrancheMapping(
                deal_id=mag_deal.deal_id, tranche_id="MAG14-A",
                tranche_type=TrancheType.SENIOR_AAA.value,
                payment_category=PaymentCategory.SENIOR_INTEREST.value,
                category_rank=1, interest_step="CLASS_A_INTEREST",
                effective_date=date(2023, 1, 15)
            ),
            TrancheMapping(
                deal_id=mag_deal.deal_id, tranche_id="MAG14-E",
                tranche_type=TrancheType.SUBORDINATED.value,
                payment_category=PaymentCategory.SUBORDINATED_INTEREST.value,
                category_rank=1, interest_step="CLASS_E_INTEREST",
                is_deferrable=True, effective_date=date(2023, 1, 15)
            )
        ]
        
        for mapping in mappings:
            session.add(mapping)
        
        # Create Mag configuration
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_14.value,
            enabled_features=[
                MagPaymentFeature.TURBO_PRINCIPAL.value,
                MagPaymentFeature.REINVESTMENT_OVERLAY.value
            ],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        session.commit()
        
        # Create calculator
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        # Create Mag strategy
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_14)
        
        # Test that it inherits from dynamic strategy
        assert isinstance(mag_strategy, DynamicWaterfallStrategy)
        
        # Test payment sequence generation
        sequence = mag_strategy.get_payment_sequence()
        assert len(sequence) > 0
        
        # Should include both base dynamic steps and Mag modifications
        step_values = [step.value for step in sequence]
        assert "TRUSTEE_FEES" in step_values or any("FEE" in step for step in step_values)
    
    def test_payment_amount_calculations_with_mag_features(self, session, mag_deal, base_waterfall_config):
        """Test payment calculations with Magnetar-specific adjustments"""
        # Setup Mag config with fee sharing
        mag_config = MagWaterfallConfiguration(
            deal_id=mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_16.value,
            management_fee_sharing_pct=Decimal('0.75'),
            reinvestment_overlay_rate=Decimal('0.001'),
            enabled_features=[
                MagPaymentFeature.INCENTIVE_FEE_SHARING.value,
                MagPaymentFeature.REINVESTMENT_OVERLAY.value,
                MagPaymentFeature.EXCESS_SPREAD_CAPTURE.value
            ],
            effective_date=date(2023, 1, 15)
        )
        session.add(mag_config)
        
        # Add performance metrics for spread calculation
        metrics = MagPerformanceMetrics(
            deal_id=mag_deal.deal_id,
            calculation_date=date(2023, 9, 15),
            portfolio_yield_spread=Decimal('0.025'),  # 2.5% spread
            calculation_method="ACTUAL"
        )
        session.add(metrics)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=mag_deal.deal_id,
            payment_date=date(2023, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_16)
        
        # Test incentive fee sharing
        base_incentive_fee = Decimal('1000000')
        adjusted_fee = mag_strategy._calculate_shared_incentive_fee(base_incentive_fee)
        
        # Should be reduced by sharing percentage
        expected_fee = base_incentive_fee * Decimal('0.75')
        assert adjusted_fee == expected_fee
        
        # Test excess spread capture
        base_mgmt_fee = Decimal('500000')
        enhanced_fee = mag_strategy._calculate_excess_spread_fee(base_mgmt_fee)
        
        # Should be higher due to excess spread
        assert enhanced_fee >= base_mgmt_fee


if __name__ == "__main__":
    pytest.main([__file__, "-v"])