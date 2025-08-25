"""
Portfolio Analytics Schemas
Pydantic models for advanced portfolio analytics API requests and responses
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


class OptimizationType(str, Enum):
    """Portfolio optimization type"""
    RISK_MINIMIZATION = "risk_minimization"
    RETURN_MAXIMIZATION = "return_maximization"
    SHARPE_RATIO = "sharpe_ratio"
    COMPLIANCE_OPTIMIZATION = "compliance_optimization"
    CUSTOM = "custom"


class AnalysisPeriod(str, Enum):
    """Analysis time period"""
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"
    FULL_PERIOD = "FULL"
    CUSTOM = "CUSTOM"


class BenchmarkType(str, Enum):
    """Benchmark comparison type"""
    CLO_INDEX = "clo_index"
    HIGH_YIELD = "high_yield"
    INVESTMENT_GRADE = "investment_grade"
    LEVERAGED_LOANS = "leveraged_loans"
    CUSTOM = "custom"


class PortfolioOptimizationRequest(BaseModel):
    """Schema for portfolio optimization requests"""
    portfolio_id: Optional[str] = None
    optimization_type: OptimizationType = OptimizationType.RISK_MINIMIZATION
    constraints: Dict[str, Any] = Field(default_factory=dict)
    
    # Risk parameters
    target_volatility: Optional[Decimal] = None
    max_risk: Optional[Decimal] = None
    risk_free_rate: Decimal = Field(default=Decimal("0.02"))
    
    # Concentration limits
    max_single_asset_weight: Decimal = Field(default=Decimal("0.05"))
    sector_limits: Optional[Dict[str, Decimal]] = None
    rating_limits: Optional[Dict[str, Decimal]] = None
    
    # Scenario analysis
    include_stress_testing: bool = True
    monte_carlo_runs: int = Field(default=1000, ge=100, le=10000)
    
    # Time horizon
    optimization_horizon: int = Field(default=12, description="Months")


class PortfolioOptimizationResult(BaseModel):
    """Schema for portfolio optimization results"""
    portfolio_id: Optional[str] = None
    optimization_date: datetime
    optimization_type: OptimizationType
    
    # Optimization results
    success: bool
    iterations: int
    convergence_achieved: bool
    
    # Current vs optimized metrics
    current_metrics: Dict[str, Decimal]
    optimized_metrics: Dict[str, Decimal]
    improvement_summary: Dict[str, Decimal]
    
    # Recommended trades
    recommended_sales: List[Dict[str, Any]]
    recommended_purchases: List[Dict[str, Any]]
    trade_impact: Dict[str, Decimal]
    
    # Risk analysis
    current_risk_metrics: Dict[str, Decimal]
    optimized_risk_metrics: Dict[str, Decimal]
    
    # Constraints validation
    constraint_violations: List[str]
    constraint_adherence: Dict[str, bool]


class PortfolioPerformanceAnalysisRequest(BaseModel):
    """Schema for portfolio performance analysis requests"""
    portfolio_id: Optional[str] = None
    analysis_period: AnalysisPeriod = AnalysisPeriod.ONE_YEAR
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Benchmark comparison
    benchmark_type: Optional[BenchmarkType] = None
    custom_benchmark_returns: Optional[List[Decimal]] = None
    
    # Analysis options
    include_attribution: bool = True
    include_risk_decomposition: bool = True
    include_sector_analysis: bool = True
    include_rating_migration: bool = True


class PortfolioPerformanceResult(BaseModel):
    """Schema for portfolio performance analysis results"""
    portfolio_id: Optional[str] = None
    analysis_date: datetime
    analysis_period: str
    start_date: date
    end_date: date
    
    # Return metrics
    total_return: Decimal
    annualized_return: Decimal
    cumulative_return: Decimal
    period_returns: List[Dict[str, Any]]
    
    # Risk metrics
    volatility: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal
    var_95: Decimal
    var_99: Decimal
    
    # Benchmark comparison
    benchmark_return: Optional[Decimal] = None
    excess_return: Optional[Decimal] = None
    tracking_error: Optional[Decimal] = None
    information_ratio: Optional[Decimal] = None
    
    # Attribution analysis
    sector_attribution: Optional[Dict[str, Decimal]] = None
    security_attribution: Optional[Dict[str, Decimal]] = None
    style_attribution: Optional[Dict[str, Decimal]] = None


class PortfolioRiskAnalysisRequest(BaseModel):
    """Schema for portfolio risk analysis requests"""
    portfolio_id: Optional[str] = None
    confidence_levels: List[float] = Field(default=[0.95, 0.99])
    time_horizons: List[int] = Field(default=[1, 5, 10], description="Days")
    
    # Stress testing
    stress_scenarios: List[str] = Field(default_factory=list)
    custom_shocks: Optional[Dict[str, Decimal]] = None
    
    # Correlation analysis
    include_correlation_breakdown: bool = True
    correlation_threshold: float = Field(default=0.8)


class PortfolioRiskAnalysisResult(BaseModel):
    """Schema for portfolio risk analysis results"""
    portfolio_id: Optional[str] = None
    analysis_date: datetime
    
    # VaR analysis
    var_results: Dict[str, Dict[str, Decimal]]  # confidence_level -> time_horizon -> value
    expected_shortfall: Dict[str, Dict[str, Decimal]]
    
    # Stress test results
    stress_test_results: Dict[str, Decimal]
    worst_case_scenario: str
    worst_case_loss: Decimal
    
    # Risk decomposition
    sector_risk_contribution: Dict[str, Decimal]
    asset_risk_contribution: Dict[str, Decimal]
    marginal_var: Dict[str, Decimal]
    
    # Correlation analysis
    high_correlation_pairs: List[Dict[str, Any]]
    correlation_clusters: List[List[str]]
    diversification_ratio: Decimal


class ConcentrationAnalysisRequest(BaseModel):
    """Schema for concentration analysis requests"""
    portfolio_id: Optional[str] = None
    analysis_dimensions: List[str] = Field(
        default=["sector", "industry", "rating", "geography", "issuer"],
        description="Dimensions to analyze concentration"
    )
    
    # Concentration limits
    single_asset_limit: float = Field(default=0.05)
    sector_limit: float = Field(default=0.25)
    rating_limits: Optional[Dict[str, float]] = None
    
    # Herfindahl-Hirschman Index
    calculate_hhi: bool = True
    hhi_thresholds: Dict[str, float] = Field(
        default={"low": 0.15, "moderate": 0.25, "high": 0.35}
    )


class ConcentrationAnalysisResult(BaseModel):
    """Schema for concentration analysis results"""
    portfolio_id: Optional[str] = None
    analysis_date: datetime
    
    # Concentration metrics by dimension
    concentration_metrics: Dict[str, Dict[str, Any]]  # dimension -> metrics
    
    # HHI analysis
    herfindahl_indices: Dict[str, float]
    concentration_levels: Dict[str, str]  # dimension -> level (low/moderate/high)
    
    # Limit breaches
    limit_violations: List[Dict[str, Any]]
    concentration_warnings: List[str]
    
    # Diversification recommendations
    diversification_opportunities: List[Dict[str, Any]]
    recommended_adjustments: List[Dict[str, Any]]


class PortfolioScenarioAnalysisRequest(BaseModel):
    """Schema for portfolio scenario analysis requests"""
    portfolio_id: Optional[str] = None
    scenarios: List[str] = Field(default_factory=list)
    custom_scenarios: Optional[List[Dict[str, Any]]] = None
    
    # Analysis parameters
    time_horizon: int = Field(default=12, description="Months")
    confidence_level: float = Field(default=0.95)
    
    # Monte Carlo parameters
    simulation_runs: int = Field(default=1000)
    include_path_dependency: bool = True


class PortfolioScenarioAnalysisResult(BaseModel):
    """Schema for portfolio scenario analysis results"""
    portfolio_id: Optional[str] = None
    analysis_date: datetime
    scenarios_analyzed: List[str]
    
    # Scenario results
    scenario_outcomes: Dict[str, Dict[str, Any]]  # scenario -> metrics
    
    # Statistical analysis
    mean_outcome: Decimal
    median_outcome: Decimal
    std_deviation: Decimal
    skewness: Decimal
    kurtosis: Decimal
    
    # Risk metrics
    scenario_var: Decimal
    tail_risk: Decimal
    probability_of_loss: Decimal
    
    # Best/worst case analysis
    best_case_scenario: str
    worst_case_scenario: str
    most_likely_outcome: Dict[str, Any]


class PortfolioComparisonRequest(BaseModel):
    """Schema for portfolio comparison requests"""
    portfolio_ids: List[str] = Field(..., min_items=2, max_items=10)
    comparison_metrics: List[str] = Field(
        default=["return", "volatility", "sharpe_ratio", "max_drawdown", "var"],
        description="Metrics to compare"
    )
    
    # Analysis parameters
    analysis_period: AnalysisPeriod = AnalysisPeriod.ONE_YEAR
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Benchmark
    benchmark_type: Optional[BenchmarkType] = None


class PortfolioComparisonResult(BaseModel):
    """Schema for portfolio comparison results"""
    comparison_date: datetime
    portfolios_analyzed: List[str]
    analysis_period: str
    
    # Comparison matrix
    metric_comparisons: Dict[str, Dict[str, Any]]  # metric -> portfolio -> value
    relative_rankings: Dict[str, List[str]]  # metric -> ranked portfolio IDs
    
    # Statistical tests
    significance_tests: Dict[str, Dict[str, Any]]
    correlation_matrix: Dict[str, Dict[str, float]]
    
    # Performance summary
    best_performer: Dict[str, str]  # metric -> portfolio_id
    worst_performer: Dict[str, str]  # metric -> portfolio_id
    overall_ranking: List[str]  # portfolio IDs ranked by composite score


class PortfolioAnalyticsStatsResponse(BaseModel):
    """Schema for portfolio analytics statistics"""
    total_portfolios_analyzed: int
    analysis_types_performed: Dict[str, int]
    average_analysis_time: Dict[str, float]  # analysis_type -> seconds
    
    # Usage patterns
    most_requested_analytics: List[Dict[str, Any]]
    recent_analyses: List[Dict[str, Any]]
    
    # System performance
    success_rate: Dict[str, float]  # analysis_type -> success_rate
    error_summary: Dict[str, int]  # error_type -> count