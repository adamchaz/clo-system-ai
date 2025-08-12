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
    """Schema for asset API responses"""
    id: str = Field(..., description="Internal asset ID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Additional computed fields
    days_to_maturity: Optional[int] = None
    yield_to_maturity: Optional[Decimal] = None
    duration: Optional[Decimal] = None
    
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