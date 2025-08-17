"""
Asset Schemas
Pydantic models for asset-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

class AssetBase(BaseModel):
    """Base asset model with common fields"""
    cusip: Optional[str] = None
    isin: Optional[str] = None
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    current_balance: Optional[Decimal] = None
    original_balance: Optional[Decimal] = None
    coupon_rate: Optional[Decimal] = None
    maturity_date: Optional[date] = None
    rating: Optional[str] = None
    
class AssetCreate(AssetBase):
    """Schema for creating a new asset"""
    cusip: str = Field(..., description="CUSIP identifier")
    asset_name: str = Field(..., description="Asset name")
    asset_type: str = Field(..., description="Asset type")
    current_balance: Decimal = Field(..., gt=0, description="Current balance")
    
class AssetUpdate(BaseModel):
    """Schema for updating an asset"""
    asset_name: Optional[str] = None
    current_balance: Optional[Decimal] = None
    coupon_rate: Optional[Decimal] = None
    rating: Optional[str] = None
    # Add other updatable fields as needed
    
class AssetResponse(AssetBase):
    """Schema for asset API responses - Complete 70-field database schema"""
    
    # Required fields (non-nullable in database)
    blkrock_id: str = Field(..., description="BlackRock asset identifier")
    issue_name: str = Field(..., description="Asset issue name") 
    issuer_name: str = Field(..., description="Issuer company name")
    par_amount: Decimal = Field(..., description="Principal amount outstanding")
    maturity: date = Field(..., description="Asset maturity date")
    
    # Optional string fields
    issuer_id: Optional[str] = None
    tranche: Optional[str] = None
    bond_loan: Optional[str] = None
    currency: Optional[str] = None
    coupon_type: Optional[str] = None
    index_name: Optional[str] = None
    amortization_type: Optional[str] = None
    day_count: Optional[str] = None
    business_day_conv: Optional[str] = None
    
    # Rating fields
    mdy_rating: Optional[str] = None
    mdy_dp_rating: Optional[str] = None
    mdy_dp_rating_warf: Optional[str] = None
    sp_rating: Optional[str] = None
    derived_mdy_rating: Optional[str] = None
    derived_sp_rating: Optional[str] = None
    mdy_facility_rating: Optional[str] = None
    mdy_facility_outlook: Optional[str] = None
    mdy_issuer_rating: Optional[str] = None
    mdy_issuer_outlook: Optional[str] = None
    mdy_snr_sec_rating: Optional[str] = None
    mdy_snr_unsec_rating: Optional[str] = None
    mdy_sub_rating: Optional[str] = None
    mdy_credit_est_rating: Optional[str] = None
    sandp_facility_rating: Optional[str] = None
    sandp_issuer_rating: Optional[str] = None
    sandp_snr_sec_rating: Optional[str] = None
    sandp_subordinate: Optional[str] = None
    sandp_rec_rating: Optional[str] = None
    
    # Industry and classification fields
    mdy_industry: Optional[str] = None
    sp_industry: Optional[str] = None
    country: Optional[str] = None
    seniority: Optional[str] = None
    mdy_asset_category: Optional[str] = None
    sp_priority_category: Optional[str] = None
    discount_curve_name: Optional[str] = None
    
    # Numeric fields
    market_value: Optional[Decimal] = None
    coupon: Optional[Decimal] = None
    cpn_spread: Optional[Decimal] = None
    libor_floor: Optional[Decimal] = None
    index_cap: Optional[Decimal] = None
    amount_issued: Optional[Decimal] = None
    pik_amount: Optional[Decimal] = None
    unfunded_amount: Optional[Decimal] = None
    mdy_recovery_rate: Optional[Decimal] = None
    fair_value: Optional[Decimal] = None
    commit_fee: Optional[Decimal] = None
    facility_size: Optional[Decimal] = None
    wal: Optional[Decimal] = None
    
    # Integer fields
    payment_freq: Optional[int] = None
    discount_curve_id: Optional[int] = None
    pricing_spread_bps: Optional[int] = None
    
    # Boolean fields
    payment_eom: Optional[bool] = None
    piking: Optional[bool] = None
    
    # Date fields
    dated_date: Optional[date] = None
    issue_date: Optional[date] = None
    first_payment_date: Optional[date] = None
    date_of_default: Optional[date] = None
    rating_derivation_date: Optional[date] = None
    fair_value_date: Optional[date] = None
    mdy_credit_est_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Text fields
    rating_source_hierarchy: Optional[str] = None
    analyst_opinion: Optional[str] = None
    
    # JSON fields
    flags: Optional[Dict[str, Any]] = None
    
    # Legacy API compatibility fields (aliases and computed)
    id: Optional[str] = Field(default=None, description="Alias for blkrock_id")
    asset_name: Optional[str] = Field(default=None, description="Alias for issue_name")
    asset_type: Optional[str] = Field(default=None, description="Alias for bond_loan") 
    issuer: Optional[str] = Field(default=None, description="Alias for issuer_name")
    industry: Optional[str] = Field(default=None, description="Alias for mdy_industry")
    sector: Optional[str] = Field(default=None, description="Alias for sp_industry")
    current_balance: Optional[Decimal] = Field(default=None, description="Alias for par_amount")
    original_balance: Optional[Decimal] = Field(default=None, description="Alias for facility_size")
    coupon_rate: Optional[Decimal] = Field(default=None, description="Alias for coupon")
    maturity_date: Optional[date] = Field(default=None, description="Alias for maturity")
    rating: Optional[str] = Field(default=None, description="Primary rating")
    spread: Optional[Decimal] = Field(default=None, description="Alias for cpn_spread")
    duration: Optional[Decimal] = Field(default=None, description="Alias for wal")
    recovery_rate: Optional[Decimal] = Field(default=None, description="Alias for mdy_recovery_rate")
    current_price: Optional[Decimal] = Field(default=None, description="Alias for market_value")
    final_maturity: Optional[date] = Field(default=None, description="Alias for maturity")
    current_rating: Optional[str] = Field(default=None, description="Current primary rating")
    last_updated: Optional[datetime] = Field(default=None, description="Alias for updated_at")
    status: Optional[str] = Field(default=None, description="Computed status field")
    is_active: Optional[bool] = Field(default=None, description="Computed active status")
    
    # Computed fields for frontend compatibility
    days_to_maturity: Optional[int] = None
    yield_to_maturity: Optional[Decimal] = None
    convexity: Optional[Decimal] = None
    default_probability: Optional[Decimal] = None
    lgd: Optional[Decimal] = None
    ead: Optional[Decimal] = None
    performance_1d: Optional[Decimal] = None
    performance_30d: Optional[Decimal] = None
    performance_ytd: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    purchase_date: Optional[date] = None
    
    class Config:
        from_attributes = True
        
class AssetListResponse(BaseModel):
    """Schema for paginated asset list responses"""
    assets: List[AssetResponse]
    total_count: int
    skip: int
    limit: int
    has_more: bool = Field(default=False)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.has_more = (self.skip + len(self.assets)) < self.total_count
        
class AssetCorrelationResponse(BaseModel):
    """Schema for asset correlation responses"""
    asset_id_1: str
    asset_id_2: str
    correlation: float = Field(..., ge=-1.0, le=1.0)
    last_updated: Optional[datetime] = None
    
class AssetStatistics(BaseModel):
    """Schema for asset statistics"""
    total_count: int
    by_type: Dict[str, int]
    by_rating: Dict[str, int]
    by_sector: Dict[str, int] = Field(default_factory=dict)
    by_industry: Dict[str, int] = Field(default_factory=dict)
    avg_balance: Optional[Decimal] = None
    total_balance: Optional[Decimal] = None
    
class AssetSearchRequest(BaseModel):
    """Schema for asset search requests"""
    query: str = Field(..., min_length=1)
    asset_type: Optional[str] = None
    rating: Optional[str] = None
    sector: Optional[str] = None
    min_balance: Optional[Decimal] = None
    max_balance: Optional[Decimal] = None
    limit: int = Field(default=50, ge=1, le=500)
    
class AssetCashFlowResponse(BaseModel):
    """Schema for asset cash flow responses"""
    asset_id: str
    payment_date: date
    principal_payment: Decimal
    interest_payment: Decimal
    total_payment: Decimal
    remaining_balance: Decimal
    
class BulkAssetOperationRequest(BaseModel):
    """Schema for bulk asset operations"""
    asset_ids: List[str] = Field(..., min_items=1, max_items=1000)
    operation: str = Field(..., pattern="^(activate|deactivate|delete|update)$")
    parameters: Optional[Dict[str, Any]] = None
    
class BulkAssetOperationResponse(BaseModel):
    """Schema for bulk asset operation responses"""
    total_requested: int
    successful: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    processed_asset_ids: List[str] = Field(default_factory=list)