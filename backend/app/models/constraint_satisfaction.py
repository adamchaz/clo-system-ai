"""
Constraint Satisfaction Engine - Advanced Portfolio Constraints
Sophisticated constraint satisfaction for CLO portfolio optimization
"""

from typing import Dict, List, Optional, Tuple, Any, Union, Set
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from abc import ABC, abstractmethod
import numpy as np
from sqlalchemy.orm import Session

from .asset import Asset
from .clo_deal import CLODeal


class ConstraintType(str, Enum):
    """Types of portfolio constraints"""
    CONCENTRATION = "CONCENTRATION"
    DIVERSIFICATION = "DIVERSIFICATION"
    CREDIT_QUALITY = "CREDIT_QUALITY"
    MATURITY = "MATURITY"
    SECTOR = "SECTOR"
    GEOGRAPHIC = "GEOGRAPHIC"
    LIQUIDITY = "LIQUIDITY"
    REGULATORY = "REGULATORY"
    COVENANT = "COVENANT"
    CUSTOM = "CUSTOM"


class ConstraintPriority(str, Enum):
    """Priority levels for constraints"""
    CRITICAL = "CRITICAL"      # Must be satisfied
    HIGH = "HIGH"              # Should be satisfied
    MEDIUM = "MEDIUM"          # Preferably satisfied
    LOW = "LOW"                # Nice to have


class ConstraintOperator(str, Enum):
    """Constraint comparison operators"""
    LESS_THAN = "LT"
    LESS_EQUAL = "LE"
    EQUAL = "EQ"
    GREATER_EQUAL = "GE"
    GREATER_THAN = "GT"
    NOT_EQUAL = "NE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"


@dataclass
class ConstraintRule:
    """Individual constraint rule"""
    constraint_id: str
    constraint_type: ConstraintType
    priority: ConstraintPriority
    name: str
    description: str
    
    # Constraint definition
    target_field: str          # Asset field to constrain
    operator: ConstraintOperator
    threshold_value: Union[Decimal, str, List[str]]
    
    # Optional parameters
    applies_to_assets: Optional[List[str]] = None  # Specific asset IDs
    sector_filter: Optional[List[str]] = None      # Sector restrictions
    rating_filter: Optional[List[str]] = None      # Rating restrictions
    
    # Tolerance and penalties
    soft_limit_tolerance: Decimal = Decimal('0.05')  # 5% tolerance for soft limits
    violation_penalty: Decimal = Decimal('1000')     # Penalty for violations
    
    # Activation conditions
    active_from_date: Optional[date] = None
    active_to_date: Optional[date] = None
    active_when_conditions: Optional[Dict[str, Any]] = None


@dataclass
class ConstraintViolation:
    """Constraint violation information"""
    constraint_id: str
    constraint_name: str
    priority: ConstraintPriority
    violation_type: str
    
    # Violation details
    current_value: Decimal
    threshold_value: Decimal
    excess_amount: Decimal
    percentage_violation: Decimal
    
    # Impact assessment
    penalty_score: Decimal
    affected_assets: List[str]
    suggested_actions: List[str]


class BaseConstraint(ABC):
    """Base class for all constraint implementations"""
    
    def __init__(self, rule: ConstraintRule):
        self.rule = rule
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        """Evaluate constraint against portfolio"""
        pass
    
    @abstractmethod
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        """Suggest actions to resolve constraint violation"""
        pass
    
    def is_active(self, evaluation_date: date) -> bool:
        """Check if constraint is active on given date"""
        if self.rule.active_from_date and evaluation_date < self.rule.active_from_date:
            return False
        if self.rule.active_to_date and evaluation_date > self.rule.active_to_date:
            return False
        return True
    
    def calculate_penalty(self, violation_amount: Decimal) -> Decimal:
        """Calculate penalty for constraint violation"""
        if violation_amount <= self.rule.soft_limit_tolerance:
            return Decimal('0')  # Within tolerance
        
        base_penalty = self.rule.violation_penalty
        severity_multiplier = min(violation_amount / self.rule.soft_limit_tolerance, Decimal('10'))
        
        return base_penalty * severity_multiplier


