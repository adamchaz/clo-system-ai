"""
Waterfall Configuration System
Manages deal-specific waterfall rules, custom logic, and payment modifications
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any, Union
import json

from ..core.database import Base
from .waterfall_types import WaterfallType, PaymentPhase, TriggerCondition


class WaterfallTemplate(Base):
    """
    Waterfall template definitions
    Pre-built waterfall configurations for common deal types
    """
    __tablename__ = 'waterfall_templates'
    
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(100), nullable=False, unique=True)
    waterfall_type = Column(String(30), nullable=False)  # WaterfallType enum
    template_description = Column(Text)
    
    # Template configuration (JSON)
    default_config = Column(JSON, nullable=False)
    
    # Template metadata
    manager_type = Column(String(50))  # Asset manager preference
    jurisdiction = Column(String(20))   # US, European, etc.
    rating_agencies = Column(JSON)      # Preferred rating agencies
    
    # Version control
    version = Column(String(10), default='1.0')
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<WaterfallTemplate({self.template_name}: {self.waterfall_type})>"
    
    def get_default_config(self) -> Dict:
        """Parse default configuration JSON"""
        return self.default_config if isinstance(self.default_config, dict) else {}


class PaymentRule(Base):
    """
    Individual payment rules within waterfall
    Defines step-specific logic, calculations, and conditions
    """
    __tablename__ = 'payment_rules'
    
    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey('waterfall_configurations.config_id'), nullable=False)
    
    # Rule identification
    step_name = Column(String(30), nullable=False)  # WaterfallStep enum value
    step_sequence = Column(Integer, nullable=False)  # Order in waterfall
    
    # Payment logic
    payment_formula = Column(Text)  # Calculation formula or Python expression
    payment_cap = Column(Numeric(18,2))  # Maximum payment amount
    payment_floor = Column(Numeric(18,2))  # Minimum payment amount
    
    # Trigger conditions
    trigger_conditions = Column(JSON)  # List of TriggerCondition requirements
    trigger_logic = Column(String(10), default='AND')  # AND, OR logic for multiple conditions
    
    # Target specification
    target_type = Column(String(20))  # TRANCHE, ACCOUNT, EXTERNAL
    target_identifier = Column(String(50))  # Tranche ID, account name, etc.
    
    # Payment timing
    payment_frequency_override = Column(Integer)  # Override deal frequency for this step
    payment_delay_days = Column(Integer, default=0)  # Delay payment by N days
    
    # Business day adjustments
    business_day_convention = Column(String(30))
    calendar_name = Column(String(20), default='US')
    
    # Rule metadata
    rule_description = Column(Text)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    configuration = relationship("WaterfallConfiguration", back_populates="payment_rules")
    
    def get_trigger_conditions(self) -> List[str]:
        """Get list of trigger condition names"""
        if isinstance(self.trigger_conditions, list):
            return self.trigger_conditions
        elif isinstance(self.trigger_conditions, str):
            return json.loads(self.trigger_conditions)
        return []
    
    def evaluate_triggers(self, context: Dict[str, Any]) -> bool:
        """Evaluate trigger conditions against provided context"""
        conditions = self.get_trigger_conditions()
        
        if not conditions:
            return True  # No conditions = always execute
        
        results = []
        for condition in conditions:
            results.append(self._evaluate_single_condition(condition, context))
        
        # Apply logic operator
        if self.trigger_logic == 'OR':
            return any(results)
        else:  # Default to AND
            return all(results)
    
    def _evaluate_single_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate single trigger condition"""
        # Implementation would check specific conditions
        if condition == TriggerCondition.OC_TEST_FAILURE.value:
            return not context.get('oc_tests_pass', True)
        elif condition == TriggerCondition.IC_TEST_FAILURE.value:
            return not context.get('ic_tests_pass', True)
        elif condition == TriggerCondition.REINVESTMENT_END.value:
            payment_date = context.get('payment_date')
            reinvestment_end = context.get('reinvestment_end_date')
            return payment_date and reinvestment_end and payment_date >= reinvestment_end
        elif condition == TriggerCondition.CALL_DATE_REACHED.value:
            payment_date = context.get('payment_date')
            no_call_date = context.get('no_call_date')
            return payment_date and no_call_date and payment_date >= no_call_date
        
        return True  # Default to True for unknown conditions


