"""
Magnetar (Mag) Waterfall Implementations
Handles Magnetar CLO structures (Mag 6 through Mag 17) with specific payment rules
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal
from datetime import date
from enum import Enum
from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .waterfall_types import BaseWaterfallStrategy, WaterfallStep, PaymentPhase
from .dynamic_waterfall import DynamicWaterfallStrategy, TrancheMapping, WaterfallStructure, PaymentCategory
from .clo_deal import CLOTranche


class MagWaterfallType(str, Enum):
    """Magnetar waterfall variations"""
    MAG_6 = "MAG_6"
    MAG_7 = "MAG_7"
    MAG_8 = "MAG_8"
    MAG_9 = "MAG_9"
    MAG_10 = "MAG_10"
    MAG_11 = "MAG_11"
    MAG_12 = "MAG_12"
    MAG_13 = "MAG_13"
    MAG_14 = "MAG_14"
    MAG_15 = "MAG_15"
    MAG_16 = "MAG_16"
    MAG_17 = "MAG_17"


class MagPaymentFeature(str, Enum):
    """Magnetar-specific payment features"""
    EQUITY_CLAW_BACK = "EQUITY_CLAW_BACK"
    TURBO_PRINCIPAL = "TURBO_PRINCIPAL"
    MANAGEMENT_FEE_DEFERRAL = "MANAGEMENT_FEE_DEFERRAL"
    INCENTIVE_FEE_SHARING = "INCENTIVE_FEE_SHARING"
    REINVESTMENT_OVERLAY = "REINVESTMENT_OVERLAY"
    CALL_PROTECTION_OVERRIDE = "CALL_PROTECTION_OVERRIDE"
    EXCESS_SPREAD_CAPTURE = "EXCESS_SPREAD_CAPTURE"
    SENIOR_MANAGEMENT_CARVE_OUT = "SENIOR_MANAGEMENT_CARVE_OUT"
    PERFORMANCE_HURDLE = "PERFORMANCE_HURDLE"
    DISTRIBUTION_STOPPER = "DISTRIBUTION_STOPPER"


class MagWaterfallConfiguration(Base):
    """
    Magnetar-specific waterfall configurations
    Stores deal-specific parameters for Mag 6-17 structures
    """
    __tablename__ = 'mag_waterfall_configurations'
    
    config_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    mag_version = Column(String(10), nullable=False)  # MAG_6, MAG_7, etc.
    
    # Mag-specific parameters
    equity_hurdle_rate = Column(Numeric(6,4))  # Equity return hurdle (e.g., 0.12 = 12%)
    equity_catch_up_rate = Column(Numeric(6,4))  # Catch-up rate above hurdle
    management_fee_sharing_pct = Column(Numeric(5,4))  # % of incentive fee to manager
    
    # Turbo features
    turbo_threshold_oc_ratio = Column(Numeric(8,6))  # OC ratio triggering turbo
    turbo_threshold_ic_ratio = Column(Numeric(8,6))  # IC ratio triggering turbo
    
    # Performance metrics
    minimum_equity_irr = Column(Numeric(6,4))  # Minimum equity IRR requirement
    performance_test_frequency = Column(String(20), default='QUARTERLY')  # Test frequency
    
    # Reinvestment overlay
    reinvestment_overlay_rate = Column(Numeric(6,4))  # Additional reinvestment fee
    reinvestment_overlay_cap = Column(Numeric(18,2))  # Cap on overlay fees
    
    # Call protection overrides
    call_protection_equity_threshold = Column(Numeric(8,6))  # Equity threshold for call override
    
    # Distribution controls
    distribution_stopper_covenant = Column(String(100))  # Covenant triggering stopper
    distribution_stopper_threshold = Column(Numeric(8,6))  # Threshold value
    
    # Features enabled for this deal
    enabled_features = Column(JSON)  # List of MagPaymentFeature values
    
    # Effective dates
    effective_date = Column(Date, nullable=False)
    amendment_number = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled Magnetar features"""
        return self.enabled_features if isinstance(self.enabled_features, list) else []
    
    def is_feature_enabled(self, feature: MagPaymentFeature) -> bool:
        """Check if specific feature is enabled"""
        return feature.value in self.get_enabled_features()


