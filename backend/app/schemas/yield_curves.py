"""
Yield Curve Pydantic Schemas
Data validation and serialization models for yield curve API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import date
from decimal import Decimal


class YieldCurveRateInput(BaseModel):
    """Input model for individual yield curve rates"""
    maturity_month: int = Field(..., ge=1, le=600, description="Maturity in months")
    spot_rate: float = Field(..., ge=-0.10, le=1.0, description="Spot rate (decimal, e.g., 0.035 for 3.5%)")

    @validator('spot_rate')
    def validate_spot_rate(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('spot_rate must be a number')
        return float(v)


class YieldCurveCreate(BaseModel):
    """Schema for creating a new yield curve"""
    curve_name: str = Field(..., min_length=1, max_length=100, description="Unique curve name")
    curve_type: str = Field(default="GENERIC", max_length=50, description="Curve type (GENERIC, LIBOR, SOFR, etc.)")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    analysis_date: date = Field(..., description="Analysis date for the curve")
    description: Optional[str] = Field(None, max_length=500, description="Curve description")
    rates: List[YieldCurveRateInput] = Field(..., min_items=2, description="List of rate points (minimum 2)")

    @validator('rates')
    def validate_rates(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 rate points required')
        
        # Check for duplicate maturities
        maturities = [rate.maturity_month for rate in v]
        if len(maturities) != len(set(maturities)):
            raise ValueError('Duplicate maturity months not allowed')
        
        return v

    @validator('curve_name')
    def validate_curve_name(cls, v):
        if not v.strip():
            raise ValueError('Curve name cannot be empty')
        return v.strip()


class YieldCurveUpdate(BaseModel):
    """Schema for updating a yield curve"""
    curve_name: Optional[str] = Field(None, min_length=1, max_length=100)
    curve_type: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    analysis_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    rates: Optional[List[YieldCurveRateInput]] = Field(None, min_items=2)
    is_active: Optional[bool] = None

    @validator('rates')
    def validate_rates(cls, v):
        if v is not None:
            if len(v) < 2:
                raise ValueError('At least 2 rate points required')
            
            # Check for duplicate maturities
            maturities = [rate.maturity_month for rate in v]
            if len(maturities) != len(set(maturities)):
                raise ValueError('Duplicate maturity months not allowed')
        
        return v


class YieldCurveRateResponse(BaseModel):
    """Response model for yield curve rates"""
    rate_id: int
    maturity_month: int
    maturity_date: Optional[date]
    spot_rate: float
    is_interpolated: bool
    source: Optional[str]

    class Config:
        orm_mode = True


class ForwardRateResponse(BaseModel):
    """Response model for forward rates"""
    forward_id: int
    forward_date: date
    period_start_date: date
    period_months: int
    forward_rate: float
    calculation_method: str

    class Config:
        orm_mode = True


class YieldCurveResponse(BaseModel):
    """Response model for yield curves"""
    curve_id: int
    curve_name: str
    curve_type: str
    currency: str
    analysis_date: date
    base_date: date
    last_month: int
    description: Optional[str]
    is_active: bool
    created_date: Optional[date]
    updated_date: Optional[date]
    
    # Related data
    rates: List[YieldCurveRateResponse] = []
    forward_rates: List[ForwardRateResponse] = []

    class Config:
        orm_mode = True


class YieldCurveSummaryResponse(BaseModel):
    """Summary response model for yield curve lists"""
    curve_id: int
    curve_name: str
    curve_type: str
    currency: str
    analysis_date: date
    description: Optional[str]
    is_active: bool
    rate_count: int
    maturity_range: str  # e.g., "1M - 10Y"

    class Config:
        orm_mode = True


class YieldCurveRateCalculationRequest(BaseModel):
    """Request model for rate calculations"""
    curve_id: int
    calculation_date: date
    maturity_months: int = Field(..., ge=1, le=600)


class YieldCurveRateCalculationResponse(BaseModel):
    """Response model for rate calculations"""
    curve_id: int
    curve_name: str
    calculation_date: date
    maturity_months: int
    spot_rate: float
    is_interpolated: bool
    calculation_method: str


class YieldCurveScenarioRequest(BaseModel):
    """Request model for yield curve scenarios"""
    base_curve_id: int
    scenario_name: str = Field(..., min_length=1, max_length=100)
    scenario_type: str = Field(..., max_length=50)  # PARALLEL_SHIFT, STEEPENING, etc.
    shift_type: str = Field(default="ABSOLUTE", max_length=20)  # ABSOLUTE, RELATIVE
    parallel_shift_bps: Optional[int] = Field(None, description="Parallel shift in basis points")
    steepening_bps: Optional[int] = Field(None, description="Steepening adjustment in basis points")
    twist_point_months: Optional[int] = Field(None, description="Twist point for steepening")
    description: Optional[str] = Field(None, max_length=500)


class YieldCurveListResponse(BaseModel):
    """Response model for yield curve lists with pagination"""
    curves: List[YieldCurveSummaryResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class BulkRateCalculationRequest(BaseModel):
    """Request model for bulk rate calculations"""
    curve_id: int
    calculation_date: date
    maturity_months_list: List[int] = Field(..., min_items=1, max_items=100)

    @validator('maturity_months_list')
    def validate_maturities(cls, v):
        for months in v:
            if months < 1 or months > 600:
                raise ValueError(f'Invalid maturity months: {months}. Must be between 1 and 600.')
        return v


class BulkRateCalculationResponse(BaseModel):
    """Response model for bulk rate calculations"""
    curve_id: int
    curve_name: str
    calculation_date: date
    rates: List[Dict[str, Any]]  # List of {maturity_months, spot_rate, is_interpolated}