class WaterfallModification(Base):
    """
    Temporary modifications to waterfall logic
    Handles amendments, waivers, and one-time adjustments
    """
    __tablename__ = 'waterfall_modifications'
    
    modification_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    
    # Modification details
    modification_type = Column(String(30), nullable=False)  # AMENDMENT, WAIVER, TEMPORARY
    modification_name = Column(String(100), nullable=False)
    modification_description = Column(Text)
    
    # Affected components
    affected_steps = Column(JSON)  # List of waterfall steps affected
    affected_tranches = Column(JSON)  # List of tranche IDs affected
    
    # Modification logic
    modification_rules = Column(JSON, nullable=False)  # New/modified payment rules
    override_config = Column(JSON)  # Configuration overrides
    
    # Effective period
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date)  # NULL for permanent changes
    
    # Approval tracking
    approved_by = Column(String(100))
    approval_date = Column(Date)
    approval_reference = Column(String(100))  # Amendment number, etc.
    
    # Status
    modification_status = Column(String(20), default='DRAFT')  # DRAFT, APPROVED, ACTIVE, EXPIRED
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))
    
    def is_active_for_date(self, check_date: date) -> bool:
        """Check if modification is active for given date"""
        if self.modification_status != 'ACTIVE':
            return False
            
        if check_date < self.effective_date:
            return False
            
        if self.expiration_date and check_date > self.expiration_date:
            return False
            
        return True
    
    def get_modification_rules(self) -> Dict:
        """Parse modification rules JSON"""
        return self.modification_rules if isinstance(self.modification_rules, dict) else {}


class PaymentOverride(Base):
    """
    Manual payment overrides for specific payment dates
    Allows portfolio managers to make one-time adjustments
    """
    __tablename__ = 'payment_overrides'
    
    override_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    payment_date = Column(Date, nullable=False)
    
    # Override details
    step_name = Column(String(30), nullable=False)
    override_type = Column(String(20), nullable=False)  # AMOUNT, DEFER, SKIP, REDIRECT
    
    # Override values
    override_amount = Column(Numeric(18,2))  # New payment amount
    target_override = Column(String(50))     # New payment target
    defer_to_date = Column(Date)             # Defer payment to this date
    
    # Justification
    override_reason = Column(Text, nullable=False)
    supporting_documentation = Column(Text)
    
    # Approval
    approved_by = Column(String(100), nullable=False)
    approval_date = Column(Date, nullable=False)
    
    # Status
    override_status = Column(String(20), default='PENDING')  # PENDING, APPLIED, EXPIRED
    applied_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<PaymentOverride({self.deal_id}: {self.step_name} on {self.payment_date})>"


# Enhanced WaterfallConfiguration with relationships
from .waterfall import WaterfallConfiguration

# Add relationships to existing WaterfallConfiguration
WaterfallConfiguration.payment_rules = relationship(
    "PaymentRule", 
    back_populates="configuration", 
    cascade="all, delete-orphan"
)


