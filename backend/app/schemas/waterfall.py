"""
Waterfall Schemas
Pydantic models for waterfall calculation-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class WaterfallCalculationRequest(BaseModel):
    """Schema for waterfall calculation requests"""
    deal_id: str
    payment_date: date
    available_funds: Decimal = Field(..., ge=0)
    principal_collections: Decimal = Field(default=Decimal(0), ge=0)
    interest_collections: Decimal = Field(default=Decimal(0), ge=0)
    
    # Optional scenario parameters
    scenario_name: Optional[str] = None
    stress_factor: Optional[Decimal] = None
    trigger_overrides: Optional[Dict[str, Any]] = None

class PaymentStep(BaseModel):
    """Individual payment step in waterfall"""
    step_number: int
    description: str
    payment_type: str  # interest, principal, fees, etc.
    target_amount: Decimal
    actual_amount: Decimal
    remaining_funds: Decimal
    tranche_id: Optional[str] = None
    priority: int

class WaterfallCalculationResponse(BaseModel):
    """Schema for waterfall calculation responses"""
    deal_id: str
    payment_date: date
    calculation_timestamp: datetime
    
    # Input amounts
    total_available_funds: Decimal
    principal_collections: Decimal
    interest_collections: Decimal
    
    # Payment steps
    payment_steps: List[PaymentStep]
    
    # Summary by category
    total_fees_paid: Decimal
    total_interest_paid: Decimal
    total_principal_paid: Decimal
    total_distributions: Decimal
    remaining_funds: Decimal
    
    # Tranche-level results
    tranche_payments: Dict[str, Dict[str, Decimal]]
    
    # Trigger status after payment
    trigger_status: Dict[str, bool]

class PaymentSequenceStep(BaseModel):
    """Payment sequence configuration step"""
    priority: int
    type: str
    description: str
    calculation_method: str = "standard"
    parameters: Optional[Dict[str, Any]] = None

class PaymentSequenceResponse(BaseModel):
    """Schema for payment sequence configuration"""
    deal_id: str
    payment_date: date
    sequence: List[PaymentSequenceStep]
    version: str = "1.0"
    last_updated: Optional[datetime] = None

class CashFlowProjectionRequest(BaseModel):
    """Schema for cash flow projection requests"""
    start_date: date
    end_date: date
    scenario: str = Field(default="base", description="Scenario name for projections")
    
    # Projection assumptions
    assumptions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom assumptions for the projection"
    )
    
    # Output preferences
    include_monthly_detail: bool = Field(default=True)
    include_stress_scenarios: bool = Field(default=False)

class MonthlyProjection(BaseModel):
    """Monthly cash flow projection data"""
    payment_date: date
    principal_collections: Decimal
    interest_collections: Decimal
    fees_and_expenses: Decimal
    senior_payments: Decimal
    mezzanine_payments: Decimal
    subordinate_payments: Decimal
    equity_distribution: Decimal
    ending_balance: Decimal

class CashFlowProjectionResponse(BaseModel):
    """Schema for cash flow projection responses"""
    deal_id: str
    scenario: str
    projection_date: datetime
    start_date: date
    end_date: date
    
    # Monthly projections
    monthly_projections: List[MonthlyProjection]
    
    # Summary statistics
    total_collections: Decimal
    total_distributions: Decimal
    average_monthly_payment: Decimal
    final_recovery_rate: Decimal
    
    # Risk metrics
    duration: Optional[Decimal] = None
    weighted_average_life: Optional[Decimal] = None

class StressTestScenario(BaseModel):
    """Stress test scenario definition"""
    scenario_name: str
    description: str
    default_rate: Decimal = Field(ge=0, le=1)
    recovery_rate: Decimal = Field(ge=0, le=1)
    prepayment_rate: Decimal = Field(ge=0, le=1)
    spread_shock: Optional[Decimal] = None

class StressTestResult(BaseModel):
    """Individual stress test result"""
    scenario: StressTestScenario
    projected_loss: Decimal
    tranche_impacts: Dict[str, Decimal]
    trigger_breaches: List[str]
    time_to_breach: Optional[int] = None  # months

class WaterfallConfigTemplate(BaseModel):
    """Waterfall configuration template"""
    name: str
    version: str
    description: str
    features: List[str]
    
    # Template structure
    payment_sequence: List[PaymentSequenceStep]
    trigger_definitions: Dict[str, Any]
    fee_structure: Dict[str, Any]

class ConfigurationValidationResult(BaseModel):
    """Validation result for waterfall configuration"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Detailed validation results
    payment_sequence_valid: bool = True
    trigger_config_valid: bool = True
    fee_structure_valid: bool = True