class ConcentrationConstraint(BaseConstraint):
    """Single asset/issuer concentration limits"""
    
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        total_par = sum(asset.par_amount or Decimal('0') for asset in portfolio)
        
        if total_par == 0:
            return None
        
        # Check each asset concentration
        max_concentration = Decimal('0')
        violating_asset = None
        
        for asset in portfolio:
            if self.rule.applies_to_assets and asset.blk_rock_id not in self.rule.applies_to_assets:
                continue
                
            asset_par = asset.par_amount or Decimal('0')
            concentration = asset_par / total_par
            
            if concentration > max_concentration:
                max_concentration = concentration
                violating_asset = asset
        
        threshold = Decimal(str(self.rule.threshold_value))
        
        if max_concentration > threshold:
            excess = max_concentration - threshold
            
            return ConstraintViolation(
                constraint_id=self.rule.constraint_id,
                constraint_name=self.rule.name,
                priority=self.rule.priority,
                violation_type="CONCENTRATION_EXCEEDED",
                current_value=max_concentration,
                threshold_value=threshold,
                excess_amount=excess,
                percentage_violation=excess / threshold * 100,
                penalty_score=self.calculate_penalty(excess),
                affected_assets=[violating_asset.blk_rock_id] if violating_asset else [],
                suggested_actions=[
                    f"Reduce exposure to {violating_asset.issue_name if violating_asset else 'largest holding'}",
                    "Diversify into additional assets",
                    f"Target concentration below {threshold:.1%}"
                ]
            )
        
        return None
    
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        return violation.suggested_actions


class SectorConcentrationConstraint(BaseConstraint):
    """Sector concentration limits"""
    
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        total_par = sum(asset.par_amount or Decimal('0') for asset in portfolio)
        
        if total_par == 0:
            return None
        
        # Calculate sector concentrations
        sector_exposures = {}
        for asset in portfolio:
            sector = getattr(asset, 'mdy_industry', 'UNKNOWN')
            asset_par = asset.par_amount or Decimal('0')
            
            if sector not in sector_exposures:
                sector_exposures[sector] = Decimal('0')
            sector_exposures[sector] += asset_par
        
        # Check each sector against limits
        threshold = Decimal(str(self.rule.threshold_value))
        max_sector_concentration = Decimal('0')
        violating_sector = None
        
        for sector, exposure in sector_exposures.items():
            concentration = exposure / total_par
            
            if concentration > max_sector_concentration:
                max_sector_concentration = concentration
                violating_sector = sector
        
        if max_sector_concentration > threshold:
            excess = max_sector_concentration - threshold
            
            # Find assets in violating sector
            affected_assets = [
                asset.blk_rock_id for asset in portfolio 
                if getattr(asset, 'mdy_industry', 'UNKNOWN') == violating_sector
            ]
            
            return ConstraintViolation(
                constraint_id=self.rule.constraint_id,
                constraint_name=self.rule.name,
                priority=self.rule.priority,
                violation_type="SECTOR_CONCENTRATION_EXCEEDED",
                current_value=max_sector_concentration,
                threshold_value=threshold,
                excess_amount=excess,
                percentage_violation=excess / threshold * 100,
                penalty_score=self.calculate_penalty(excess),
                affected_assets=affected_assets,
                suggested_actions=[
                    f"Reduce exposure to {violating_sector} sector",
                    "Diversify across additional sectors",
                    f"Target {violating_sector} concentration below {threshold:.1%}"
                ]
            )
        
        return None
    
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        return violation.suggested_actions