class MagPerformanceMetrics(Base):
    """
    Performance metrics calculation for Magnetar deals
    Tracks equity returns, hurdle achievements, and fee calculations
    """
    __tablename__ = 'mag_performance_metrics'
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    calculation_date = Column(Date, nullable=False)
    
    # Equity performance
    equity_irr = Column(Numeric(8,6))  # Annualized equity IRR
    equity_moic = Column(Numeric(6,4))  # Multiple of invested capital
    cumulative_equity_distributions = Column(Numeric(18,2))
    
    # Hurdle calculations  
    hurdle_achievement_pct = Column(Numeric(6,4))  # % of hurdle achieved
    excess_return_above_hurdle = Column(Numeric(8,6))  # Return above hurdle rate
    catch_up_provision_activated = Column(Boolean, default=False)
    
    # Fee calculations
    base_management_fee_ytd = Column(Numeric(18,2))
    incentive_fee_accrued = Column(Numeric(18,2))
    incentive_fee_paid_ytd = Column(Numeric(18,2))
    
    # Performance tests
    oc_test_buffer = Column(Numeric(8,6))  # Cushion above minimum OC
    ic_test_buffer = Column(Numeric(8,6))  # Cushion above minimum IC
    portfolio_yield_spread = Column(Numeric(8,6))  # Spread above funding cost
    
    # Calculation metadata
    calculation_method = Column(String(50))  # ACTUAL, PROJECTED, STRESS_TEST
    calculation_notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<MagPerformanceMetrics({self.deal_id}: IRR={self.equity_irr}, Date={self.calculation_date})>"


