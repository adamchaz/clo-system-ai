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
    portfolio_id: Optional[str] = Query(None),
    deal_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all assets with pagination and filtering"""
    # Test if this endpoint is being called
    if portfolio_id == 'TEST_BREAK':
        raise HTTPException(status_code=999, detail="Test endpoint is working")
    # Handle deal-specific filtering using deal_assets join
    effective_deal_id = deal_id or portfolio_id  # Support both parameters for compatibility
    
    if effective_deal_id:
        print(f"DEBUG: Filtering assets for deal_id: {effective_deal_id}")
        try:
            from sqlalchemy import text
            
            # Build query with JOIN to deal_assets table for deal-specific assets
            query = """
                SELECT a.* 
                FROM assets a 
                JOIN deal_assets da ON a.blkrock_id = da.blkrock_id 
                WHERE da.deal_id = :deal_id AND da.par_amount > 0
            """
            count_query = """
                SELECT COUNT(*) 
                FROM assets a 
                JOIN deal_assets da ON a.blkrock_id = da.blkrock_id 
                WHERE da.deal_id = :deal_id AND da.par_amount > 0
            """
            params = {'deal_id': effective_deal_id}
            
            # Add additional filters
            if asset_type:
                query += " AND bond_loan = :asset_type"
                count_query += " AND bond_loan = :asset_type"
                params['asset_type'] = asset_type
                
            if rating:
                query += " AND (mdy_rating = :rating OR sp_rating = :rating)"
                count_query += " AND (mdy_rating = :rating OR sp_rating = :rating)"
                params['rating'] = rating
                
            if search:
                query += " AND (LOWER(issue_name) LIKE LOWER(:search) OR LOWER(issuer_name) LIKE LOWER(:search) OR LOWER(blkrock_id) LIKE LOWER(:search))"
                count_query += " AND (LOWER(issue_name) LIKE LOWER(:search) OR LOWER(issuer_name) LIKE LOWER(:search) OR LOWER(blkrock_id) LIKE LOWER(:search))"
                params['search'] = f'%{search}%'
            
            query += " ORDER BY par_amount DESC LIMIT :limit OFFSET :skip"
            params.update({'skip': skip, 'limit': limit})
            
            # Get total count
            total_result = db.execute(text(count_query), {k: v for k, v in params.items() if k not in ['skip', 'limit']})
            total_count = total_result.scalar()
            
            # Get paginated results
            result = db.execute(text(query), params).fetchall()
            
            # Convert to API format
            assets = []
            for row in result:
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                from decimal import Decimal
                
                # Complete mapping matching AssetResponse schema
                asset_dict = {
                        # Required fields
                        "blkrock_id": row_dict.get('blkrock_id', ''),
                        "issue_name": row_dict.get('issue_name', ''),
                        "issuer_name": row_dict.get('issuer_name', ''),
                        "par_amount": float(row_dict.get('par_amount', 0)),
                        "maturity": row_dict.get('maturity'),
                        
                        # Optional string fields
                        "issuer_id": row_dict.get('issuer_id'),
                        "tranche": row_dict.get('tranche'),
                        "bond_loan": row_dict.get('bond_loan'),
                        "currency": row_dict.get('currency', 'USD'),
                        "coupon_type": row_dict.get('coupon_type'),
                        "index_name": row_dict.get('index_name'),
                        "amortization_type": row_dict.get('amortization_type'),
                        "day_count": row_dict.get('day_count'),
                        "business_day_conv": row_dict.get('business_day_conv'),
                        
                        # Rating fields
                        "mdy_rating": row_dict.get('mdy_rating'),
                        "mdy_dp_rating": row_dict.get('mdy_dp_rating'),
                        "mdy_dp_rating_warf": row_dict.get('mdy_dp_rating_warf'),
                        "sp_rating": row_dict.get('sp_rating'),
                        "derived_mdy_rating": row_dict.get('derived_mdy_rating'),
                        "derived_sp_rating": row_dict.get('derived_sp_rating'),
                        "mdy_facility_rating": row_dict.get('mdy_facility_rating'),
                        "mdy_facility_outlook": row_dict.get('mdy_facility_outlook'),
                        "mdy_issuer_rating": row_dict.get('mdy_issuer_rating'),
                        "mdy_issuer_outlook": row_dict.get('mdy_issuer_outlook'),
                        "mdy_snr_sec_rating": row_dict.get('mdy_snr_sec_rating'),
                        "mdy_snr_unsec_rating": row_dict.get('mdy_snr_unsec_rating'),
                        "mdy_sub_rating": row_dict.get('mdy_sub_rating'),
                        "mdy_credit_est_rating": row_dict.get('mdy_credit_est_rating'),
                        "sandp_facility_rating": row_dict.get('sandp_facility_rating'),
                        "sandp_issuer_rating": row_dict.get('sandp_issuer_rating'),
                        "sandp_snr_sec_rating": row_dict.get('sandp_snr_sec_rating'),
                        "sandp_subordinate": row_dict.get('sandp_subordinate'),
                        "sandp_rec_rating": row_dict.get('sandp_rec_rating'),
                        
                        # Industry and classification
                        "mdy_industry": row_dict.get('mdy_industry'),
                        "sp_industry": row_dict.get('sp_industry'),
                        "country": row_dict.get('country'),
                        "seniority": row_dict.get('seniority'),
                        "mdy_asset_category": row_dict.get('mdy_asset_category'),
                        "sp_priority_category": row_dict.get('sp_priority_category'),
                        "discount_curve_name": row_dict.get('discount_curve_name'),
                        
                        # Numeric fields
                        "market_value": float(row_dict.get('market_value', 0)) if row_dict.get('market_value') else None,
                        "coupon": float(row_dict.get('coupon', 0)) if row_dict.get('coupon') else None,
                        "cpn_spread": float(row_dict.get('cpn_spread', 0)) if row_dict.get('cpn_spread') else None,
                        "libor_floor": float(row_dict.get('libor_floor', 0)) if row_dict.get('libor_floor') else None,
                        "index_cap": float(row_dict.get('index_cap', 0)) if row_dict.get('index_cap') else None,
                        "amount_issued": float(row_dict.get('amount_issued', 0)) if row_dict.get('amount_issued') else None,
                        "pik_amount": float(row_dict.get('pik_amount', 0)) if row_dict.get('pik_amount') else None,
                        "unfunded_amount": float(row_dict.get('unfunded_amount', 0)) if row_dict.get('unfunded_amount') else None,
                        "mdy_recovery_rate": float(row_dict.get('mdy_recovery_rate', 0)) if row_dict.get('mdy_recovery_rate') else None,
                        "fair_value": float(row_dict.get('fair_value', 0)) if row_dict.get('fair_value') else None,
                        "commit_fee": float(row_dict.get('commit_fee', 0)) if row_dict.get('commit_fee') else None,
                        "facility_size": float(row_dict.get('facility_size', 0)) if row_dict.get('facility_size') else None,
                        "wal": float(row_dict.get('wal', 0)) if row_dict.get('wal') else None,
                        
                        # Integer fields
                        "payment_freq": row_dict.get('payment_freq'),
                        "discount_curve_id": row_dict.get('discount_curve_id'),
                        "pricing_spread_bps": row_dict.get('pricing_spread_bps'),
                        
                        # Boolean fields
                        "payment_eom": row_dict.get('payment_eom'),
                        "piking": row_dict.get('piking'),
                        
                        # Date fields
                        "dated_date": row_dict.get('dated_date'),
                        "issue_date": row_dict.get('issue_date'),
                        "first_payment_date": row_dict.get('first_payment_date'),
                        "date_of_default": row_dict.get('date_of_default'),
                        "rating_derivation_date": row_dict.get('rating_derivation_date'),
                        "fair_value_date": row_dict.get('fair_value_date'),
                        "mdy_credit_est_date": row_dict.get('mdy_credit_est_date'),
                        "created_at": row_dict.get('created_at'),
                        "updated_at": row_dict.get('updated_at'),
                        
                        # Text fields
                        "rating_source_hierarchy": row_dict.get('rating_source_hierarchy'),
                        "analyst_opinion": row_dict.get('analyst_opinion'),
                        
                        # JSON fields
                        "flags": row_dict.get('flags')
                }
                assets.append(asset_dict)
            
            # Convert to AssetResponse objects
            asset_responses = [AssetResponse(**asset) for asset in assets]
            
            return AssetListResponse(
                assets=asset_responses,
                total_count=total_count,
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            # If portfolio filtering fails, log the error and fall back to regular filtering
            print(f"Portfolio filtering error for {portfolio_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Portfolio filtering failed: {str(e)}")
    
    # No portfolio filter - use existing logic
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
        
        # Convert to AssetResponse objects
        asset_responses = [AssetResponse(**asset) for asset in assets]
        
        return AssetListResponse(
            assets=asset_responses,
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