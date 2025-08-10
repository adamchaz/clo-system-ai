"""
Portfolio Optimization Engine - Main.bas VBA Conversion
Converts VBA Main.bas (1,175+ lines) to Python with sophisticated optimization algorithms
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from enum import Enum
from dataclasses import dataclass
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text, JSON

from ..core.database import Base
from .asset import Asset
from .clo_deal import CLODeal
from .clo_deal_engine import CLODealEngine, AccountType, CashType


class OptimizationType(str, Enum):
    """Optimization algorithm types"""
    GENERIC_RANKING = "GENERIC_RANKING"
    GREEDY_SELECTION = "GREEDY_SELECTION"
    CONSTRAINT_SATISFACTION = "CONSTRAINT_SATISFACTION"
    MONTE_CARLO = "MONTE_CARLO"
    SCENARIO_ANALYSIS = "SCENARIO_ANALYSIS"


class ObjectiveWeightType(str, Enum):
    """Objective function weight types"""
    OC_RATIO = "OC_RATIO"          # Test 33, 32, 37
    IC_RATIO = "IC_RATIO"          # Test 36, 35
    DIVERSITY_SCORE = "DIVERSITY_SCORE"
    CREDIT_QUALITY = "CREDIT_QUALITY"
    YIELD_SPREAD = "YIELD_SPREAD"


@dataclass
class OptimizationInputs:
    """Optimization input parameters"""
    max_assets: int = 100
    max_loan_size: Decimal = Decimal('50000000')  # $50M
    increase_current_loans: bool = True
    run_hypothesis_indicator: bool = False
    max_par_amount: Decimal = Decimal('10000000')  # $10M
    include_current_assets: bool = True
    output_results: bool = True


@dataclass
class ObjectiveWeights:
    """Objective function weights for optimization"""
    oc_test_32: Decimal = Decimal('0.30')  # OC Test weight
    oc_test_33: Decimal = Decimal('0.25')  # OC Test weight  
    oc_test_37: Decimal = Decimal('0.20')  # OC Test weight
    ic_test_35: Decimal = Decimal('0.15')  # IC Test weight
    ic_test_36: Decimal = Decimal('0.10')  # IC Test weight
    
    def get_weight(self, test_number: int) -> Decimal:
        """Get weight for specific test number"""
        weight_map = {
            32: self.oc_test_32,
            33: self.oc_test_33,
            37: self.oc_test_37,
            35: self.ic_test_35,
            36: self.ic_test_36
        }
        return weight_map.get(test_number, Decimal('0'))


@dataclass
class ComplianceTestResult:
    """Individual compliance test result"""
    test_number: int
    test_name: str
    comments: str
    numerator: Decimal
    denominator: Decimal
    result: Decimal
    threshold: Decimal
    pass_fail: bool
    pass_fail_comment: str


@dataclass
class OptimizationResult:
    """Optimization algorithm result"""
    asset_id: str
    blk_rock_id: str
    objective_value: Decimal
    par_amount: Decimal
    compliance_results: List[ComplianceTestResult]
    improvement_score: Decimal


class PortfolioOptimizationEngine:
    """
    Main portfolio optimization engine
    Converted from VBA Main.bas - handles asset selection and portfolio optimization
    """
    
    def __init__(self, deal: CLODeal, session: Session):
        self.deal = deal
        self.session = session
        self.deal_name = deal.deal_name
        
        # Core components
        self.deal_engine: Optional[CLODealEngine] = None
        self.current_portfolio: List[Asset] = []
        self.potential_assets: List[Asset] = []
        self.hypothesis_portfolio: List[Asset] = []
        
        # Optimization parameters
        self.optimization_inputs = OptimizationInputs()
        self.objective_weights = ObjectiveWeights()
        self.optimization_rankings: Dict[str, Decimal] = {}
        
        # Progress tracking
        self.current_objective_value: Decimal = Decimal('0')
        self.initial_objective_value: Decimal = Decimal('0')
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def setup_optimization(self, 
                          opt_inputs: OptimizationInputs,
                          obj_weights: ObjectiveWeights) -> None:
        """Setup optimization parameters and load data"""
        self.optimization_inputs = opt_inputs
        self.objective_weights = obj_weights
        
        # Initialize deal engine
        self.deal_engine = CLODealEngine(self.deal, self.session)
        
        # Load portfolios
        self._load_current_portfolio()
        self._load_potential_assets()
        self._load_hypothesis_portfolio()
        
        # Setup accounts and move ramp-up cash
        self._setup_accounts()
        
        self.logger.info("Portfolio optimization setup completed")
    
    def run_compliance_tests(self) -> List[ComplianceTestResult]:
        """
        Run compliance tests on current portfolio
        Converted from VBA RunCompliance()
        """
        self.logger.info("Running compliance tests")
        
        # Calculate compliance metrics
        compliance_results = self._calculate_compliance_tests()
        
        # Calculate objective value
        self.current_objective_value = self._calculate_objective_function(compliance_results)
        
        return compliance_results
    
    def run_portfolio_rankings(self) -> Dict[str, Decimal]:
        """
        Run asset rankings for portfolio optimization
        Converted from VBA RunRankings()
        """
        self.logger.info("Running portfolio rankings")
        
        # Generic optimization with rankings
        return self._generic_optimization_rankings(
            max_assets=self.optimization_inputs.max_assets,
            include_current_assets=self.optimization_inputs.include_current_assets,
            max_par_amount=self.optimization_inputs.max_par_amount,
            output_results=self.optimization_inputs.output_results
        )
    
    def run_generic_optimization(self) -> Decimal:
        """
        Run generic portfolio optimization algorithm
        Converted from VBA GenericOptimizationPool2343()
        """
        self.logger.info("Running generic portfolio optimization")
        
        # Get initial compliance results
        initial_results = self._calculate_compliance_tests()
        self.initial_objective_value = self._calculate_objective_function(initial_results)
        
        last_objective_value = self.initial_objective_value
        current_objective_value = last_objective_value + Decimal('0.00000000001')
        counter = 1
        
        # Optimization loop - continue while improving
        while (current_objective_value > last_objective_value and 
               self._get_available_cash() > 0):
            
            last_objective_value = current_objective_value
            
            # Determine par amount for this iteration
            available_cash = self._get_available_cash()
            par_amount = min(self.optimization_inputs.max_par_amount, available_cash)
            
            if par_amount <= 0:
                break
            
            # Run rankings to find best asset
            self.optimization_rankings = self._generic_optimization_rankings(
                max_assets=self.optimization_inputs.max_assets,
                include_current_assets=self.optimization_inputs.include_current_assets,
                max_par_amount=par_amount,
                output_results=False
            )
            
            # Sort rankings and get best asset
            sorted_rankings = sorted(
                self.optimization_rankings.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            if not sorted_rankings:
                break
                
            best_asset_id, current_objective_value = sorted_rankings[0]
            
            # If improvement found, add the asset
            if current_objective_value > last_objective_value:
                success = self._add_best_asset(best_asset_id, par_amount)
                if not success:
                    break
                    
                self.logger.info(
                    f"Added asset {best_asset_id} with par ${par_amount:,.2f}. "
                    f"Objective improved from {last_objective_value:.6f} to {current_objective_value:.6f}"
                )
                
                counter += 1
                
                # Reload potential assets for next iteration
                self._load_potential_assets()
            
        final_objective_value = last_objective_value if current_objective_value <= last_objective_value else current_objective_value
        
        self.logger.info(
            f"Optimization completed. Initial: {self.initial_objective_value:.6f}, "
            f"Final: {final_objective_value:.6f}, Assets added: {counter-1}"
        )
        
        return final_objective_value
    
    def run_scenario_analysis(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run multiple optimization scenarios
        """
        self.logger.info(f"Running scenario analysis with {len(scenarios)} scenarios")
        
        results = {}
        
        for i, scenario in enumerate(scenarios):
            self.logger.info(f"Running scenario {i+1}/{len(scenarios)}")
            
            # Apply scenario parameters
            scenario_inputs = OptimizationInputs(**scenario.get('inputs', {}))
            scenario_weights = ObjectiveWeights(**scenario.get('weights', {}))
            
            # Reset portfolio state
            self._reset_portfolio_state()
            
            # Setup with scenario parameters
            self.setup_optimization(scenario_inputs, scenario_weights)
            
            # Run optimization
            final_objective = self.run_generic_optimization()
            
            # Collect results
            results[f"scenario_{i+1}"] = {
                'inputs': scenario,
                'final_objective_value': float(final_objective),
                'initial_objective_value': float(self.initial_objective_value),
                'improvement': float(final_objective - self.initial_objective_value),
                'assets_in_portfolio': len(self.current_portfolio)
            }
        
        return results
    
    # Private helper methods
    
    def _calculate_objective_function(self, results: List[ComplianceTestResult]) -> Decimal:
        """
        Calculate objective function value
        Converted from VBA CalcObjectiveFunction()
        """
        objective_value = Decimal('0')
        
        for result in results:
            # If any critical test fails (except test 31), objective = 0
            if not result.pass_fail and result.test_number != 31:
                return Decimal('0')
            
            # Calculate weighted objective contribution
            test_weight = self.objective_weights.get_weight(result.test_number)
            
            if result.test_number in [33, 32, 37]:  # OC tests
                if result.threshold > 0:
                    contribution = (result.result / result.threshold) * test_weight
                    objective_value += contribution
                    
            elif result.test_number in [36, 35]:  # IC tests
                if result.result > 0:
                    contribution = (result.threshold / result.result) * test_weight
                    objective_value += contribution
        
        return objective_value * 100  # Scale by 100 as in VBA
    
    def _generic_optimization_rankings(self, 
                                     max_assets: int,
                                     include_current_assets: bool,
                                     max_par_amount: Decimal,
                                     output_results: bool) -> Dict[str, Decimal]:
        """
        Generic optimization with asset rankings
        Converted from VBA GenericOptimizationRankings()
        """
        rankings: Dict[str, Decimal] = {}
        counter = 0
        
        while counter < max_assets:
            # Get random asset for testing
            asset_id = self._get_random_asset(max_par_amount, include_current_assets)
            
            if not asset_id:
                break
                
            # Test this asset addition
            objective_value = self._test_asset_addition(asset_id, max_par_amount)
            
            if objective_value > 0:
                rankings[asset_id] = objective_value
            
            counter += 1
            
            if output_results and counter % 10 == 0:
                self.logger.info(f"Processed {counter}/{max_assets} assets for ranking")
        
        return rankings
    
    def _test_asset_addition(self, asset_id: str, par_amount: Decimal) -> Decimal:
        """Test adding an asset and return objective function improvement"""
        try:
            # Get asset from potential pool
            asset = self._get_potential_asset(asset_id)
            if not asset:
                return Decimal('0')
            
            # Check if asset already exists
            increase_par = Decimal('0')
            if self._asset_exists_in_portfolio(asset_id):
                # Increase existing asset
                current_par = self._get_asset_par_amount(asset_id)
                increase_par = min(par_amount, 
                                 self.optimization_inputs.max_loan_size - current_par)
                if increase_par <= 0:
                    return Decimal('0')
                
                self._increase_asset_par(asset_id, increase_par)
            else:
                # Add new asset
                asset_copy = self._create_asset_copy(asset)
                asset_copy.par_amount = par_amount
                self._add_asset_to_portfolio(asset_copy)
            
            # Remove cash from collection account
            self._remove_cash_from_collection(par_amount)
            
            # Calculate compliance and objective
            compliance_results = self._calculate_compliance_tests()
            objective_value = self._calculate_objective_function(compliance_results)
            
            # Restore portfolio state
            if increase_par > 0:
                self._decrease_asset_par(asset_id, increase_par)
            else:
                self._remove_asset_from_portfolio(asset_id)
            
            # Restore cash
            self._add_cash_to_collection(par_amount)
            
            return objective_value
            
        except Exception as e:
            self.logger.error(f"Error testing asset {asset_id}: {e}")
            return Decimal('0')
    
    def _calculate_compliance_tests(self) -> List[ComplianceTestResult]:
        """Calculate all compliance test results"""
        # This would integrate with actual compliance testing system
        # For now, return mock results
        
        results = []
        
        # OC Tests
        for test_num in [32, 33, 37]:
            result = ComplianceTestResult(
                test_number=test_num,
                test_name=f"OC Test {test_num}",
                comments=f"Overcollateralization Test {test_num}",
                numerator=Decimal('120.5'),
                denominator=Decimal('100.0'),
                result=Decimal('1.205'),
                threshold=Decimal('1.10'),
                pass_fail=True,
                pass_fail_comment="PASS"
            )
            results.append(result)
        
        # IC Tests
        for test_num in [35, 36]:
            result = ComplianceTestResult(
                test_number=test_num,
                test_name=f"IC Test {test_num}",
                comments=f"Interest Coverage Test {test_num}",
                numerator=Decimal('115.2'),
                denominator=Decimal('100.0'),
                result=Decimal('1.152'),
                threshold=Decimal('1.05'),
                pass_fail=True,
                pass_fail_comment="PASS"
            )
            results.append(result)
        
        return results
    
    def _load_current_portfolio(self) -> None:
        """Load existing collateral pool"""
        # Load current portfolio assets from database
        assets = self.session.query(Asset).filter(
            Asset.deal_id == self.deal.deal_id,
            Asset.is_current_holding == True
        ).all()
        
        self.current_portfolio = assets
        self.logger.info(f"Loaded {len(assets)} assets in current portfolio")
    
    def _load_potential_assets(self) -> None:
        """Load potential assets for optimization"""
        # Load potential assets from database
        assets = self.session.query(Asset).filter(
            Asset.deal_id == self.deal.deal_id,
            Asset.is_potential_holding == True
        ).all()
        
        self.potential_assets = assets
        self.logger.info(f"Loaded {len(assets)} potential assets")
    
    def _load_hypothesis_portfolio(self) -> None:
        """Load hypothesis portfolio assets"""
        # Load hypothesis assets from database  
        assets = self.session.query(Asset).filter(
            Asset.deal_id == self.deal.deal_id,
            Asset.is_hypothesis_holding == True
        ).all()
        
        self.hypothesis_portfolio = assets
        self.logger.info(f"Loaded {len(assets)} hypothesis assets")
    
    def _setup_accounts(self) -> None:
        """Setup cash accounts and move ramp-up cash"""
        if not self.deal_engine:
            return
            
        # Move ramp-up cash to collection account
        ramp_up_cash = self.deal_engine.accounts[AccountType.RAMP_UP].principal_proceeds
        
        if ramp_up_cash > 0:
            self.deal_engine.accounts[AccountType.RAMP_UP].add(CashType.PRINCIPAL, -ramp_up_cash)
            self.deal_engine.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, ramp_up_cash)
            
            self.logger.info(f"Moved ${ramp_up_cash:,.2f} from ramp-up to collection account")
    
    def _get_available_cash(self) -> Decimal:
        """Get available cash in collection account"""
        if not self.deal_engine:
            return Decimal('0')
        return self.deal_engine.accounts[AccountType.COLLECTION].principal_proceeds
    
    def _get_random_asset(self, max_par_amount: Decimal, include_current: bool) -> Optional[str]:
        """Get random asset ID for testing"""
        import random
        
        available_assets = []
        
        # Add potential assets
        for asset in self.potential_assets:
            if not self._asset_exists_in_portfolio(asset.blk_rock_id):
                available_assets.append(asset.blk_rock_id)
        
        # Add current assets if including current
        if include_current:
            for asset in self.current_portfolio:
                current_par = asset.par_amount or Decimal('0')
                if current_par < self.optimization_inputs.max_loan_size:
                    available_assets.append(asset.blk_rock_id)
        
        return random.choice(available_assets) if available_assets else None
    
    def _get_potential_asset(self, asset_id: str) -> Optional[Asset]:
        """Get asset from potential pool"""
        for asset in self.potential_assets:
            if asset.blk_rock_id == asset_id:
                return asset
        return None
    
    def _asset_exists_in_portfolio(self, asset_id: str) -> bool:
        """Check if asset exists in current portfolio"""
        return any(asset.blk_rock_id == asset_id for asset in self.current_portfolio)
    
    def _get_asset_par_amount(self, asset_id: str) -> Decimal:
        """Get current par amount for asset"""
        for asset in self.current_portfolio:
            if asset.blk_rock_id == asset_id:
                return asset.par_amount or Decimal('0')
        return Decimal('0')
    
    def _increase_asset_par(self, asset_id: str, amount: Decimal) -> None:
        """Increase par amount for existing asset"""
        for asset in self.current_portfolio:
            if asset.blk_rock_id == asset_id:
                asset.par_amount = (asset.par_amount or Decimal('0')) + amount
                break
    
    def _decrease_asset_par(self, asset_id: str, amount: Decimal) -> None:
        """Decrease par amount for existing asset"""
        for asset in self.current_portfolio:
            if asset.blk_rock_id == asset_id:
                asset.par_amount = (asset.par_amount or Decimal('0')) - amount
                break
    
    def _create_asset_copy(self, asset: Asset) -> Asset:
        """Create a copy of an asset for testing"""
        # Create a copy of the asset with same properties
        asset_copy = Asset(
            deal_id=asset.deal_id,
            blk_rock_id=asset.blk_rock_id,
            issue_name=asset.issue_name,
            issuer_name=asset.issuer_name,
            # ... copy all other properties
        )
        return asset_copy
    
    def _add_asset_to_portfolio(self, asset: Asset) -> None:
        """Add asset to current portfolio"""
        self.current_portfolio.append(asset)
    
    def _remove_asset_from_portfolio(self, asset_id: str) -> None:
        """Remove asset from current portfolio"""
        self.current_portfolio = [
            asset for asset in self.current_portfolio 
            if asset.blk_rock_id != asset_id
        ]
    
    def _remove_cash_from_collection(self, amount: Decimal) -> None:
        """Remove cash from collection account"""
        if self.deal_engine:
            self.deal_engine.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, -amount)
    
    def _add_cash_to_collection(self, amount: Decimal) -> None:
        """Add cash to collection account"""
        if self.deal_engine:
            self.deal_engine.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, amount)
    
    def _add_best_asset(self, asset_id: str, par_amount: Decimal) -> bool:
        """Add the best ranked asset to portfolio"""
        try:
            asset = self._get_potential_asset(asset_id)
            if not asset:
                return False
            
            if self._asset_exists_in_portfolio(asset_id):
                # Increase existing asset
                self._increase_asset_par(asset_id, par_amount)
            else:
                # Add new asset
                asset_copy = self._create_asset_copy(asset)
                asset_copy.par_amount = par_amount
                self._add_asset_to_portfolio(asset_copy)
            
            # Remove cash
            self._remove_cash_from_collection(par_amount)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding best asset {asset_id}: {e}")
            return False
    
    def _reset_portfolio_state(self) -> None:
        """Reset portfolio to initial state"""
        self.current_portfolio = []
        self.potential_assets = []
        self.hypothesis_portfolio = []
        self.optimization_rankings = {}
        self.current_objective_value = Decimal('0')
        self.initial_objective_value = Decimal('0')


