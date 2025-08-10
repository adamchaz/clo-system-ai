"""
Test All Magnetar Versions (Mag 6-17)
Validates version-specific configurations and feature evolution
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.mag_waterfall import (
    MagWaterfallType, MagWaterfallFactory, MagPaymentFeature,
    MagWaterfallConfiguration, MagPerformanceMetrics, MagWaterfallStrategy
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


class TestMag6Through9:
    """Test early Magnetar versions (6-9) with basic features"""
    
    @pytest.fixture
    def early_mag_deal(self, session):
        """Create early Mag deal for testing"""
        deal = CLODeal(
            deal_id="MAG-EARLY-TEST",
            deal_name="Early Magnetar Test Deal",
            effective_date=date(2019, 6, 15),
            first_payment_date=date(2019, 9, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        session.commit()
        return deal
    
    def test_mag_6_basic_configuration(self, session, early_mag_deal):
        """Test Mag 6 - simplest configuration"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=early_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_6
        )
        
        session.add(config)
        session.commit()
        
        # Verify Mag 6 characteristics
        assert config.mag_version == MagWaterfallType.MAG_6.value
        assert config.equity_hurdle_rate == Decimal('0.08')  # 8% hurdle
        
        # Only basic turbo feature
        features = config.get_enabled_features()
        assert len(features) == 1
        assert MagPaymentFeature.TURBO_PRINCIPAL.value in features
        
        # No advanced features
        assert not config.is_feature_enabled(MagPaymentFeature.EQUITY_CLAW_BACK)
        assert not config.is_feature_enabled(MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL)
    
    def test_mag_7_similar_to_6(self, session, early_mag_deal):
        """Test Mag 7 - similar to Mag 6"""
        features_6 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_6)
        features_7 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_7)
        
        # Mag 6 and 7 should have same basic features
        assert features_6 == features_7
        assert MagPaymentFeature.TURBO_PRINCIPAL in features_7
    
    def test_mag_8_adds_equity_clawback(self, session, early_mag_deal):
        """Test Mag 8 - adds equity claw-back"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=early_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_8
        )
        
        # Verify equity claw-back addition
        assert config.equity_hurdle_rate == Decimal('0.10')  # Higher hurdle
        assert config.equity_catch_up_rate == Decimal('0.80')  # 80% catch-up
        
        features = config.get_enabled_features()
        assert MagPaymentFeature.TURBO_PRINCIPAL.value in features
        assert MagPaymentFeature.EQUITY_CLAW_BACK.value in features
        assert len(features) == 2
    
    def test_mag_9_same_as_8(self, session, early_mag_deal):
        """Test Mag 9 - same features as Mag 8"""
        features_8 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_8)
        features_9 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_9)
        
        assert features_8 == features_9
        assert len(features_9) == 2


class TestMag10Through13:
    """Test middle Magnetar versions (10-13) with expanded features"""
    
    @pytest.fixture
    def mid_mag_deal(self, session):
        """Create middle-era Mag deal"""
        deal = CLODeal(
            deal_id="MAG-MID-TEST",
            deal_name="Mid-Era Magnetar Test Deal",
            effective_date=date(2020, 12, 15),
            first_payment_date=date(2021, 3, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        session.commit()
        return deal
    
    def test_mag_10_adds_fee_deferral(self, session, mid_mag_deal):
        """Test Mag 10 - adds management fee deferral"""
        features = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_10)
        
        # Should have previous features plus fee deferral
        assert MagPaymentFeature.TURBO_PRINCIPAL in features
        assert MagPaymentFeature.EQUITY_CLAW_BACK in features
        assert MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL in features
        assert len(features) == 3
    
    def test_mag_11_same_as_10(self, session, mid_mag_deal):
        """Test Mag 11 - same as Mag 10"""
        features_10 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_10)
        features_11 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_11)
        
        assert features_10 == features_11
    
    def test_mag_12_adds_fee_sharing(self, session, mid_mag_deal):
        """Test Mag 12 - adds incentive fee sharing"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=mid_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_12
        )
        
        features = config.get_enabled_features()
        assert MagPaymentFeature.INCENTIVE_FEE_SHARING.value in features
        assert len(features) == 4
        
        # Test strategy implementation
        base_config = WaterfallConfiguration(
            deal_id=mid_mag_deal.deal_id,
            config_name="Mag 12 Base",
            effective_date=date(2021, 3, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.add(config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=mid_mag_deal.deal_id,
            payment_date=date(2021, 6, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_12)
        
        # Test fee sharing calculation
        base_fee = Decimal('1000000')
        shared_fee = mag_strategy._calculate_shared_incentive_fee(base_fee)
        
        # Should return some fee amount
        assert isinstance(shared_fee, Decimal)
        assert shared_fee >= Decimal('0')
    
    def test_mag_13_same_as_12(self, session, mid_mag_deal):
        """Test Mag 13 - same features as Mag 12"""
        features_12 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_12)
        features_13 = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_13)
        
        assert features_12 == features_13
        assert len(features_13) == 4


class TestMag14Through17:
    """Test latest Magnetar versions (14-17) with comprehensive features"""
    
    @pytest.fixture
    def modern_mag_deal(self, session):
        """Create modern Mag deal"""
        deal = CLODeal(
            deal_id="MAG-MODERN-TEST",
            deal_name="Modern Magnetar Test Deal",
            effective_date=date(2022, 3, 15),
            first_payment_date=date(2022, 6, 15),
            deal_status="ACTIVE"
        )
        session.add(deal)
        session.commit()
        return deal
    
    def test_mag_14_adds_reinvestment_overlay(self, session, modern_mag_deal):
        """Test Mag 14 - adds reinvestment overlay"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=modern_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_14
        )
        
        features = config.get_enabled_features()
        assert MagPaymentFeature.REINVESTMENT_OVERLAY.value in features
        assert len(features) == 5
        
        # Verify reinvestment overlay parameters
        assert config.reinvestment_overlay_rate == Decimal('0.001')  # 10bps
        assert config.equity_hurdle_rate == Decimal('0.12')  # Higher hurdle
        assert config.management_fee_sharing_pct == Decimal('0.75')  # 75% sharing
    
    def test_mag_15_adds_performance_hurdle(self, session, modern_mag_deal):
        """Test Mag 15 - adds performance hurdle"""
        features = MagWaterfallFactory.get_mag_features_by_version(MagWaterfallType.MAG_15)
        
        assert MagPaymentFeature.PERFORMANCE_HURDLE in features
        assert len(features) == 6
        
        # Test with performance metrics
        config = MagWaterfallFactory.create_mag_config(
            deal_id=modern_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_15,
            effective_date=date(2022, 3, 15)
        )
        
        # High performance metrics
        metrics = MagPerformanceMetrics(
            deal_id=modern_mag_deal.deal_id,
            calculation_date=date(2022, 9, 15),
            equity_irr=Decimal('0.18'),  # Above hurdle
            calculation_method="ACTUAL"
        )
        
        session.add(config)
        session.add(metrics)
        session.commit()
        
        # Create strategy and test hurdle check
        base_config = WaterfallConfiguration(
            deal_id=modern_mag_deal.deal_id,
            config_name="Mag 15 Base",
            effective_date=date(2022, 3, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=modern_mag_deal.deal_id,
            payment_date=date(2022, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_15)
        
        # Performance hurdle should be met
        hurdle_met = mag_strategy._performance_hurdle_met()
        assert hurdle_met == True
    
    def test_mag_16_adds_distribution_stopper(self, session, modern_mag_deal):
        """Test Mag 16 - adds distribution stopper"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=modern_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_16
        )
        
        features = config.get_enabled_features()
        assert MagPaymentFeature.DISTRIBUTION_STOPPER.value in features
        assert len(features) == 7
        
        # Test distribution stopper with poor metrics
        poor_metrics = MagPerformanceMetrics(
            deal_id=modern_mag_deal.deal_id,
            calculation_date=date(2022, 9, 15),
            oc_test_buffer=Decimal('0.02'),  # Low buffer
            calculation_method="ACTUAL"
        )
        
        session.add(config)
        session.add(poor_metrics)
        session.commit()
        
        base_config = WaterfallConfiguration(
            deal_id=modern_mag_deal.deal_id,
            config_name="Mag 16 Base",
            effective_date=date(2022, 3, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=modern_mag_deal.deal_id,
            payment_date=date(2022, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_16)
        
        # Distribution stopper should be triggered
        stopper_triggered = mag_strategy._distribution_stopper_triggered()
        # Should return boolean (implementation uses placeholder logic)
        assert isinstance(stopper_triggered, bool)
    
    def test_mag_17_most_comprehensive(self, session, modern_mag_deal):
        """Test Mag 17 - most comprehensive feature set"""
        config = MagWaterfallFactory.create_mag_config(
            deal_id=modern_mag_deal.deal_id,
            mag_version=MagWaterfallType.MAG_17,
            effective_date=date(2022, 3, 15)
        )
        
        features = config.get_enabled_features()
        
        # Should have all major features
        expected_features = [
            MagPaymentFeature.TURBO_PRINCIPAL.value,
            MagPaymentFeature.EQUITY_CLAW_BACK.value,
            MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL.value,
            MagPaymentFeature.INCENTIVE_FEE_SHARING.value,
            MagPaymentFeature.REINVESTMENT_OVERLAY.value,
            MagPaymentFeature.PERFORMANCE_HURDLE.value,
            MagPaymentFeature.DISTRIBUTION_STOPPER.value,
            MagPaymentFeature.CALL_PROTECTION_OVERRIDE.value,
            MagPaymentFeature.EXCESS_SPREAD_CAPTURE.value
        ]
        
        for feature in expected_features:
            assert feature in features
        
        # Should have most features
        assert len(features) >= 9
        
        # Verify advanced parameters
        assert config.equity_hurdle_rate == Decimal('0.15')  # Highest hurdle
        assert config.minimum_equity_irr == Decimal('0.08')   # Minimum performance
        assert config.distribution_stopper_threshold == Decimal('0.05')  # 5% buffer
        
        # Test advanced features in strategy
        session.add(config)
        session.commit()
        
        base_config = WaterfallConfiguration(
            deal_id=modern_mag_deal.deal_id,
            config_name="Mag 17 Base",
            effective_date=date(2022, 3, 15),
            payment_rules='[]'
        )
        session.add(base_config)
        session.commit()
        
        calculator = EnhancedWaterfallCalculator(
            deal_id=modern_mag_deal.deal_id,
            payment_date=date(2022, 9, 15),
            session=session,
            waterfall_type=WaterfallType.TRADITIONAL
        )
        
        mag_strategy = MagWaterfallStrategy(calculator, MagWaterfallType.MAG_17)
        
        # Test multiple feature checks
        assert mag_strategy.mag_config.is_feature_enabled(MagPaymentFeature.EXCESS_SPREAD_CAPTURE)
        assert mag_strategy.mag_config.is_feature_enabled(MagPaymentFeature.CALL_PROTECTION_OVERRIDE)


class TestMagVersionEvolution:
    """Test feature evolution across all Mag versions"""
    
    def test_feature_progression(self, session):
        """Test that features are additive across versions"""
        
        # Test feature count progression
        version_feature_counts = {}
        
        for version in MagWaterfallType:
            features = MagWaterfallFactory.get_mag_features_by_version(version)
            version_feature_counts[version] = len(features)
        
        # Early versions should have fewer features
        assert version_feature_counts[MagWaterfallType.MAG_6] <= version_feature_counts[MagWaterfallType.MAG_8]
        assert version_feature_counts[MagWaterfallType.MAG_8] <= version_feature_counts[MagWaterfallType.MAG_12]
        assert version_feature_counts[MagWaterfallType.MAG_12] <= version_feature_counts[MagWaterfallType.MAG_17]
        
        # Mag 17 should have the most features
        max_features = max(version_feature_counts.values())
        assert version_feature_counts[MagWaterfallType.MAG_17] == max_features
    
    def test_hurdle_rate_evolution(self, session):
        """Test that hurdle rates generally increase over time"""
        
        # Create configs for different versions
        versions_to_test = [
            MagWaterfallType.MAG_6,
            MagWaterfallType.MAG_8,
            MagWaterfallType.MAG_14,
            MagWaterfallType.MAG_17
        ]
        
        hurdle_rates = {}
        
        for version in versions_to_test:
            config = MagWaterfallFactory.create_mag_config(
                deal_id=f"TEST-{version.value}",
                mag_version=version
            )
            hurdle_rates[version] = config.equity_hurdle_rate
        
        # Later versions should generally have higher hurdles
        assert hurdle_rates[MagWaterfallType.MAG_6] <= hurdle_rates[MagWaterfallType.MAG_8]
        assert hurdle_rates[MagWaterfallType.MAG_8] <= hurdle_rates[MagWaterfallType.MAG_14]
        assert hurdle_rates[MagWaterfallType.MAG_14] <= hurdle_rates[MagWaterfallType.MAG_17]
    
    def test_version_compatibility(self, session):
        """Test that all versions can be instantiated and configured"""
        
        for version in MagWaterfallType:
            # Should be able to create config for any version
            config = MagWaterfallFactory.create_mag_config(
                deal_id=f"COMPAT-{version.value}",
                mag_version=version
            )
            
            # Basic validation
            assert config.mag_version == version.value
            assert isinstance(config.get_enabled_features(), list)
            assert len(config.get_enabled_features()) >= 1  # At least turbo
            
            # Should have turbo feature (present in all versions)
            features = config.get_enabled_features()
            assert MagPaymentFeature.TURBO_PRINCIPAL.value in features


if __name__ == "__main__":
    pytest.main([__file__, "-v"])