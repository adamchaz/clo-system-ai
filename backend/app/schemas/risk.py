"""
Risk Analytics Schemas
Pydantic models for risk analysis-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskMetricsResponse(BaseModel):
    """Schema for comprehensive risk metrics"""
    deal_id: str
    as_of_date: date
    calculation_timestamp: datetime
    
    # Volatility metrics
    portfolio_volatility: Decimal = Field(..., description="Annualized portfolio volatility")
    tracking_error: Optional[Decimal] = None
    
    # Concentration metrics
    sector_concentration: Dict[str, Decimal]
    rating_concentration: Dict[str, Decimal]
    single_asset_max_weight: Decimal
    herfindahl_index: Decimal
    
    # Risk measures
    value_at_risk_95: Decimal
    value_at_risk_99: Decimal
    expected_shortfall: Decimal
    maximum_drawdown: Optional[Decimal] = None
    
    # Duration and sensitivity
    modified_duration: Optional[Decimal] = None
    effective_duration: Optional[Decimal] = None
    convexity: Optional[Decimal] = None
    
    # Credit risk metrics
    average_rating_score: Decimal
    weighted_average_rating: str
    default_probability: Optional[Decimal] = None
    
    # Market risk factors
    interest_rate_sensitivity: Optional[Decimal] = None
    credit_spread_sensitivity: Optional[Decimal] = None
    
    # Risk level assessment
    overall_risk_level: RiskLevel
    risk_factors: List[str] = Field(default_factory=list)

class CorrelationMatrixResponse(BaseModel):
    """Schema for correlation matrix analysis"""
    deal_id: str
    asset_count: int
    correlation_matrix: List[List[float]]
    asset_ids: List[str] = Field(default_factory=list)
    
    # Matrix properties
    eigenvalues: List[float]
    principal_components: List[Dict[str, Any]]
    condition_number: Optional[float] = None
    
    # Statistics
    average_correlation: float
    max_correlation: float
    min_correlation: float
    correlation_clusters: Optional[List[List[str]]] = None

class ConcentrationAnalysisResponse(BaseModel):
    """Schema for portfolio concentration analysis"""
    deal_id: str
    dimension: str  # sector, industry, rating, etc.
    analysis_date: date
    
    # Concentration metrics
    concentrations: Dict[str, Decimal]  # dimension_value -> weight
    concentration_ratio_top5: Decimal
    concentration_ratio_top10: Decimal
    
    # Risk assessment
    concentration_risk_score: Decimal
    over_concentrated_segments: List[str]
    recommended_limits: Dict[str, Decimal]
    
    # Diversification metrics
    effective_number_of_positions: int
    diversification_ratio: Decimal

class StressScenario(BaseModel):
    """Individual stress test scenario"""
    scenario_name: str
    description: str
    
    # Scenario parameters
    default_rate_shock: Optional[Decimal] = None
    recovery_rate_shock: Optional[Decimal] = None
    spread_shock: Optional[Decimal] = None
    interest_rate_shock: Optional[Decimal] = None
    correlation_shock: Optional[Decimal] = None
    
    # Custom parameters
    custom_shocks: Optional[Dict[str, Any]] = None

class StressTestRequest(BaseModel):
    """Schema for stress test requests"""
    scenarios: List[StressScenario] = Field(..., min_items=1, max_items=20)
    time_horizon: int = Field(default=12, ge=1, le=120, description="Time horizon in months")
    monte_carlo_runs: int = Field(default=1000, ge=100, le=10000)
    include_correlation_breakdown: bool = Field(default=True)
    
class StressTestResult(BaseModel):
    """Individual stress test scenario result"""
    scenario: StressScenario
    
    # Impact metrics
    portfolio_loss: Decimal
    loss_percentage: Decimal
    tranche_impacts: Dict[str, Decimal]
    
    # Risk metrics under stress
    stressed_var: Decimal
    stressed_volatility: Decimal
    time_to_recovery: Optional[int] = None  # months
    
    # Asset-level impacts
    worst_performing_assets: List[Dict[str, Any]]
    sector_impacts: Dict[str, Decimal]

class StressTestResponse(BaseModel):
    """Schema for comprehensive stress test results"""
    deal_id: str
    test_date: datetime
    scenarios_tested: int
    monte_carlo_runs: int
    
    # Individual scenario results
    scenario_results: List[StressTestResult]
    
    # Summary statistics
    worst_case_loss: Decimal
    best_case_loss: Decimal
    median_loss: Decimal
    loss_distribution: Dict[str, int]  # loss_bucket -> frequency
    
    # Risk rankings
    scenario_rankings: List[str]  # scenarios ranked by severity
    critical_scenarios: List[str]

class RiskReportRequest(BaseModel):
    """Schema for risk report generation requests"""
    report_type: str = Field(..., pattern="^(summary|detailed|regulatory|custom)$")
    include_sections: List[str] = Field(
        default=["metrics", "concentration", "stress_test", "recommendations"],
        description="Sections to include in the report"
    )
    custom_parameters: Optional[Dict[str, Any]] = None
    format: str = Field(default="json", pattern="^(json|pdf|excel)$")

class RiskReportResponse(BaseModel):
    """Schema for risk report responses"""
    deal_id: str
    report_type: str
    generation_date: datetime
    
    # Report sections
    executive_summary: Dict[str, Any]
    risk_metrics: Optional[RiskMetricsResponse] = None
    concentration_analysis: Optional[ConcentrationAnalysisResponse] = None
    stress_test_results: Optional[StressTestResponse] = None
    
    # Recommendations
    risk_recommendations: List[str]
    action_items: List[Dict[str, Any]]
    
    # Report metadata
    data_as_of_date: date
    report_version: str = "1.0"
    next_review_date: Optional[date] = None

class VaRCalculationResponse(BaseModel):
    """Schema for Value at Risk calculation responses"""
    deal_id: str
    confidence_level: float
    time_horizon_days: int
    method: str
    
    # VaR results
    var_amount: Decimal
    var_percentage: Decimal
    expected_shortfall: Decimal
    portfolio_value: Decimal
    
    # Method-specific details
    calculation_details: Dict[str, Any]
    assumptions: List[str]
    
class RiskAttributionResponse(BaseModel):
    """Schema for risk attribution analysis"""
    deal_id: str
    attribution_type: str
    total_portfolio_risk: Decimal
    
    # Attribution breakdown
    attributions: Dict[str, Decimal]  # component -> risk contribution
    marginal_contributions: Dict[str, Decimal]
    component_contributions: Dict[str, Decimal]
    
    # Top contributors
    top_risk_contributors: List[Dict[str, Any]]
    risk_concentration_score: Decimal

class CorrelationHeatmapData(BaseModel):
    """Schema for correlation heatmap visualization data"""
    asset_ids: List[str]
    correlation_matrix: List[List[float]]
    labels: List[str]
    
    # Statistics for color scaling
    max_correlation: float
    min_correlation: float
    avg_correlation: float
    
    # Metadata
    data_date: Optional[date] = None
    matrix_size: int