class CreditQualityConstraint(BaseConstraint):
    """Credit quality/rating distribution constraints"""
    
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        total_par = sum(asset.par_amount or Decimal('0') for asset in portfolio)
        
        if total_par == 0:
            return None
        
        # Calculate rating distribution
        rating_exposures = {}
        for asset in portfolio:
            rating = getattr(asset, 'mdy_rating', 'NR')
            asset_par = asset.par_amount or Decimal('0')
            
            if rating not in rating_exposures:
                rating_exposures[rating] = Decimal('0')
            rating_exposures[rating] += asset_par
        
        # Check specific rating constraint
        target_rating = self.rule.target_field  # e.g., 'CCC'
        rating_concentration = rating_exposures.get(target_rating, Decimal('0')) / total_par
        threshold = Decimal(str(self.rule.threshold_value))
        
        # Evaluate based on operator
        violation = False
        if self.rule.operator == ConstraintOperator.LESS_EQUAL and rating_concentration > threshold:
            violation = True
        elif self.rule.operator == ConstraintOperator.GREATER_EQUAL and rating_concentration < threshold:
            violation = True
        
        if violation:
            excess = abs(rating_concentration - threshold)
            
            affected_assets = [
                asset.blk_rock_id for asset in portfolio 
                if getattr(asset, 'mdy_rating', 'NR') == target_rating
            ]
            
            return ConstraintViolation(
                constraint_id=self.rule.constraint_id,
                constraint_name=self.rule.name,
                priority=self.rule.priority,
                violation_type="CREDIT_QUALITY_VIOLATION",
                current_value=rating_concentration,
                threshold_value=threshold,
                excess_amount=excess,
                percentage_violation=excess / threshold * 100 if threshold > 0 else Decimal('100'),
                penalty_score=self.calculate_penalty(excess),
                affected_assets=affected_assets,
                suggested_actions=[
                    f"Adjust {target_rating}-rated asset allocation",
                    f"Target {target_rating} concentration {'below' if self.rule.operator == ConstraintOperator.LESS_EQUAL else 'above'} {threshold:.1%}",
                    "Rebalance credit quality distribution"
                ]
            )
        
        return None
    
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        return violation.suggested_actions


class MaturityConstraint(BaseConstraint):
    """Weighted average maturity constraints"""
    
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        total_par = sum(asset.par_amount or Decimal('0') for asset in portfolio)
        
        if total_par == 0:
            return None
        
        # Calculate weighted average maturity
        total_weighted_maturity = Decimal('0')
        evaluation_date = date.today()
        
        for asset in portfolio:
            if not asset.maturity_date:
                continue
                
            asset_par = asset.par_amount or Decimal('0')
            days_to_maturity = (asset.maturity_date - evaluation_date).days
            years_to_maturity = Decimal(str(days_to_maturity / 365.25))
            
            total_weighted_maturity += asset_par * years_to_maturity
        
        weighted_avg_maturity = total_weighted_maturity / total_par
        threshold = Decimal(str(self.rule.threshold_value))
        
        # Evaluate constraint
        violation = False
        if self.rule.operator == ConstraintOperator.LESS_EQUAL and weighted_avg_maturity > threshold:
            violation = True
        elif self.rule.operator == ConstraintOperator.GREATER_EQUAL and weighted_avg_maturity < threshold:
            violation = True
        
        if violation:
            excess = abs(weighted_avg_maturity - threshold)
            
            return ConstraintViolation(
                constraint_id=self.rule.constraint_id,
                constraint_name=self.rule.name,
                priority=self.rule.priority,
                violation_type="MATURITY_CONSTRAINT_VIOLATION",
                current_value=weighted_avg_maturity,
                threshold_value=threshold,
                excess_amount=excess,
                percentage_violation=excess / threshold * 100 if threshold > 0 else Decimal('100'),
                penalty_score=self.calculate_penalty(excess),
                affected_assets=[asset.blk_rock_id for asset in portfolio],
                suggested_actions=[
                    f"Adjust portfolio maturity profile",
                    f"Target weighted average maturity {'below' if self.rule.operator == ConstraintOperator.LESS_EQUAL else 'above'} {threshold:.1f} years",
                    "Consider longer/shorter maturity assets"
                ]
            )
        
        return None
    
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        return violation.suggested_actions


