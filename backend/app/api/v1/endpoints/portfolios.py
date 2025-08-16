"""
Portfolio Management API Endpoints
Handles CLO deal CRUD operations, portfolio analytics, and deal management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from ....core.database_config import db_config
from ....services.data_integration import DataIntegrationService
from ....utils.date_utils import get_analysis_date, validate_analysis_date
from ....schemas.portfolios import (
    CLODealResponse,
    CLODealCreate,
    CLODealUpdate,
    PortfolioSummaryResponse,
    DealAssetResponse
)

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_integration_service():
    """Data integration service dependency"""
    return DataIntegrationService()

@router.get("/")
async def list_clo_deals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None),
    analysis_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD), defaults to March 23, 2016"),
    db: Session = Depends(get_db)
):
    """List all CLO deals with pagination"""
    try:
        # Return sample CLO deals for development/testing (as of March 23, 2016)
        from datetime import datetime, date
        from decimal import Decimal
        
        # Calculate days to maturity from the analysis date
        target_analysis_date = get_analysis_date(analysis_date)
        
        sample_deals = [
            {
                "id": "CLO2014-001",
                "deal_name": "Magnetar Capital CLO 2014-1",
                "manager": "Magnetar Capital LLC",
                "trustee": "Wells Fargo Bank N.A.",
                "effective_date": date(2014, 6, 15),
                "stated_maturity": date(2021, 6, 15),
                "revolving_period_end": date(2016, 6, 15),
                "reinvestment_period_end": date(2016, 6, 15),
                "deal_size": Decimal("400000000.00"),
                "currency": "USD",
                "status": "revolving",
                "created_at": datetime(2014, 5, 1, 10, 0, 0),
                "updated_at": datetime(2016, 3, 20, 14, 30, 0),
                "is_active": True,
                "days_to_maturity": (date(2021, 6, 15) - target_analysis_date).days,
                "current_asset_count": 147,
                "current_portfolio_balance": Decimal("385500000.00")
            },
            {
                "id": "CLO2013-002", 
                "deal_name": "Blackstone Credit CLO 2013-A",
                "manager": "Blackstone Credit",
                "trustee": "U.S. Bank N.A.",
                "effective_date": date(2013, 9, 1),
                "stated_maturity": date(2020, 9, 1),
                "revolving_period_end": date(2015, 9, 1),
                "reinvestment_period_end": date(2015, 9, 1),
                "deal_size": Decimal("500000000.00"),
                "currency": "USD",
                "status": "amortizing",
                "created_at": datetime(2013, 8, 15, 9, 0, 0),
                "updated_at": datetime(2016, 3, 22, 11, 15, 0),
                "is_active": True,
                "days_to_maturity": (date(2020, 9, 1) - target_analysis_date).days,
                "current_asset_count": 203,
                "current_portfolio_balance": Decimal("467200000.00")
            },
            {
                "id": "CLO2015-003",
                "deal_name": "Apollo Credit CLO 2015-C",
                "manager": "Apollo Credit Management LLC",
                "trustee": "Deutsche Bank Trust Company",
                "effective_date": date(2015, 1, 20),
                "stated_maturity": date(2022, 1, 20),
                "revolving_period_end": date(2017, 1, 20),
                "reinvestment_period_end": date(2017, 1, 20),
                "deal_size": Decimal("350000000.00"),
                "currency": "USD",
                "status": "revolving",
                "created_at": datetime(2014, 12, 1, 14, 0, 0),
                "updated_at": datetime(2016, 3, 21, 16, 45, 0),
                "is_active": True,
                "days_to_maturity": (date(2022, 1, 20) - target_analysis_date).days,
                "current_asset_count": 98,
                "current_portfolio_balance": Decimal("328750000.00")
            }
        ]
        
        # Apply filtering
        filtered_deals = sample_deals
        if status:
            filtered_deals = [deal for deal in filtered_deals if deal["status"] == status]
            
        # Apply pagination
        paginated_deals = filtered_deals[skip:skip + limit]
        
        return {
            "data": paginated_deals,
            "message": f"Retrieved {len(paginated_deals)} portfolios successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CLO deals: {str(e)}")

@router.post("/", response_model=CLODealResponse)
async def create_clo_deal(
    deal: CLODealCreate,
    db: Session = Depends(get_db)
):
    """Create a new CLO deal"""
    try:
        # Implementation will create deal in operational database
        raise HTTPException(status_code=501, detail="CLO deal creation not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create CLO deal: {str(e)}")

@router.get("/{deal_id}", response_model=CLODealResponse)
async def get_clo_deal(
    deal_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific CLO deal by ID"""
    try:
        # Implementation will query operational database
        raise HTTPException(status_code=501, detail="CLO deal retrieval not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CLO deal: {str(e)}")