class ConfigurableWaterfallCalculator:
    """
    Advanced waterfall calculator with full configuration support
    Handles templates, modifications, and overrides
    """
    
    def __init__(self, deal_id: str, payment_date: date, session):
        self.deal_id = deal_id
        self.payment_date = payment_date
        self.session = session
        
        # Load configuration components
        self.base_config = self._load_base_configuration()
        self.modifications = self._load_active_modifications()
        self.overrides = self._load_payment_overrides()
        
        # Build effective configuration
        self.effective_config = self._build_effective_configuration()
    
    def _load_base_configuration(self) -> Optional[WaterfallConfiguration]:
        """Load base waterfall configuration for deal"""
        return self.session.query(WaterfallConfiguration).filter_by(
            deal_id=self.deal_id
        ).order_by(WaterfallConfiguration.effective_date.desc()).first()
    
    def _load_active_modifications(self) -> List[WaterfallModification]:
        """Load active modifications for payment date"""
        return self.session.query(WaterfallModification).filter(
            WaterfallModification.deal_id == self.deal_id,
            WaterfallModification.effective_date <= self.payment_date,
            WaterfallModification.modification_status == 'ACTIVE'
        ).filter(
            (WaterfallModification.expiration_date.is_(None)) |
            (WaterfallModification.expiration_date >= self.payment_date)
        ).all()
    
    def _load_payment_overrides(self) -> List[PaymentOverride]:
        """Load payment overrides for specific payment date"""
        return self.session.query(PaymentOverride).filter(
            PaymentOverride.deal_id == self.deal_id,
            PaymentOverride.payment_date == self.payment_date,
            PaymentOverride.override_status.in_(['PENDING', 'APPLIED'])
        ).all()
    
    def _build_effective_configuration(self) -> Dict[str, Any]:
        """Build effective configuration with all modifications applied"""
        config = {}
        
        # Start with base configuration
        if self.base_config:
            config = {
                'waterfall_type': WaterfallType.TRADITIONAL,
                'payment_rules': [],
                'fee_rates': {
                    'senior_mgmt_fee_rate': self.base_config.senior_mgmt_fee_rate,
                    'junior_mgmt_fee_rate': self.base_config.junior_mgmt_fee_rate,
                    'incentive_fee_rate': self.base_config.incentive_fee_rate
                },
                'reserve_targets': {
                    'interest_reserve_target': self.base_config.interest_reserve_target,
                    'interest_reserve_cap': self.base_config.interest_reserve_cap
                }
            }
            
            # Load payment rules
            config['payment_rules'] = self._load_payment_rules()
        
        # Apply modifications
        for modification in self.modifications:
            self._apply_modification(config, modification)
        
        # Apply overrides
        self._apply_overrides(config)
        
        return config
    
    def _load_payment_rules(self) -> List[Dict[str, Any]]:
        """Load payment rules from database"""
        if not self.base_config:
            return []
        
        rules = self.session.query(PaymentRule).filter(
            PaymentRule.config_id == self.base_config.config_id,
            PaymentRule.is_active == True
        ).filter(
            (PaymentRule.effective_date.is_(None)) |
            (PaymentRule.effective_date <= self.payment_date)
        ).filter(
            (PaymentRule.expiration_date.is_(None)) |
            (PaymentRule.expiration_date >= self.payment_date)
        ).order_by(PaymentRule.step_sequence).all()
        
        return [self._rule_to_dict(rule) for rule in rules]
    
    def _rule_to_dict(self, rule: PaymentRule) -> Dict[str, Any]:
        """Convert PaymentRule to dictionary"""
        return {
            'step_name': rule.step_name,
            'step_sequence': rule.step_sequence,
            'payment_formula': rule.payment_formula,
            'payment_cap': rule.payment_cap,
            'payment_floor': rule.payment_floor,
            'trigger_conditions': rule.get_trigger_conditions(),
            'trigger_logic': rule.trigger_logic,
            'target_type': rule.target_type,
            'target_identifier': rule.target_identifier
        }
    
    def _apply_modification(self, config: Dict[str, Any], modification: WaterfallModification):
        """Apply modification to configuration"""
        mod_rules = modification.get_modification_rules()
        
        # Apply rule modifications
        if 'payment_rules' in mod_rules:
            for rule_mod in mod_rules['payment_rules']:
                self._modify_payment_rule(config['payment_rules'], rule_mod)
        
        # Apply configuration overrides
        if modification.override_config:
            config.update(modification.override_config)
    
    def _modify_payment_rule(self, rules: List[Dict], rule_modification: Dict):
        """Apply modification to specific payment rule"""
        step_name = rule_modification.get('step_name')
        
        # Find existing rule
        existing_rule = next((r for r in rules if r['step_name'] == step_name), None)
        
        if existing_rule:
            # Modify existing rule
            existing_rule.update(rule_modification)
        else:
            # Add new rule
            rules.append(rule_modification)
    
    def _apply_overrides(self, config: Dict[str, Any]):
        """Apply payment overrides to configuration"""
        for override in self.overrides:
            # Find affected payment rule
            rules = config.get('payment_rules', [])
            rule = next((r for r in rules if r['step_name'] == override.step_name), None)
            
            if rule:
                # Apply override
                if override.override_type == 'AMOUNT' and override.override_amount:
                    rule['override_amount'] = override.override_amount
                elif override.override_type == 'DEFER' and override.defer_to_date:
                    rule['defer_to_date'] = override.defer_to_date
                elif override.override_type == 'SKIP':
                    rule['skip_payment'] = True
                elif override.override_type == 'REDIRECT' and override.target_override:
                    rule['target_identifier'] = override.target_override
    
    def get_effective_waterfall_type(self) -> WaterfallType:
        """Get effective waterfall type with modifications applied"""
        return WaterfallType(self.effective_config.get('waterfall_type', WaterfallType.TRADITIONAL))
    
    def get_payment_rules_for_step(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get effective payment rules for specific step"""
        rules = self.effective_config.get('payment_rules', [])
        return next((r for r in rules if r['step_name'] == step_name), None)