class LiquidityConstraint(BaseConstraint):
    """Portfolio liquidity requirements"""
    
    def evaluate(self, portfolio: List[Asset], deal: CLODeal) -> Optional[ConstraintViolation]:
        total_par = sum(asset.par_amount or Decimal('0') for asset in portfolio)
        
        if total_par == 0:
            return None
        
        # Calculate liquidity score (simplified)
        liquid_assets_par = Decimal('0')
        
        for asset in portfolio:
            # Assets with certain characteristics are considered more liquid
            is_liquid = (
                getattr(asset, 'bond_loan', '') == 'BOND' or
                getattr(asset, 'seniority', '') in ['SENIOR', '1ST LIEN'] or
                getattr(asset, 'mdy_rating', 'CCC') in ['AAA', 'AA', 'A', 'BBB', 'BB']
            )
            
            if is_liquid:
                liquid_assets_par += asset.par_amount or Decimal('0')
        
        liquidity_ratio = liquid_assets_par / total_par
        threshold = Decimal(str(self.rule.threshold_value))
        
        if liquidity_ratio < threshold:
            shortfall = threshold - liquidity_ratio
            
            illiquid_assets = [
                asset.blk_rock_id for asset in portfolio
                if not (getattr(asset, 'bond_loan', '') == 'BOND' or
                       getattr(asset, 'seniority', '') in ['SENIOR', '1ST LIEN'])
            ]
            
            return ConstraintViolation(
                constraint_id=self.rule.constraint_id,
                constraint_name=self.rule.name,
                priority=self.rule.priority,
                violation_type="LIQUIDITY_SHORTFALL",
                current_value=liquidity_ratio,
                threshold_value=threshold,
                excess_amount=shortfall,
                percentage_violation=shortfall / threshold * 100,
                penalty_score=self.calculate_penalty(shortfall),
                affected_assets=illiquid_assets,
                suggested_actions=[
                    f"Increase liquid assets allocation to meet {threshold:.1%} requirement",
                    "Consider bonds over loans for better liquidity",
                    "Focus on senior/first lien instruments",
                    "Improve credit quality for enhanced liquidity"
                ]
            )
        
        return None
    
    def suggest_resolution(self, portfolio: List[Asset], violation: ConstraintViolation) -> List[str]:
        return violation.suggested_actions


