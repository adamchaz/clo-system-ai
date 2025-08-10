"""
Asset Management API Endpoints
Handles asset CRUD operations, correlation lookups, and asset analytics
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....services.data_integration import DataIntegrationService
from ....schemas.assets import (
    AssetResponse, 
    AssetCreate, 
    AssetUpdate,
    AssetCorrelationResponse,
    AssetListResponse
)

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_integration_service():
    """Data integration service dependency"""
    return DataIntegrationService()

@router.get("/", response_model=AssetListResponse)
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    asset_type: Optional[str] = Query(None),
    rating: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all assets with pagination and filtering"""
    # Implementation will query operational database
    # For now, return migrated data
    integration_service = get_integration_service()
    
    try:
        assets = integration_service.get_assets_paginated(
            skip=skip, 
            limit=limit,
            asset_type=asset_type,
            rating=rating
        )
        
        total_count = integration_service.get_assets_count(
            asset_type=asset_type,
            rating=rating
        )
        
        return AssetListResponse(
            assets=assets,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assets: {str(e)}")

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get a specific asset by ID"""
    try:
        asset = integration_service.get_asset_by_id(asset_id)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return AssetResponse(**asset)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch asset: {str(e)}")

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset in operational database"""
    # This will create assets in the operational PostgreSQL database
    try:
        # Implementation will use operational database models
        # For now, placeholder response
        raise HTTPException(status_code=501, detail="Asset creation not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create asset: {str(e)}")

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing asset"""
    try:
        # Implementation will update operational database
        raise HTTPException(status_code=501, detail="Asset update not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """Delete an asset (soft delete)"""
    try:
        # Implementation will soft delete from operational database
        raise HTTPException(status_code=501, detail="Asset deletion not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete asset: {str(e)}")

@router.get("/{asset_id}/correlations", response_model=List[AssetCorrelationResponse])
async def get_asset_correlations(
    asset_id: str,
    limit: int = Query(50, ge=1, le=500),
    threshold: Optional[float] = Query(None, ge=-1.0, le=1.0),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get correlations for a specific asset"""
    try:
        correlations = integration_service.get_asset_correlations(
            asset_id, 
            limit=limit,
            threshold=threshold
        )
        
        return [
            AssetCorrelationResponse(
                asset_id_1=corr['asset_id_1'],
                asset_id_2=corr['asset_id_2'],
                correlation=corr['correlation'],
                last_updated=corr.get('last_updated')
            )
            for corr in correlations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch correlations: {str(e)}")

@router.get("/correlations/{asset_id_1}/{asset_id_2}")
async def get_specific_correlation(
    asset_id_1: str,
    asset_id_2: str,
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get correlation between two specific assets"""
    try:
        correlation = integration_service.get_correlation(asset_id_1, asset_id_2)
        
        if correlation is None:
            raise HTTPException(status_code=404, detail="Correlation not found")
        
        return {
            "asset_id_1": asset_id_1,
            "asset_id_2": asset_id_2,
            "correlation": correlation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch correlation: {str(e)}")

@router.get("/stats/summary")
async def get_asset_stats(
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get asset statistics summary"""
    try:
        stats = integration_service.get_asset_statistics()
        
        return {
            "total_assets": stats.get('total_count', 0),
            "by_type": stats.get('by_type', {}),
            "by_rating": stats.get('by_rating', {}),
            "correlations_available": stats.get('correlation_count', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch asset stats: {str(e)}")