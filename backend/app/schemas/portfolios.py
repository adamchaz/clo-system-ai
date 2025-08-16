"""
Portfolio Schemas
Pydantic models for portfolio and CLO deal-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum

class DealStatus(str, Enum):
    """CLO deal status enumeration"""
    RAMPING = "ramping"
    EFFECTIVE = "effective"
    REVOLVING = "revolving"
    AMORTIZING = "amortizing"
    LIQUIDATING = "liquidating"
    CLOSED = "closed"

class CLODealBase(BaseModel):
    """Base CLO deal model"""
    deal_name: str
    manager: Optional[str] = None
    trustee: Optional[str] = None
    effective_date: Optional[date] = None
    stated_maturity: Optional[date] = None
    revolving_period_end: Optional[date] = None
    reinvestment_period_end: Optional[date] = None
    deal_size: Optional[Decimal] = None
    currency: str = Field(default="USD")
    status: DealStatus = DealStatus.RAMPING
    
class CLODealCreate(CLODealBase):
    """Schema for creating a new CLO deal"""
    deal_name: str = Field(..., min_length=1, max_length=200)
    manager: str = Field(..., min_length=1)
    effective_date: date = Field(...)
    deal_size: Decimal = Field(..., gt=0)
    
class CLODealUpdate(BaseModel):
    """Schema for updating a CLO deal"""
    deal_name: Optional[str] = None
    manager: Optional[str] = None
    status: Optional[DealStatus] = None
    revolving_period_end: Optional[date] = None
    reinvestment_period_end: Optional[date] = None
    
class CLODealResponse(CLODealBase):
    """Schema for CLO deal API responses"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Computed fields
    days_to_maturity: Optional[int] = None
    current_asset_count: int = 0
    current_portfolio_balance: Decimal = Decimal(0)
    
    class Config:
        from_attributes = True

class TrancheBase(BaseModel):
    """Base tranche model"""
    tranche_name: str
    tranche_type: str  # Senior, Mezzanine, Subordinate, Equity
    original_balance: Decimal
    current_balance: Decimal
    coupon_rate: Optional[Decimal] = None
    spread: Optional[Decimal] = None
    rating: Optional[str] = None
    
class TrancheResponse(TrancheBase):
    """Schema for tranche responses"""
    id: str
    deal_id: str
    payment_priority: int
    is_floating_rate: bool = False
    
    class Config:
        from_attributes = True

class DealAssetResponse(BaseModel):
    """Schema for assets within a deal"""
    asset_id: str
    deal_id: str
    allocation_amount: Decimal
    allocation_percentage: Decimal
    date_added: datetime
    is_active: bool = True
    
    # Asset details
    cusip: Optional[str] = None
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    rating: Optional[str] = None
    
class PortfolioSummaryResponse(BaseModel):
    """Schema for portfolio summary statistics"""
    deal_id: str
    total_assets: int
    total_balance: Decimal
    average_rating: str
    weighted_average_life: Optional[Decimal] = None
    analysis_date: Optional[str] = None  # Date the analysis was performed
    
    # Diversification metrics
    sector_diversification: Dict[str, Decimal]
    rating_diversification: Dict[str, Decimal]
    geography_diversification: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Risk metrics
    average_spread: Optional[Decimal] = None
    duration: Optional[Decimal] = None
    convexity: Optional[Decimal] = None
    
    # Top holdings
    top_holdings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Maturity profile
    maturity_profile: Dict[str, int]
    
    # Cash flow metrics
    current_yield: Optional[Decimal] = None
    yield_to_maturity: Optional[Decimal] = None
    
class TriggerTestResult(BaseModel):
    """Schema for OC/IC trigger test results"""
    trigger_type: str  # "OC" or "IC"
    tranche_name: str
    threshold: Decimal
    current_value: Decimal
    is_passing: bool
    margin: Decimal
    last_tested: datetime
    
class DealTriggerStatus(BaseModel):
    """Schema for deal trigger status"""
    deal_id: str
    oc_triggers: List[TriggerTestResult]
    ic_triggers: List[TriggerTestResult]
    overall_status: str  # "compliant", "breached", "warning"
    last_updated: datetime
    
class WaterfallResult(BaseModel):
    """Schema for waterfall calculation results"""
    deal_id: str
    payment_date: date
    available_funds: Decimal
    
    # Payments by tranche
    senior_payments: List[Dict[str, Any]]
    mezzanine_payments: List[Dict[str, Any]]
    subordinate_payments: List[Dict[str, Any]]
    equity_distribution: Decimal
    
    # Fees and expenses
    management_fee: Decimal
    trustee_fee: Decimal
    other_expenses: Decimal
    
    # Remaining funds
    excess_spread: Decimal
    principal_collections: Decimal
    interest_collections: Decimal
    
class PortfolioStatsResponse(BaseModel):
    """Schema for overall portfolio statistics"""
    total_deals: int
    active_deals: int
    total_assets_under_management: Decimal
    average_deal_size: Decimal
    
    deals_by_status: Dict[str, int]
    deals_by_manager: Dict[str, int]
    
    # Performance metrics
    portfolio_yield: Optional[Decimal] = None
    average_rating: str
    total_market_value: Decimal