class ConstraintSatisfactionEngine:
    """
    Advanced constraint satisfaction engine
    Manages and evaluates all portfolio constraints
    """
    
    def __init__(self, deal: CLODeal, session: Session):
        self.deal = deal
        self.session = session
        self.constraints: Dict[str, BaseConstraint] = {}
        self.constraint_factory = {
            ConstraintType.CONCENTRATION: ConcentrationConstraint,
            ConstraintType.SECTOR: SectorConcentrationConstraint,
            ConstraintType.CREDIT_QUALITY: CreditQualityConstraint,
            ConstraintType.MATURITY: MaturityConstraint,
            ConstraintType.LIQUIDITY: LiquidityConstraint
        }
        self.logger = logging.getLogger(__name__)
    
    def add_constraint(self, rule: ConstraintRule) -> None:
        """Add constraint to engine"""
        if rule.constraint_type not in self.constraint_factory:
            raise ValueError(f"Unsupported constraint type: {rule.constraint_type}")
        
        constraint_class = self.constraint_factory[rule.constraint_type]
        constraint = constraint_class(rule)
        self.constraints[rule.constraint_id] = constraint
        
        self.logger.info(f"Added constraint: {rule.name}")
    
    def remove_constraint(self, constraint_id: str) -> None:
        """Remove constraint from engine"""
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            self.logger.info(f"Removed constraint: {constraint_id}")
    
    def evaluate_all_constraints(self, portfolio: List[Asset], 
                                evaluation_date: date = None) -> List[ConstraintViolation]:
        """Evaluate all constraints against portfolio"""
        if evaluation_date is None:
            evaluation_date = date.today()
        
        violations = []
        
        for constraint_id, constraint in self.constraints.items():
            if not constraint.is_active(evaluation_date):
                continue
            
            violation = constraint.evaluate(portfolio, self.deal)
            if violation:
                violations.append(violation)
        
        # Sort by priority and severity
        violations.sort(key=lambda v: (
            self._priority_order(v.priority),
            -float(v.penalty_score)
        ))
        
        return violations
    
    def calculate_total_penalty(self, violations: List[ConstraintViolation]) -> Decimal:
        """Calculate total penalty score for all violations"""
        return sum(v.penalty_score for v in violations)
    
    def get_constraint_satisfaction_score(self, portfolio: List[Asset]) -> Decimal:
        """Calculate overall constraint satisfaction score (0-100)"""
        violations = self.evaluate_all_constraints(portfolio)
        
        if not violations:
            return Decimal('100')  # Perfect satisfaction
        
        # Calculate weighted penalty based on priority
        total_penalty = Decimal('0')
        max_possible_penalty = Decimal('0')
        
        for violation in violations:
            priority_weight = self._get_priority_weight(violation.priority)
            weighted_penalty = violation.penalty_score * priority_weight
            total_penalty += weighted_penalty
            max_possible_penalty += violation.constraint.rule.violation_penalty * priority_weight
        
        if max_possible_penalty == 0:
            return Decimal('100')
        
        # Convert to 0-100 score
        satisfaction_ratio = max(Decimal('0'), Decimal('1') - (total_penalty / max_possible_penalty))
        return satisfaction_ratio * 100
    
    def suggest_portfolio_improvements(self, portfolio: List[Asset]) -> Dict[str, List[str]]:
        """Suggest improvements to satisfy constraints"""
        violations = self.evaluate_all_constraints(portfolio)
        
        suggestions = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for violation in violations:
            priority_key = violation.priority.value.lower()
            if priority_key in suggestions:
                suggestions[priority_key].extend(violation.suggested_actions)
        
        return suggestions
    
    def optimize_for_constraints(self, portfolio: List[Asset], 
                                available_assets: List[Asset]) -> List[Asset]:
        """Optimize portfolio to satisfy constraints (simplified implementation)"""
        
        optimized_portfolio = portfolio.copy()
        violations = self.evaluate_all_constraints(optimized_portfolio)
        
        # Simple heuristic: remove worst violating assets and replace with compliant ones
        max_iterations = 10
        iteration = 0
        
        while violations and iteration < max_iterations:
            # Find most problematic asset
            asset_violation_counts = {}
            for violation in violations:
                for asset_id in violation.affected_assets:
                    if asset_id not in asset_violation_counts:
                        asset_violation_counts[asset_id] = 0
                    asset_violation_counts[asset_id] += float(violation.penalty_score)
            
            if not asset_violation_counts:
                break
            
            # Remove most problematic asset
            worst_asset_id = max(asset_violation_counts.keys(), 
                               key=lambda k: asset_violation_counts[k])
            
            optimized_portfolio = [
                asset for asset in optimized_portfolio 
                if asset.blk_rock_id != worst_asset_id
            ]
            
            # Try to add a compliant replacement
            for candidate in available_assets:
                if candidate.blk_rock_id not in [a.blk_rock_id for a in optimized_portfolio]:
                    # Test adding this asset
                    test_portfolio = optimized_portfolio + [candidate]
                    test_violations = self.evaluate_all_constraints(test_portfolio)
                    
                    if len(test_violations) < len(violations):
                        optimized_portfolio = test_portfolio
                        break
            
            violations = self.evaluate_all_constraints(optimized_portfolio)
            iteration += 1
        
        return optimized_portfolio
    
    def _priority_order(self, priority: ConstraintPriority) -> int:
        """Get numeric order for priority sorting"""
        order_map = {
            ConstraintPriority.CRITICAL: 0,
            ConstraintPriority.HIGH: 1,
            ConstraintPriority.MEDIUM: 2,
            ConstraintPriority.LOW: 3
        }
        return order_map.get(priority, 999)
    
    def _get_priority_weight(self, priority: ConstraintPriority) -> Decimal:
        """Get weighting factor for priority"""
        weight_map = {
            ConstraintPriority.CRITICAL: Decimal('10'),
            ConstraintPriority.HIGH: Decimal('5'),
            ConstraintPriority.MEDIUM: Decimal('2'),
            ConstraintPriority.LOW: Decimal('1')
        }
        return weight_map.get(priority, Decimal('1'))
    
    def create_standard_clo_constraints(self) -> List[ConstraintRule]:
        """Create standard CLO portfolio constraints"""
        
        constraints = [
            # Single asset concentration
            ConstraintRule(
                constraint_id="SINGLE_ASSET_CONC",
                constraint_type=ConstraintType.CONCENTRATION,
                priority=ConstraintPriority.CRITICAL,
                name="Single Asset Concentration",
                description="Maximum exposure to any single asset",
                target_field="par_amount",
                operator=ConstraintOperator.LESS_EQUAL,
                threshold_value=Decimal('0.02'),  # 2%
                violation_penalty=Decimal('5000')
            ),
            
            # Sector concentration
            ConstraintRule(
                constraint_id="SECTOR_CONC",
                constraint_type=ConstraintType.SECTOR,
                priority=ConstraintPriority.HIGH,
                name="Sector Concentration",
                description="Maximum exposure to any single sector",
                target_field="mdy_industry",
                operator=ConstraintOperator.LESS_EQUAL,
                threshold_value=Decimal('0.15'),  # 15%
                violation_penalty=Decimal('3000')
            ),
            
            # CCC rating limit
            ConstraintRule(
                constraint_id="CCC_LIMIT",
                constraint_type=ConstraintType.CREDIT_QUALITY,
                priority=ConstraintPriority.CRITICAL,
                name="CCC Rating Limit",
                description="Maximum exposure to CCC-rated assets",
                target_field="CCC",
                operator=ConstraintOperator.LESS_EQUAL,
                threshold_value=Decimal('0.07'),  # 7%
                violation_penalty=Decimal('10000')
            ),
            
            # Weighted average maturity
            ConstraintRule(
                constraint_id="WAL_LIMIT",
                constraint_type=ConstraintType.MATURITY,
                priority=ConstraintPriority.MEDIUM,
                name="Weighted Average Life",
                description="Maximum weighted average life of portfolio",
                target_field="maturity_date",
                operator=ConstraintOperator.LESS_EQUAL,
                threshold_value=Decimal('5.5'),  # 5.5 years
                violation_penalty=Decimal('2000')
            ),
            
            # Minimum liquidity
            ConstraintRule(
                constraint_id="MIN_LIQUIDITY",
                constraint_type=ConstraintType.LIQUIDITY,
                priority=ConstraintPriority.HIGH,
                name="Minimum Liquidity",
                description="Minimum percentage of liquid assets",
                target_field="liquidity_score",
                operator=ConstraintOperator.GREATER_EQUAL,
                threshold_value=Decimal('0.30'),  # 30%
                violation_penalty=Decimal('4000')
            )
        ]
        
        return constraints
    
    def load_standard_constraints(self) -> None:
        """Load standard CLO constraints into engine"""
        standard_constraints = self.create_standard_clo_constraints()
        
        for rule in standard_constraints:
            self.add_constraint(rule)
        
        self.logger.info(f"Loaded {len(standard_constraints)} standard constraints")