class PortfolioOptimizationService:
    """
    Service layer for portfolio optimization operations
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def run_portfolio_optimization(self, 
                                       deal_id: str,
                                       optimization_inputs: OptimizationInputs,
                                       objective_weights: ObjectiveWeights) -> Dict[str, Any]:
        """Run portfolio optimization for a deal"""
        
        # Get deal
        deal = self.session.query(CLODeal).filter(CLODeal.deal_id == deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Create optimization engine
        engine = PortfolioOptimizationEngine(deal, self.session)
        
        # Setup optimization
        engine.setup_optimization(optimization_inputs, objective_weights)
        
        # Run optimization
        initial_compliance = engine.run_compliance_tests()
        final_objective = engine.run_generic_optimization()
        final_compliance = engine.run_compliance_tests()
        
        # Return results
        return {
            'deal_id': deal_id,
            'optimization_type': 'generic_optimization',
            'initial_objective_value': float(engine.initial_objective_value),
            'final_objective_value': float(final_objective),
            'improvement': float(final_objective - engine.initial_objective_value),
            'initial_compliance': [self._compliance_result_to_dict(r) for r in initial_compliance],
            'final_compliance': [self._compliance_result_to_dict(r) for r in final_compliance],
            'assets_in_portfolio': len(engine.current_portfolio),
            'available_cash_remaining': float(engine._get_available_cash())
        }
    
    async def run_scenario_analysis(self,
                                  deal_id: str,
                                  scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run multiple optimization scenarios"""
        
        # Get deal
        deal = self.session.query(CLODeal).filter(CLODeal.deal_id == deal_id).first()
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Create optimization engine
        engine = PortfolioOptimizationEngine(deal, self.session)
        
        # Run scenario analysis
        results = engine.run_scenario_analysis(scenarios)
        
        return {
            'deal_id': deal_id,
            'analysis_type': 'scenario_analysis',
            'scenarios_count': len(scenarios),
            'results': results
        }
    
    def _compliance_result_to_dict(self, result: ComplianceTestResult) -> Dict[str, Any]:
        """Convert compliance result to dictionary"""
        return {
            'test_number': result.test_number,
            'test_name': result.test_name,
            'result': float(result.result),
            'threshold': float(result.threshold),
            'pass_fail': result.pass_fail,
            'numerator': float(result.numerator),
            'denominator': float(result.denominator)
        }