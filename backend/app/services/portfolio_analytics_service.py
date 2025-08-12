"""
Portfolio Analytics Service
Advanced portfolio analysis, optimization, and performance measurement
"""

import logging
import uuid
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from ..core.database_config import get_db_session
from ..core.exceptions import CLOBusinessError, CLOValidationError
from ..models.clo_deal import CLODeal
from ..models.asset import Asset
from ..models.portfolio_optimization import PortfolioOptimizationEngine
from ..schemas.portfolio_analytics import (
    PortfolioOptimizationRequest, PortfolioOptimizationResult,
    PortfolioPerformanceAnalysisRequest, PortfolioPerformanceResult,
    PortfolioRiskAnalysisRequest, PortfolioRiskAnalysisResult,
    ConcentrationAnalysisRequest, ConcentrationAnalysisResult,
    PortfolioScenarioAnalysisRequest, PortfolioScenarioAnalysisResult,
    PortfolioComparisonRequest, PortfolioComparisonResult,
    OptimizationType, AnalysisPeriod, BenchmarkType
)
from ..utils.math_utils import MathUtils
from ..utils.financial_utils import FinancialUtils

logger = logging.getLogger(__name__)


class PortfolioAnalyticsService:
    """Service for advanced portfolio analytics operations"""
    
    def __init__(self):
        self.math_utils = MathUtils()
        self.financial_utils = FinancialUtils()
    
    def optimize_portfolio(
        self, 
        request: PortfolioOptimizationRequest, 
        user_id: str
    ) -> PortfolioOptimizationResult:
        """
        Perform portfolio optimization based on specified criteria
        """
        try:
            with get_db_session() as session:
                # Get portfolio data
                portfolio = self._get_portfolio(session, request.portfolio_id)
                assets = self._get_portfolio_assets(session, request.portfolio_id)
                
                if not assets:
                    raise CLOValidationError(f"No assets found for portfolio: {request.portfolio_id}")
                
                # Current portfolio metrics
                current_metrics = self._calculate_portfolio_metrics(assets)
                
                # Setup optimization engine
                optimization_engine = PortfolioOptimizationEngine()
                
                # Configure optimization parameters
                optimization_params = {
                    "optimization_type": request.optimization_type.value,
                    "target_volatility": float(request.target_volatility) if request.target_volatility else None,
                    "max_risk": float(request.max_risk) if request.max_risk else None,
                    "risk_free_rate": float(request.risk_free_rate),
                    "constraints": request.constraints,
                    "concentration_limits": {
                        "max_single_asset": float(request.max_single_asset_weight),
                        "sector_limits": {k: float(v) for k, v in (request.sector_limits or {}).items()},
                        "rating_limits": {k: float(v) for k, v in (request.rating_limits or {}).items()}
                    }
                }
                
                # Run optimization
                optimization_result = optimization_engine.optimize(
                    assets=assets,
                    parameters=optimization_params
                )
                
                # Calculate optimized metrics
                optimized_assets = optimization_result.get("optimized_assets", assets)
                optimized_metrics = self._calculate_portfolio_metrics(optimized_assets)
                
                # Generate recommendations
                recommendations = self._generate_trade_recommendations(
                    current_assets=assets,
                    optimized_assets=optimized_assets,
                    optimization_result=optimization_result
                )
                
                # Stress testing if requested
                risk_metrics = {}
                if request.include_stress_testing:
                    risk_metrics = self._perform_stress_testing(
                        assets=optimized_assets,
                        monte_carlo_runs=request.monte_carlo_runs
                    )
                
                # Build result
                result = PortfolioOptimizationResult(
                    portfolio_id=request.portfolio_id,
                    optimization_date=datetime.utcnow(),
                    optimization_type=request.optimization_type,
                    success=optimization_result.get("success", True),
                    iterations=optimization_result.get("iterations", 0),
                    convergence_achieved=optimization_result.get("converged", True),
                    current_metrics=current_metrics,
                    optimized_metrics=optimized_metrics,
                    improvement_summary=self._calculate_improvements(current_metrics, optimized_metrics),
                    recommended_sales=recommendations.get("sales", []),
                    recommended_purchases=recommendations.get("purchases", []),
                    trade_impact=recommendations.get("impact", {}),
                    current_risk_metrics=current_metrics,
                    optimized_risk_metrics=optimized_metrics,
                    constraint_violations=optimization_result.get("violations", []),
                    constraint_adherence=optimization_result.get("constraint_adherence", {})
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}")
            raise CLOBusinessError(f"Portfolio optimization failed: {str(e)}") from e
    
    def analyze_portfolio_performance(
        self, 
        request: PortfolioPerformanceAnalysisRequest, 
        user_id: str
    ) -> PortfolioPerformanceResult:
        """
        Analyze portfolio performance over specified period
        """
        try:
            with get_db_session() as session:
                # Get portfolio and historical data
                portfolio = self._get_portfolio(session, request.portfolio_id)
                
                # Determine analysis period
                end_date = request.end_date or date.today()
                if request.start_date:
                    start_date = request.start_date
                else:
                    start_date = self._calculate_start_date(request.analysis_period, end_date)
                
                # Get historical performance data
                performance_data = self._get_historical_performance(
                    session, request.portfolio_id, start_date, end_date
                )
                
                # Calculate return metrics
                returns = self._calculate_returns(performance_data)
                return_metrics = {
                    "total_return": returns.get("total_return", Decimal("0")),
                    "annualized_return": returns.get("annualized_return", Decimal("0")),
                    "cumulative_return": returns.get("cumulative_return", Decimal("0"))
                }
                
                # Calculate risk metrics
                risk_metrics = self._calculate_risk_metrics(performance_data)
                
                # Benchmark analysis
                benchmark_metrics = {}
                if request.benchmark_type:
                    benchmark_data = self._get_benchmark_data(
                        request.benchmark_type, start_date, end_date
                    )
                    benchmark_metrics = self._calculate_benchmark_comparison(
                        performance_data, benchmark_data
                    )
                
                # Attribution analysis
                attribution_results = {}
                if request.include_attribution:
                    attribution_results = self._perform_attribution_analysis(
                        session, request.portfolio_id, start_date, end_date
                    )
                
                result = PortfolioPerformanceResult(
                    portfolio_id=request.portfolio_id,
                    analysis_date=datetime.utcnow(),
                    analysis_period=request.analysis_period.value,
                    start_date=start_date,
                    end_date=end_date,
                    total_return=return_metrics["total_return"],
                    annualized_return=return_metrics["annualized_return"],
                    cumulative_return=return_metrics["cumulative_return"],
                    period_returns=performance_data,
                    volatility=risk_metrics.get("volatility", Decimal("0")),
                    sharpe_ratio=risk_metrics.get("sharpe_ratio"),
                    max_drawdown=risk_metrics.get("max_drawdown", Decimal("0")),
                    var_95=risk_metrics.get("var_95", Decimal("0")),
                    var_99=risk_metrics.get("var_99", Decimal("0")),
                    benchmark_return=benchmark_metrics.get("benchmark_return"),
                    excess_return=benchmark_metrics.get("excess_return"),
                    tracking_error=benchmark_metrics.get("tracking_error"),
                    information_ratio=benchmark_metrics.get("information_ratio"),
                    sector_attribution=attribution_results.get("sector_attribution"),
                    security_attribution=attribution_results.get("security_attribution"),
                    style_attribution=attribution_results.get("style_attribution")
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            raise CLOBusinessError(f"Performance analysis failed: {str(e)}") from e
    
    def analyze_portfolio_risk(
        self, 
        request: PortfolioRiskAnalysisRequest, 
        user_id: str
    ) -> PortfolioRiskAnalysisResult:
        """
        Comprehensive portfolio risk analysis including VaR and stress testing
        """
        try:
            with get_db_session() as session:
                # Get portfolio assets
                portfolio = self._get_portfolio(session, request.portfolio_id)
                assets = self._get_portfolio_assets(session, request.portfolio_id)
                
                # VaR analysis
                var_results = {}
                expected_shortfall = {}
                
                for confidence_level in request.confidence_levels:
                    var_results[str(confidence_level)] = {}
                    expected_shortfall[str(confidence_level)] = {}
                    
                    for time_horizon in request.time_horizons:
                        var_calc = self._calculate_var(
                            assets, confidence_level, time_horizon
                        )
                        var_results[str(confidence_level)][str(time_horizon)] = var_calc["var"]
                        expected_shortfall[str(confidence_level)][str(time_horizon)] = var_calc["es"]
                
                # Stress testing
                stress_results = {}
                worst_case_scenario = None
                worst_case_loss = Decimal("0")
                
                for scenario in request.stress_scenarios:
                    stress_result = self._perform_stress_test(assets, scenario)
                    stress_results[scenario] = stress_result["loss"]
                    
                    if stress_result["loss"] > worst_case_loss:
                        worst_case_loss = stress_result["loss"]
                        worst_case_scenario = scenario
                
                # Risk decomposition
                risk_decomposition = self._calculate_risk_decomposition(assets)
                
                # Correlation analysis
                correlation_analysis = {}
                if request.include_correlation_breakdown:
                    correlation_analysis = self._analyze_correlations(
                        assets, request.correlation_threshold
                    )
                
                result = PortfolioRiskAnalysisResult(
                    portfolio_id=request.portfolio_id,
                    analysis_date=datetime.utcnow(),
                    var_results=var_results,
                    expected_shortfall=expected_shortfall,
                    stress_test_results=stress_results,
                    worst_case_scenario=worst_case_scenario or "None",
                    worst_case_loss=worst_case_loss,
                    sector_risk_contribution=risk_decomposition.get("sector", {}),
                    asset_risk_contribution=risk_decomposition.get("asset", {}),
                    marginal_var=risk_decomposition.get("marginal_var", {}),
                    high_correlation_pairs=correlation_analysis.get("high_correlation_pairs", []),
                    correlation_clusters=correlation_analysis.get("clusters", []),
                    diversification_ratio=correlation_analysis.get("diversification_ratio", Decimal("1.0"))
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Risk analysis failed: {str(e)}")
            raise CLOBusinessError(f"Risk analysis failed: {str(e)}") from e
    
    def analyze_concentration(
        self, 
        request: ConcentrationAnalysisRequest, 
        user_id: str
    ) -> ConcentrationAnalysisResult:
        """
        Analyze portfolio concentration across various dimensions
        """
        try:
            with get_db_session() as session:
                # Get portfolio assets
                assets = self._get_portfolio_assets(session, request.portfolio_id)
                
                if not assets:
                    raise CLOValidationError(f"No assets found for portfolio: {request.portfolio_id}")
                
                # Analyze concentration by each dimension
                concentration_metrics = {}
                herfindahl_indices = {}
                concentration_levels = {}
                limit_violations = []
                
                for dimension in request.analysis_dimensions:
                    # Calculate concentration metrics for this dimension
                    dimension_analysis = self._analyze_dimension_concentration(
                        assets, dimension, request
                    )
                    
                    concentration_metrics[dimension] = dimension_analysis["metrics"]
                    
                    if request.calculate_hhi:
                        hhi = self._calculate_herfindahl_index(assets, dimension)
                        herfindahl_indices[dimension] = hhi
                        concentration_levels[dimension] = self._classify_concentration_level(
                            hhi, request.hhi_thresholds
                        )
                    
                    # Check for limit violations
                    violations = self._check_concentration_limits(
                        dimension_analysis["metrics"], dimension, request
                    )
                    limit_violations.extend(violations)
                
                # Generate recommendations
                diversification_opportunities = self._identify_diversification_opportunities(
                    assets, concentration_metrics
                )
                
                recommended_adjustments = self._recommend_concentration_adjustments(
                    assets, limit_violations, concentration_metrics
                )
                
                result = ConcentrationAnalysisResult(
                    portfolio_id=request.portfolio_id,
                    analysis_date=datetime.utcnow(),
                    concentration_metrics=concentration_metrics,
                    herfindahl_indices=herfindahl_indices,
                    concentration_levels=concentration_levels,
                    limit_violations=limit_violations,
                    concentration_warnings=self._generate_concentration_warnings(limit_violations),
                    diversification_opportunities=diversification_opportunities,
                    recommended_adjustments=recommended_adjustments
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Concentration analysis failed: {str(e)}")
            raise CLOBusinessError(f"Concentration analysis failed: {str(e)}") from e
    
    # Helper methods
    def _get_portfolio(self, session: Session, portfolio_id: str) -> CLODeal:
        """Get portfolio from database"""
        portfolio = session.query(CLODeal).filter(
            CLODeal.deal_id == portfolio_id
        ).first()
        
        if not portfolio:
            raise CLOValidationError(f"Portfolio not found: {portfolio_id}")
        
        return portfolio
    
    def _get_portfolio_assets(self, session: Session, portfolio_id: str) -> List[Asset]:
        """Get assets for a portfolio"""
        # This would join with the deal-asset relationship table
        # For now, return a mock list
        return []
    
    def _calculate_portfolio_metrics(self, assets: List[Asset]) -> Dict[str, Decimal]:
        """Calculate basic portfolio metrics"""
        if not assets:
            return {
                "total_value": Decimal("0"),
                "asset_count": 0,
                "weighted_avg_rating": Decimal("0"),
                "duration": Decimal("0"),
                "yield": Decimal("0")
            }
        
        # Mock calculation - in real implementation would use asset data
        return {
            "total_value": Decimal("1000000"),
            "asset_count": len(assets),
            "weighted_avg_rating": Decimal("7.5"),
            "duration": Decimal("3.2"),
            "yield": Decimal("0.065")
        }
    
    def _calculate_improvements(
        self, 
        current: Dict[str, Decimal], 
        optimized: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Calculate improvement metrics"""
        improvements = {}
        for metric in current.keys():
            if metric in optimized:
                try:
                    if current[metric] != 0:
                        improvement = (optimized[metric] - current[metric]) / current[metric]
                    else:
                        improvement = optimized[metric]
                    improvements[f"{metric}_improvement"] = improvement
                except:
                    improvements[f"{metric}_improvement"] = Decimal("0")
        return improvements
    
    def _generate_trade_recommendations(
        self, 
        current_assets: List[Asset], 
        optimized_assets: List[Asset],
        optimization_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trade recommendations based on optimization"""
        # Mock implementation
        return {
            "sales": [],
            "purchases": [],
            "impact": {
                "estimated_cost": Decimal("5000"),
                "expected_improvement": Decimal("0.15")
            }
        }
    
    def _perform_stress_testing(
        self, 
        assets: List[Asset], 
        monte_carlo_runs: int
    ) -> Dict[str, Decimal]:
        """Perform stress testing analysis"""
        # Mock implementation
        return {
            "var_95": Decimal("0.05"),
            "var_99": Decimal("0.08"),
            "expected_shortfall": Decimal("0.12"),
            "stress_scenarios": {
                "credit_crisis": Decimal("0.18"),
                "interest_rate_shock": Decimal("0.12"),
                "liquidity_crisis": Decimal("0.25")
            }
        }
    
    def _calculate_start_date(self, period: AnalysisPeriod, end_date: date) -> date:
        """Calculate start date based on analysis period"""
        if period == AnalysisPeriod.ONE_MONTH:
            return end_date - timedelta(days=30)
        elif period == AnalysisPeriod.THREE_MONTHS:
            return end_date - timedelta(days=90)
        elif period == AnalysisPeriod.SIX_MONTHS:
            return end_date - timedelta(days=180)
        elif period == AnalysisPeriod.ONE_YEAR:
            return end_date - timedelta(days=365)
        elif period == AnalysisPeriod.TWO_YEARS:
            return end_date - timedelta(days=730)
        else:
            return end_date - timedelta(days=365)  # Default to 1 year
    
    def _get_historical_performance(
        self, 
        session: Session, 
        portfolio_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get historical performance data"""
        # Mock implementation - would query actual historical data
        return [
            {"date": "2024-01-01", "return": 0.012, "value": 1000000},
            {"date": "2024-02-01", "return": 0.008, "value": 1008000},
            {"date": "2024-03-01", "return": -0.005, "value": 1003000}
        ]
    
    def _calculate_returns(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Calculate various return metrics"""
        # Mock implementation
        return {
            "total_return": Decimal("0.15"),
            "annualized_return": Decimal("0.12"),
            "cumulative_return": Decimal("0.15")
        }
    
    def _calculate_risk_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Calculate risk metrics from performance data"""
        # Mock implementation
        return {
            "volatility": Decimal("0.08"),
            "sharpe_ratio": Decimal("1.5"),
            "max_drawdown": Decimal("0.05"),
            "var_95": Decimal("0.03"),
            "var_99": Decimal("0.06")
        }