@router.put("/{deal_id}", response_model=CLODealResponse)
async def update_clo_deal(
    deal_id: str,
    deal_update: CLODealUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing CLO deal"""
    try:
        # Implementation will update operational database
        raise HTTPException(status_code=501, detail="CLO deal update not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update CLO deal: {str(e)}")

@router.get("/{deal_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    deal_id: str,
    analysis_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get comprehensive portfolio summary for a CLO deal"""
    try:
        # Validate and parse analysis date
        if analysis_date and not validate_analysis_date(analysis_date):
            raise HTTPException(status_code=400, detail="Invalid analysis date format. Use YYYY-MM-DD")
        
        target_date = get_analysis_date(analysis_date)
        
        # This will aggregate data from migrated assets and operational database as of the analysis date
        summary = {
            "deal_id": deal_id,
            "total_assets": 0,
            "total_balance": 0,
            "average_rating": "NR",
            "sector_diversification": {},
            "rating_diversification": {},
            "maturity_profile": {},
            "top_holdings": [],
            "analysis_date": target_date.isoformat()  # Include analysis date in response
        }
        
        return PortfolioSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio summary: {str(e)}")

@router.get("/{deal_id}/assets", response_model=List[DealAssetResponse])
async def get_deal_assets(
    deal_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    analysis_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db)
):
    """Get assets in a specific CLO deal"""
    try:
        # Implementation will query deal_assets table
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal assets: {str(e)}")

@router.post("/{deal_id}/assets")
async def add_asset_to_deal(
    deal_id: str,
    asset_id: str,
    allocation_amount: float,
    db: Session = Depends(get_db)
):
    """Add an asset to a CLO deal"""
    try:
        # Implementation will update deal_assets table
        raise HTTPException(status_code=501, detail="Add asset to deal not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add asset to deal: {str(e)}")

@router.delete("/{deal_id}/assets/{asset_id}")
async def remove_asset_from_deal(
    deal_id: str,
    asset_id: str,
    db: Session = Depends(get_db)
):
    """Remove an asset from a CLO deal"""
    try:
        # Implementation will update deal_assets table
        raise HTTPException(status_code=501, detail="Remove asset from deal not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove asset from deal: {str(e)}")

@router.get("/{deal_id}/tranches")
async def get_deal_tranches(
    deal_id: str,
    db: Session = Depends(get_db)
):
    """Get tranche structure for a CLO deal"""
    try:
        # Implementation will query clo_tranches table
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal tranches: {str(e)}")

@router.get("/{deal_id}/triggers")
async def get_deal_triggers(
    deal_id: str,
    analysis_date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db)
):
    """Get OC/IC trigger status for a CLO deal"""
    try:
        # Implementation will query trigger tables
        return {
            "oc_triggers": [],
            "ic_triggers": [],
            "status": "compliant"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal triggers: {str(e)}")

@router.get("/stats/overview")
async def get_portfolio_stats():
    """Get portfolio statistics overview"""
    try:
        from decimal import Decimal
        
        return {
            "total_deals": 3,
            "active_deals": 3,
            "total_assets_under_management": Decimal("1171450000.00"),
            "average_deal_size": Decimal("416666666.67"),
            "deals_by_status": {
                "effective": 1,
                "revolving": 1,
                "amortizing": 1
            },
            "deals_by_manager": {
                "Magnetar Capital LLC": 1,
                "Blackstone Credit": 1,
                "Apollo Credit Management LLC": 1
            },
            "portfolio_yield": Decimal("7.85"),
            "average_rating": "B+",
            "total_market_value": Decimal("1171450000.00")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio stats: {str(e)}")