class MagWaterfallStrategy(DynamicWaterfallStrategy):
    """
    Magnetar waterfall strategy with specific payment logic
    Handles Mag 6-17 deal structures with performance-based features
    """
    
    def __init__(self, calculator, mag_version: MagWaterfallType):
        super().__init__(calculator, f"MAGNETAR_{mag_version.value}")
        self.mag_version = mag_version
        self.mag_config = self._load_mag_configuration()
        self.performance_metrics = self._load_performance_metrics()
    
    def get_payment_sequence(self) -> List[WaterfallStep]:
        """Magnetar-specific payment sequence with performance overlays"""
        
        # Start with base dynamic sequence
        base_sequence = super().get_payment_sequence()
        
        # Apply Magnetar modifications based on version and features
        mag_sequence = self._apply_mag_modifications(base_sequence)
        
        return mag_sequence
    
    def check_payment_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Enhanced trigger checking with Magnetar-specific conditions"""
        
        # Base trigger check
        base_result = super().check_payment_triggers(step, tranche)
        
        if not base_result:
            return False
        
        # Apply Magnetar-specific triggers
        return self._check_mag_specific_triggers(step, tranche)
    
    def calculate_payment_amount(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> Decimal:
        """Magnetar payment calculations with performance adjustments"""
        
        # Get base payment amount
        base_amount = super().calculate_payment_amount(step, tranche)
        
        # Apply Magnetar-specific adjustments
        mag_amount = self._apply_mag_payment_adjustments(step, base_amount, tranche)
        
        return mag_amount
    
    def _load_mag_configuration(self) -> Optional[MagWaterfallConfiguration]:
        """Load Magnetar-specific configuration"""
        return self.calculator.session.query(MagWaterfallConfiguration).filter(
            MagWaterfallConfiguration.deal_id == self.deal_id,
            MagWaterfallConfiguration.mag_version == self.mag_version.value,
            MagWaterfallConfiguration.effective_date <= self.payment_date
        ).order_by(MagWaterfallConfiguration.effective_date.desc()).first()
    
    def _load_performance_metrics(self) -> Optional[MagPerformanceMetrics]:
        """Load latest performance metrics"""
        return self.calculator.session.query(MagPerformanceMetrics).filter(
            MagPerformanceMetrics.deal_id == self.deal_id,
            MagPerformanceMetrics.calculation_date <= self.payment_date
        ).order_by(MagPerformanceMetrics.calculation_date.desc()).first()
    
    def _apply_mag_modifications(self, base_sequence: List[WaterfallStep]) -> List[WaterfallStep]:
        """Apply Magnetar-specific modifications to payment sequence"""
        
        if not self.mag_config:
            return base_sequence
        
        modified_sequence = base_sequence.copy()
        
        # Turbo principal acceleration
        if self.mag_config.is_feature_enabled(MagPaymentFeature.TURBO_PRINCIPAL):
            modified_sequence = self._apply_turbo_modifications(modified_sequence)
        
        # Equity claw-back provisions
        if self.mag_config.is_feature_enabled(MagPaymentFeature.EQUITY_CLAW_BACK):
            modified_sequence = self._apply_equity_clawback(modified_sequence)
        
        # Management fee deferral
        if self.mag_config.is_feature_enabled(MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL):
            modified_sequence = self._apply_fee_deferral(modified_sequence)
        
        return modified_sequence
    
    def _apply_turbo_modifications(self, sequence: List[WaterfallStep]) -> List[WaterfallStep]:
        """Apply turbo principal payment modifications"""
        
        if not self._turbo_conditions_met():
            return sequence
        
        # Move principal payments earlier in sequence
        principal_steps = [step for step in sequence if 'PRINCIPAL' in step.value]
        other_steps = [step for step in sequence if 'PRINCIPAL' not in step.value]
        
        # Find position after interest payments
        interest_end = max([i for i, step in enumerate(other_steps) 
                          if 'INTEREST' in step.value], default=len(other_steps))
        
        # Insert principal payments after interest
        turbo_sequence = other_steps[:interest_end + 1] + principal_steps + other_steps[interest_end + 1:]
        
        return turbo_sequence
    
    def _apply_equity_clawback(self, sequence: List[WaterfallStep]) -> List[WaterfallStep]:
        """Apply equity claw-back provisions"""
        
        # Replace residual equity with conditional payment
        modified_sequence = []
        
        for step in sequence:
            if step == WaterfallStep.RESIDUAL_EQUITY:
                # Add conditional equity payment
                modified_sequence.append(WaterfallStep.RESIDUAL_EQUITY)  # Keep step but modify calculation
            else:
                modified_sequence.append(step)
        
        return modified_sequence
    
    def _apply_fee_deferral(self, sequence: List[WaterfallStep]) -> List[WaterfallStep]:
        """Apply management fee deferral logic"""
        
        if not self._fee_deferral_triggered():
            return sequence
        
        # Move junior management fees later in sequence
        modified_sequence = []
        deferred_fees = []
        
        for step in sequence:
            if step in [WaterfallStep.JUNIOR_MGMT_FEES, WaterfallStep.INCENTIVE_MGMT_FEES]:
                deferred_fees.append(step)
            else:
                modified_sequence.append(step)
        
        # Add deferred fees before residual
        if WaterfallStep.RESIDUAL_EQUITY in modified_sequence:
            equity_index = modified_sequence.index(WaterfallStep.RESIDUAL_EQUITY)
            modified_sequence[equity_index:equity_index] = deferred_fees
        else:
            modified_sequence.extend(deferred_fees)
        
        return modified_sequence
    
    def _check_mag_specific_triggers(self, step: WaterfallStep, tranche: Optional[CLOTranche] = None) -> bool:
        """Check Magnetar-specific payment triggers"""
        
        if not self.mag_config:
            return True
        
        # Distribution stopper
        if self.mag_config.is_feature_enabled(MagPaymentFeature.DISTRIBUTION_STOPPER):
            if self._distribution_stopper_triggered():
                # Block subordinated payments
                if step in [WaterfallStep.RESIDUAL_EQUITY, WaterfallStep.INCENTIVE_MGMT_FEES]:
                    return False
        
        # Performance hurdle requirements
        if self.mag_config.is_feature_enabled(MagPaymentFeature.PERFORMANCE_HURDLE):
            if step == WaterfallStep.INCENTIVE_MGMT_FEES:
                return self._performance_hurdle_met()
        
        # Call protection overrides
        if self.mag_config.is_feature_enabled(MagPaymentFeature.CALL_PROTECTION_OVERRIDE):
            if 'PRINCIPAL' in step.value:
                return self._call_protection_override_conditions_met()
        
        return True
    
    def _apply_mag_payment_adjustments(self, step: WaterfallStep, base_amount: Decimal, 
                                     tranche: Optional[CLOTranche] = None) -> Decimal:
        """Apply Magnetar-specific payment adjustments"""
        
        if not self.mag_config:
            return base_amount
        
        adjusted_amount = base_amount
        
        # Excess spread capture
        if (step == WaterfallStep.SENIOR_MGMT_FEES and 
            self.mag_config.is_feature_enabled(MagPaymentFeature.EXCESS_SPREAD_CAPTURE)):
            adjusted_amount = self._calculate_excess_spread_fee(base_amount)
        
        # Incentive fee sharing
        if (step == WaterfallStep.INCENTIVE_MGMT_FEES and
            self.mag_config.is_feature_enabled(MagPaymentFeature.INCENTIVE_FEE_SHARING)):
            adjusted_amount = self._calculate_shared_incentive_fee(base_amount)
        
        # Reinvestment overlay
        if (step == WaterfallStep.SENIOR_MGMT_FEES and
            self.mag_config.is_feature_enabled(MagPaymentFeature.REINVESTMENT_OVERLAY)):
            overlay_fee = self._calculate_reinvestment_overlay()
            adjusted_amount = min(adjusted_amount + overlay_fee, 
                                self.mag_config.reinvestment_overlay_cap or adjusted_amount + overlay_fee)
        
        # Equity claw-back calculation
        if (step == WaterfallStep.RESIDUAL_EQUITY and
            self.mag_config.is_feature_enabled(MagPaymentFeature.EQUITY_CLAW_BACK)):
            adjusted_amount = self._calculate_equity_after_clawback(base_amount)
        
        # Senior management carve-out
        if (step in [WaterfallStep.SENIOR_MGMT_FEES, WaterfallStep.JUNIOR_MGMT_FEES] and
            self.mag_config.is_feature_enabled(MagPaymentFeature.SENIOR_MANAGEMENT_CARVE_OUT)):
            adjusted_amount = self._apply_management_carveout(step, base_amount)
        
        return adjusted_amount
    
    def _turbo_conditions_met(self) -> bool:
        """Check if turbo conditions are satisfied"""
        if not self.mag_config:
            return False
        
        # Check OC/IC ratios vs turbo thresholds
        oc_ratio = self._calculate_current_oc_ratio()
        ic_ratio = self._calculate_current_ic_ratio()
        
        turbo_oc_threshold = self.mag_config.turbo_threshold_oc_ratio or Decimal('999')
        turbo_ic_threshold = self.mag_config.turbo_threshold_ic_ratio or Decimal('999')
        
        return oc_ratio > turbo_oc_threshold and ic_ratio > turbo_ic_threshold
    
    def _fee_deferral_triggered(self) -> bool:
        """Check if management fee deferral is triggered"""
        if not self.performance_metrics:
            return False
        
        # Defer fees if equity performance below minimum
        minimum_irr = self.mag_config.minimum_equity_irr or Decimal('0')
        current_irr = self.performance_metrics.equity_irr or Decimal('0')
        
        return current_irr < minimum_irr
    
    def _distribution_stopper_triggered(self) -> bool:
        """Check if distribution stopper is triggered"""
        if not self.mag_config:
            return False
        
        # Check if distribution stopper feature is enabled
        if not self.mag_config.is_feature_enabled(MagPaymentFeature.DISTRIBUTION_STOPPER):
            return False
        
        # Check specific covenant or performance-based triggers
        if self.performance_metrics:
            threshold = self.mag_config.distribution_stopper_threshold or Decimal('0')
            current_buffer = self.performance_metrics.oc_test_buffer or Decimal('0')
            return current_buffer < threshold
        
        return False
    
    def _performance_hurdle_met(self) -> bool:
        """Check if performance hurdle is satisfied"""
        if not self.performance_metrics or not self.mag_config:
            return False
        
        hurdle_rate = self.mag_config.equity_hurdle_rate or Decimal('0')
        current_irr = self.performance_metrics.equity_irr or Decimal('0')
        
        return current_irr >= hurdle_rate
    
    def _call_protection_override_conditions_met(self) -> bool:
        """Check call protection override conditions"""
        if not self.mag_config:
            return True  # No override conditions
        
        # Check equity threshold for call override
        if self.performance_metrics:
            equity_threshold = self.mag_config.call_protection_equity_threshold or Decimal('0')
            current_moic = self.performance_metrics.equity_moic or Decimal('0')
            return current_moic >= equity_threshold
        
        return False
    
    def _calculate_excess_spread_fee(self, base_fee: Decimal) -> Decimal:
        """Calculate excess spread capture fee"""
        if not self.performance_metrics:
            return base_fee
        
        # Add bonus based on portfolio yield spread
        spread_bonus = (self.performance_metrics.portfolio_yield_spread or Decimal('0')) * self._get_collateral_balance() / Decimal('400')  # Quarterly
        
        return base_fee + spread_bonus
    
    def _calculate_shared_incentive_fee(self, base_fee: Decimal) -> Decimal:
        """Calculate incentive fee with sharing provisions"""
        if not self.mag_config:
            return base_fee
        
        sharing_pct = self.mag_config.management_fee_sharing_pct or Decimal('1.0')
        return base_fee * sharing_pct
    
    def _calculate_reinvestment_overlay(self) -> Decimal:
        """Calculate reinvestment overlay fee"""
        if not self.mag_config:
            return Decimal('0')
        
        overlay_rate = self.mag_config.reinvestment_overlay_rate or Decimal('0')
        collateral_balance = self._get_collateral_balance()
        
        return collateral_balance * overlay_rate / Decimal('4')  # Quarterly
    
    def _calculate_equity_after_clawback(self, base_distribution: Decimal) -> Decimal:
        """Calculate equity distribution after claw-back provisions"""
        if not self.performance_metrics or not self.mag_config:
            return base_distribution
        
        # If below hurdle, hold distributions in escrow
        if not self._performance_hurdle_met():
            return Decimal('0')
        
        # If above hurdle, check for catch-up provisions
        hurdle_rate = self.mag_config.equity_hurdle_rate or Decimal('0')
        catch_up_rate = self.mag_config.equity_catch_up_rate or Decimal('1.0')
        
        excess_return = (self.performance_metrics.equity_irr or Decimal('0')) - hurdle_rate
        
        if excess_return > 0:
            # Apply catch-up calculation
            return base_distribution * catch_up_rate
        
        return base_distribution
    
    def _apply_management_carveout(self, step: WaterfallStep, base_amount: Decimal) -> Decimal:
        """Apply senior management carve-out provisions"""
        # Implementation would apply specific carve-out rules
        return base_amount
    
    def _calculate_current_oc_ratio(self) -> Decimal:
        """Calculate current over-collateralization ratio"""
        # Implementation would calculate actual OC ratio
        return Decimal('1.15')  # Placeholder
    
    def _calculate_current_ic_ratio(self) -> Decimal:
        """Calculate current interest coverage ratio"""
        # Implementation would calculate actual IC ratio  
        return Decimal('1.25')  # Placeholder
    
    def _get_collateral_balance(self) -> Decimal:
        """Get current collateral balance"""
        return self.calculator._get_collateral_balance()


class MagWaterfallFactory:
    """
    Factory for creating Magnetar waterfall configurations
    Handles version-specific settings and features
    """
    
    @classmethod
    def create_mag_config(cls, deal_id: str, mag_version: MagWaterfallType, **kwargs) -> MagWaterfallConfiguration:
        """Create Magnetar configuration with version-specific defaults"""
        
        # Base configuration
        config = MagWaterfallConfiguration(
            deal_id=deal_id,
            mag_version=mag_version.value,
            effective_date=kwargs.get('effective_date', date.today())
        )
        
        # Get default features for this version
        default_features = cls.get_mag_features_by_version(mag_version)
        config.enabled_features = [feature.value for feature in default_features]
        
        # Apply version-specific defaults
        if mag_version == MagWaterfallType.MAG_6:
            config.equity_hurdle_rate = Decimal('0.08')  # 8%
        
        elif mag_version == MagWaterfallType.MAG_7:
            config.equity_hurdle_rate = Decimal('0.08')  # 8%
        
        elif mag_version == MagWaterfallType.MAG_8:
            config.equity_hurdle_rate = Decimal('0.10')  # 10%
            config.equity_catch_up_rate = Decimal('0.80')  # 80% catch-up
        
        elif mag_version == MagWaterfallType.MAG_9:
            config.equity_hurdle_rate = Decimal('0.10')  # 10%
            config.equity_catch_up_rate = Decimal('0.80')  # 80% catch-up
        
        elif mag_version in [MagWaterfallType.MAG_10, MagWaterfallType.MAG_11]:
            config.equity_hurdle_rate = Decimal('0.11')  # 11%
            config.minimum_equity_irr = Decimal('0.07')  # Deferral threshold
        
        elif mag_version in [MagWaterfallType.MAG_12, MagWaterfallType.MAG_13]:
            config.equity_hurdle_rate = Decimal('0.115')  # 11.5%
            config.minimum_equity_irr = Decimal('0.075')  # Deferral threshold
            config.management_fee_sharing_pct = Decimal('0.70')  # Early sharing
        
        elif mag_version == MagWaterfallType.MAG_14:
            config.equity_hurdle_rate = Decimal('0.12')  # 12%
            config.management_fee_sharing_pct = Decimal('0.75')  # 75% to manager
            config.reinvestment_overlay_rate = Decimal('0.001')  # 10bps overlay
        
        elif mag_version == MagWaterfallType.MAG_15:
            config.equity_hurdle_rate = Decimal('0.125')  # 12.5%
            config.management_fee_sharing_pct = Decimal('0.75')
            config.reinvestment_overlay_rate = Decimal('0.001')
        
        elif mag_version == MagWaterfallType.MAG_16:
            config.equity_hurdle_rate = Decimal('0.13')  # 13%
            config.management_fee_sharing_pct = Decimal('0.75')
            config.reinvestment_overlay_rate = Decimal('0.001')
            config.distribution_stopper_threshold = Decimal('0.06')  # 6% buffer
        
        elif mag_version == MagWaterfallType.MAG_17:
            # Most recent with all features
            config.equity_hurdle_rate = Decimal('0.15')  # 15%
            config.minimum_equity_irr = Decimal('0.08')  # 8% minimum
            config.distribution_stopper_threshold = Decimal('0.05')  # 5% buffer
            config.management_fee_sharing_pct = Decimal('0.80')  # Higher sharing
            config.reinvestment_overlay_rate = Decimal('0.0015')  # 15bps overlay
        
        # Apply any custom parameters (override defaults)
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    @classmethod
    def get_mag_features_by_version(cls, mag_version: MagWaterfallType) -> List[MagPaymentFeature]:
        """Get typical features enabled for each Mag version"""
        
        feature_map = {
            MagWaterfallType.MAG_6: [MagPaymentFeature.TURBO_PRINCIPAL],
            MagWaterfallType.MAG_7: [MagPaymentFeature.TURBO_PRINCIPAL],
            MagWaterfallType.MAG_8: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK
            ],
            MagWaterfallType.MAG_9: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK
            ],
            MagWaterfallType.MAG_10: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL
            ],
            MagWaterfallType.MAG_11: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL
            ],
            MagWaterfallType.MAG_12: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING
            ],
            MagWaterfallType.MAG_13: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING
            ],
            MagWaterfallType.MAG_14: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING,
                MagPaymentFeature.REINVESTMENT_OVERLAY
            ],
            MagWaterfallType.MAG_15: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING,
                MagPaymentFeature.REINVESTMENT_OVERLAY,
                MagPaymentFeature.PERFORMANCE_HURDLE
            ],
            MagWaterfallType.MAG_16: [
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING,
                MagPaymentFeature.REINVESTMENT_OVERLAY,
                MagPaymentFeature.PERFORMANCE_HURDLE,
                MagPaymentFeature.DISTRIBUTION_STOPPER
            ],
            MagWaterfallType.MAG_17: [  # Most comprehensive
                MagPaymentFeature.TURBO_PRINCIPAL,
                MagPaymentFeature.EQUITY_CLAW_BACK,
                MagPaymentFeature.MANAGEMENT_FEE_DEFERRAL,
                MagPaymentFeature.INCENTIVE_FEE_SHARING,
                MagPaymentFeature.REINVESTMENT_OVERLAY,
                MagPaymentFeature.PERFORMANCE_HURDLE,
                MagPaymentFeature.DISTRIBUTION_STOPPER,
                MagPaymentFeature.CALL_PROTECTION_OVERRIDE,
                MagPaymentFeature.EXCESS_SPREAD_CAPTURE,
                MagPaymentFeature.SENIOR_MANAGEMENT_CARVE_OUT
            ]
        }
        
        return feature_map.get(mag_version, [])