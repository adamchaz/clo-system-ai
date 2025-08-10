"""
Scenario Analysis Schemas
Pydantic models for scenario-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum

class ScenarioType(str, Enum):
    """Scenario type enumeration"""
    MAG = "MAG"
    CUSTOM = "custom"
    REGULATORY = "regulatory"
    STRESS = "stress"

class AnalysisType(str, Enum):
    """Analysis type enumeration"""
    PORTFOLIO_IMPACT = "portfolio_impact"
    CASH_FLOW = "cash_flow"
    RISK_METRICS = "risk_metrics"
    WATERFALL = "waterfall"
    COMPREHENSIVE = "comprehensive"

class ScenarioBase(BaseModel):
    """Base scenario model"""
    name: str
    description: Optional[str] = None
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    is_active: bool = True

class ScenarioCreate(ScenarioBase):
    """Schema for creating a new scenario"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(..., description="Scenario parameters")
    
class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

class ScenarioResponse(ScenarioBase):
    """Schema for scenario API responses"""
    id: str
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    created_by: Optional[str] = None
    
    # Computed fields
    parameter_count: int = 0
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True

class ScenarioParameter(BaseModel):
    """Individual scenario parameter"""
    parameter_name: str
    category: str
    value: Any  # Can be string, number, boolean, etc.
    unit: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None

class ScenarioParametersResponse(BaseModel):
    """Schema for scenario parameters response"""
    scenario_id: str
    parameter_count: int
    parameters: List[ScenarioParameter]
    
    # Parameter organization
    parameters_by_category: Optional[Dict[str, List[ScenarioParameter]]] = None
    
    # Metadata
    last_updated: Optional[datetime] = None
    data_source: str = "migration_database"

class ScenarioAnalysisRequest(BaseModel):
    """Schema for scenario analysis requests"""
    deal_ids: List[str] = Field(..., min_items=1, max_items=10)
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    time_horizon: int = Field(default=60, ge=1, le=360, description="Time horizon in months")
    
    # Analysis options
    include_stress_testing: bool = Field(default=True)
    include_correlation_analysis: bool = Field(default=True)
    include_waterfall_impact: bool = Field(default=True)
    
    # Custom parameters
    custom_parameters: Optional[Dict[str, Any]] = None

class PortfolioImpact(BaseModel):
    """Portfolio impact under scenario"""
    deal_id: str
    base_portfolio_value: Decimal
    scenario_portfolio_value: Decimal
    value_change: Decimal
    value_change_percentage: Decimal
    
    # Detailed impacts
    asset_level_impacts: List[Dict[str, Any]] = Field(default_factory=list)
    sector_impacts: Dict[str, Decimal] = Field(default_factory=dict)
    rating_impacts: Dict[str, Decimal] = Field(default_factory=dict)

class ScenarioRiskMetrics(BaseModel):
    """Risk metrics under scenario"""
    portfolio_volatility: Decimal
    value_at_risk: Decimal
    expected_shortfall: Decimal
    maximum_drawdown: Decimal
    
    # Stress metrics
    tail_risk: Optional[Decimal] = None
    correlation_breakdown: Optional[Decimal] = None

class ScenarioAnalysisResponse(BaseModel):
    """Schema for comprehensive scenario analysis results"""
    scenario_id: str
    analysis_date: datetime
    deals_analyzed: List[str]
    analysis_type: AnalysisType
    
    # Portfolio impacts
    portfolio_impacts: List[PortfolioImpact]
    
    # Aggregated results
    total_portfolio_impact: Decimal
    weighted_average_impact: Decimal
    
    # Risk analysis
    risk_metrics: ScenarioRiskMetrics
    
    # Cash flow analysis
    cash_flow_impacts: Optional[List[Dict[str, Any]]] = None
    
    # Waterfall impacts
    waterfall_impacts: Optional[List[Dict[str, Any]]] = None
    
    # Recommendations
    key_findings: List[str] = Field(default_factory=list)
    risk_warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ScenarioComparison(BaseModel):
    """Schema for scenario comparison results"""
    scenarios: List[str]
    deal_id: str
    metrics_compared: List[str]
    
    # Comparison results
    metric_comparisons: Dict[str, Dict[str, Any]]  # metric -> scenario -> value
    relative_performance: Dict[str, Dict[str, Decimal]]  # metric -> scenario -> relative_score
    
    # Rankings
    scenario_rankings: Dict[str, List[str]]  # metric -> [scenarios ranked by performance]
    
    # Summary
    best_performing_scenario: Optional[str] = None
    worst_performing_scenario: Optional[str] = None
    recommended_scenario: Optional[str] = None
    recommendation_reason: Optional[str] = None

class MAGScenarioSummary(BaseModel):
    """Summary of MAG scenario data"""
    version_name: str
    parameter_count: int
    categories: List[str]
    
    # Sample parameters for preview
    sample_parameters: List[ScenarioParameter] = Field(default_factory=list)
    
    # Usage statistics
    last_accessed: Optional[datetime] = None
    analysis_count: int = 0

class ScenarioExportRequest(BaseModel):
    """Schema for scenario export requests"""
    export_format: str = Field(..., regex="^(json|excel|csv|pdf)$")
    include_analysis_history: bool = Field(default=False)
    include_parameter_descriptions: bool = Field(default=True)
    date_range: Optional[Dict[str, date]] = None

class ScenarioValidationResult(BaseModel):
    """Schema for scenario validation results"""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    
    # Parameter validation
    missing_required_parameters: List[str] = Field(default_factory=list)
    invalid_parameter_values: List[str] = Field(default_factory=list)
    
    # Compatibility checks
    compatible_deals: List[str] = Field(default_factory=list)
    incompatible_deals: List[str] = Field(default_factory=list)

class ScenarioUsageStats(BaseModel):
    """Schema for scenario usage statistics"""
    scenario_id: str
    total_analyses: int
    unique_users: int
    last_30_days_usage: int
    
    # Usage patterns
    popular_analysis_types: Dict[str, int]
    frequently_analyzed_deals: List[str]
    
    # Performance metrics
    average_analysis_time: Optional[Decimal] = None
    success_rate: Decimal