class ConstraintSatisfactionService:
    """
    Service layer for constraint satisfaction
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def evaluate_portfolio_constraints(self, 
                                     deal_id: str, 
                                     portfolio: List[Asset],
                                     custom_constraints: List[ConstraintRule] = None) -> Dict[str, Any]:
        """Evaluate portfolio against constraints"""
        
        # Get deal
        deal = self.session.query(CLODeal).filter(CLODeal.deal_id == deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Create constraint engine
        engine = ConstraintSatisfactionEngine(deal, self.session)
        engine.load_standard_constraints()
        
        # Add custom constraints
        if custom_constraints:
            for rule in custom_constraints:
                engine.add_constraint(rule)
        
        # Evaluate constraints
        violations = engine.evaluate_all_constraints(portfolio)
        satisfaction_score = engine.get_constraint_satisfaction_score(portfolio)
        total_penalty = engine.calculate_total_penalty(violations)
        suggestions = engine.suggest_portfolio_improvements(portfolio)
        
        return {
            'deal_id': deal_id,
            'evaluation_type': 'constraint_satisfaction',
            'satisfaction_score': float(satisfaction_score),
            'total_penalty': float(total_penalty),
            'violations_count': len(violations),
            'violations': [self._violation_to_dict(v) for v in violations],
            'improvement_suggestions': suggestions,
            'constraints_evaluated': len(engine.constraints)
        }
    
    def optimize_portfolio_for_constraints(self,
                                         deal_id: str,
                                         current_portfolio: List[Asset],
                                         available_assets: List[Asset],
                                         custom_constraints: List[ConstraintRule] = None) -> Dict[str, Any]:
        """Optimize portfolio to satisfy constraints"""
        
        # Get deal
        deal = self.session.query(CLODeal).filter(CLODeal.deal_id == deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Create constraint engine
        engine = ConstraintSatisfactionEngine(deal, self.session)
        engine.load_standard_constraints()
        
        if custom_constraints:
            for rule in custom_constraints:
                engine.add_constraint(rule)
        
        # Evaluate initial state
        initial_violations = engine.evaluate_all_constraints(current_portfolio)
        initial_score = engine.get_constraint_satisfaction_score(current_portfolio)
        
        # Optimize portfolio
        optimized_portfolio = engine.optimize_for_constraints(current_portfolio, available_assets)
        
        # Evaluate optimized state
        final_violations = engine.evaluate_all_constraints(optimized_portfolio)
        final_score = engine.get_constraint_satisfaction_score(optimized_portfolio)
        
        # Calculate changes
        assets_removed = [
            asset.blk_rock_id for asset in current_portfolio 
            if asset.blk_rock_id not in [a.blk_rock_id for a in optimized_portfolio]
        ]
        
        assets_added = [
            asset.blk_rock_id for asset in optimized_portfolio
            if asset.blk_rock_id not in [a.blk_rock_id for a in current_portfolio]
        ]
        
        return {
            'deal_id': deal_id,
            'optimization_type': 'constraint_satisfaction_optimization',
            'initial_satisfaction_score': float(initial_score),
            'final_satisfaction_score': float(final_score),
            'score_improvement': float(final_score - initial_score),
            'initial_violations': len(initial_violations),
            'final_violations': len(final_violations),
            'violations_resolved': len(initial_violations) - len(final_violations),
            'assets_removed': assets_removed,
            'assets_added': assets_added,
            'optimized_portfolio_size': len(optimized_portfolio)
        }
    
    def _violation_to_dict(self, violation: ConstraintViolation) -> Dict[str, Any]:
        """Convert constraint violation to dictionary"""
        return {
            'constraint_id': violation.constraint_id,
            'constraint_name': violation.constraint_name,
            'priority': violation.priority.value,
            'violation_type': violation.violation_type,
            'current_value': float(violation.current_value),
            'threshold_value': float(violation.threshold_value),
            'excess_amount': float(violation.excess_amount),
            'percentage_violation': float(violation.percentage_violation),
            'penalty_score': float(violation.penalty_score),
            'affected_assets_count': len(violation.affected_assets),
            'suggested_actions': violation.suggested_actions
        }