"""
Yield Curve Management API Endpoints
Handles yield curve CRUD operations, rate calculations, and scenario analysis
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
import logging

from app.core.database_config import db_config
from app.models.yield_curve import YieldCurve, YieldCurveService, YieldCurveModel, YieldCurveRateModel, ForwardRateModel
from app.schemas.yield_curves import (
    YieldCurveCreate,
    YieldCurveUpdate,
    YieldCurveResponse,
    YieldCurveSummaryResponse,
    YieldCurveListResponse,
    YieldCurveRateCalculationRequest,
    YieldCurveRateCalculationResponse,
    BulkRateCalculationRequest,
    BulkRateCalculationResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session


def get_yield_curve_service(db: Session = Depends(get_db)):
    """Yield curve service dependency"""
    return YieldCurveService(db)


@router.get("/", response_model=YieldCurveListResponse)
async def list_yield_curves(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    currency: Optional[str] = Query(None, description="Filter by currency (e.g., USD, EUR)"),
    curve_type: Optional[str] = Query(None, description="Filter by curve type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in curve name and description"),
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    List all yield curves with optional filtering and pagination
    
    Returns a paginated list of yield curves with summary information.
    """
    try:
        # Build query
        query = service.session.query(YieldCurveModel)
        
        # Apply filters
        if currency:
            query = query.filter(YieldCurveModel.currency == currency.upper())
        
        if curve_type:
            query = query.filter(YieldCurveModel.curve_type == curve_type.upper())
        
        if is_active is not None:
            query = query.filter(YieldCurveModel.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (YieldCurveModel.curve_name.ilike(search_term)) |
                (YieldCurveModel.description.ilike(search_term))
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        curves_query = query.order_by(
            YieldCurveModel.analysis_date.desc(),
            YieldCurveModel.curve_name
        ).offset(skip).limit(limit)
        
        curves = curves_query.all()
        
        # Build response with summary data
        curve_summaries = []
        for curve in curves:
            rate_count = len(curve.rates)
            
            # Calculate maturity range
            if curve.rates:
                min_months = min(rate.maturity_month for rate in curve.rates)
                max_months = max(rate.maturity_month for rate in curve.rates)
                
                # Convert to readable format
                min_display = f"{min_months}M" if min_months < 12 else f"{min_months//12}Y"
                max_display = f"{max_months}M" if max_months < 12 else f"{max_months//12}Y"
                maturity_range = f"{min_display} - {max_display}"
            else:
                maturity_range = "No rates"
            
            curve_summaries.append(YieldCurveSummaryResponse(
                curve_id=curve.curve_id,
                curve_name=curve.curve_name,
                curve_type=curve.curve_type,
                currency=curve.currency,
                analysis_date=curve.analysis_date,
                description=curve.description,
                is_active=curve.is_active,
                rate_count=rate_count,
                maturity_range=maturity_range
            ))
        
        return YieldCurveListResponse(
            curves=curve_summaries,
            total_count=total_count,
            page=(skip // limit) + 1,
            per_page=limit,
            has_next=(skip + limit) < total_count,
            has_prev=skip > 0
        )
        
    except Exception as e:
        logger.error(f"Error listing yield curves: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=YieldCurveResponse, status_code=201)
async def create_yield_curve(
    curve_data: YieldCurveCreate,
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Create a new yield curve
    
    Creates a yield curve with the provided rates and automatically calculates
    interpolated rates and forward rates using VBA-equivalent logic.
    """
    try:
        # Convert rates to dictionary format expected by YieldCurve
        rate_dict = {rate.maturity_month: rate.spot_rate for rate in curve_data.rates}
        
        # Create yield curve using service
        yield_curve = service.create_yield_curve(
            name=curve_data.curve_name,
            analysis_date=curve_data.analysis_date,
            rate_dict=rate_dict,
            curve_type=curve_data.curve_type,
            currency=curve_data.currency,
            description=curve_data.description
        )
        
        # Return the created curve with all related data
        return await get_yield_curve(curve_id=yield_curve.curve_id, service=service)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        service.session.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Yield curve with this name already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except Exception as e:
        logger.error(f"Error creating yield curve: {e}")
        service.session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/currencies", response_model=List[str])
async def get_available_currencies(
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """Get list of available currencies in the system"""
    try:
        currencies = service.session.query(YieldCurveModel.currency).distinct().all()
        return [currency[0] for currency in currencies if currency[0]]
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/curve-types", response_model=List[str])
async def get_available_curve_types(
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """Get list of available curve types in the system"""
    try:
        curve_types = service.session.query(YieldCurveModel.curve_type).distinct().all()
        return [curve_type[0] for curve_type in curve_types if curve_type[0]]
    except Exception as e:
        logger.error(f"Error getting curve types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{curve_id}", response_model=YieldCurveResponse)
async def get_yield_curve(
    curve_id: int = Path(..., description="Yield curve ID"),
    include_forwards: bool = Query(True, description="Include forward rates in response"),
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Get a specific yield curve by ID
    
    Returns detailed information about the yield curve including all rates,
    forward rates, and metadata.
    """
    try:
        # Get curve from database
        curve_model = service.session.query(YieldCurveModel).filter_by(
            curve_id=curve_id
        ).first()
        
        if not curve_model:
            raise HTTPException(status_code=404, detail="Yield curve not found")
        
        # Build response
        response_data = {
            "curve_id": curve_model.curve_id,
            "curve_name": curve_model.curve_name,
            "curve_type": curve_model.curve_type,
            "currency": curve_model.currency,
            "analysis_date": curve_model.analysis_date,
            "base_date": curve_model.base_date,
            "last_month": curve_model.last_month,
            "description": curve_model.description,
            "is_active": curve_model.is_active,
            "created_date": curve_model.created_date.date() if curve_model.created_date else None,
            "updated_date": curve_model.updated_date.date() if curve_model.updated_date else None,
            "rates": [
                {
                    "rate_id": rate.rate_id,
                    "maturity_month": rate.maturity_month,
                    "maturity_date": rate.maturity_date,
                    "spot_rate": float(rate.spot_rate),
                    "is_interpolated": rate.is_interpolated,
                    "source": rate.source
                }
                for rate in sorted(curve_model.rates, key=lambda x: x.maturity_month)
            ],
            "forward_rates": []
        }
        
        # Include forward rates if requested
        if include_forwards:
            response_data["forward_rates"] = [
                {
                    "forward_id": fwd.forward_id,
                    "forward_date": fwd.forward_date,
                    "period_start_date": fwd.period_start_date,
                    "period_months": fwd.period_months,
                    "forward_rate": float(fwd.forward_rate),
                    "calculation_method": fwd.calculation_method
                }
                for fwd in sorted(curve_model.forward_rates, key=lambda x: x.forward_date)
            ]
        
        return YieldCurveResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting yield curve {curve_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{curve_id}", response_model=YieldCurveResponse)
async def update_yield_curve(
    curve_id: int = Path(..., description="Yield curve ID"),
    curve_data: YieldCurveUpdate = ...,
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Update an existing yield curve
    
    Updates the yield curve and recalculates interpolated rates and forward rates
    if the rate structure has changed.
    """
    try:
        # Check if curve exists
        curve_model = service.session.query(YieldCurveModel).filter_by(
            curve_id=curve_id
        ).first()
        
        if not curve_model:
            raise HTTPException(status_code=404, detail="Yield curve not found")
        
        # Update basic fields
        update_fields = curve_data.dict(exclude_unset=True)
        
        # Handle rates update separately if provided
        if 'rates' in update_fields:
            rates_data = update_fields.pop('rates')
            
            # Delete existing rates
            service.session.query(YieldCurveRateModel).filter_by(
                curve_id=curve_id
            ).delete()
            
            # Delete existing forward rates
            service.session.query(ForwardRateModel).filter_by(
                curve_id=curve_id
            ).delete()
            
            # Recreate yield curve with new rates
            rate_dict = {rate.maturity_month: rate.spot_rate for rate in rates_data}
            
            # Load existing curve and update with new rates
            existing_curve = service.load_yield_curve(
                curve_model.curve_name,
                curve_model.analysis_date
            )
            
            if existing_curve:
                existing_curve.setup(
                    curve_model.curve_name,
                    update_fields.get('analysis_date', curve_model.analysis_date),
                    rate_dict
                )
                existing_curve.save_to_database(
                    curve_model.curve_type,
                    curve_model.currency,
                    update_fields.get('description', curve_model.description)
                )
        
        # Update other fields
        for field, value in update_fields.items():
            if hasattr(curve_model, field):
                setattr(curve_model, field, value)
        
        # Update timestamp
        curve_model.updated_date = date.today()
        
        service.session.commit()
        
        # Return updated curve
        return await get_yield_curve(curve_id=curve_id, service=service)
        
    except HTTPException:
        raise
    except ValueError as e:
        service.session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating yield curve {curve_id}: {e}")
        service.session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{curve_id}", status_code=204)
async def delete_yield_curve(
    curve_id: int = Path(..., description="Yield curve ID"),
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Delete a yield curve
    
    Soft deletes the yield curve by setting is_active to false.
    This preserves historical data while removing it from active use.
    """
    try:
        # Check if curve exists
        curve_model = service.session.query(YieldCurveModel).filter_by(
            curve_id=curve_id
        ).first()
        
        if not curve_model:
            raise HTTPException(status_code=404, detail="Yield curve not found")
        
        # Soft delete by setting is_active to False
        curve_model.is_active = False
        curve_model.updated_date = date.today()
        
        service.session.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting yield curve {curve_id}: {e}")
        service.session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate-rate", response_model=YieldCurveRateCalculationResponse)
async def calculate_spot_rate(
    request: YieldCurveRateCalculationRequest,
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Calculate spot rate for a specific maturity using yield curve interpolation
    
    Uses the same VBA-equivalent interpolation logic as the original system.
    """
    try:
        # Load yield curve
        curve_model = service.session.query(YieldCurveModel).filter_by(
            curve_id=request.curve_id,
            is_active=True
        ).first()
        
        if not curve_model:
            raise HTTPException(status_code=404, detail="Yield curve not found")
        
        # Load the curve for calculations
        yield_curve = service.load_yield_curve(
            curve_model.curve_name,
            curve_model.analysis_date
        )
        
        if not yield_curve:
            raise HTTPException(status_code=404, detail="Could not load yield curve data")
        
        # Calculate the spot rate
        spot_rate = yield_curve.spot_rate(request.calculation_date, request.maturity_months)
        
        # Determine if this rate was interpolated
        original_rates = {rate.maturity_month: float(rate.spot_rate) 
                         for rate in curve_model.rates if not rate.is_interpolated}
        is_interpolated = request.maturity_months not in original_rates
        
        return YieldCurveRateCalculationResponse(
            curve_id=request.curve_id,
            curve_name=curve_model.curve_name,
            calculation_date=request.calculation_date,
            maturity_months=request.maturity_months,
            spot_rate=spot_rate,
            is_interpolated=is_interpolated,
            calculation_method="VBA_EQUIVALENT_LINEAR_INTERPOLATION"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating spot rate: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate-bulk-rates", response_model=BulkRateCalculationResponse)
async def calculate_bulk_rates(
    request: BulkRateCalculationRequest,
    service: YieldCurveService = Depends(get_yield_curve_service)
):
    """
    Calculate spot rates for multiple maturities in a single request
    
    More efficient than multiple single rate calculations.
    """
    try:
        # Load yield curve
        curve_model = service.session.query(YieldCurveModel).filter_by(
            curve_id=request.curve_id,
            is_active=True
        ).first()
        
        if not curve_model:
            raise HTTPException(status_code=404, detail="Yield curve not found")
        
        # Load the curve for calculations
        yield_curve = service.load_yield_curve(
            curve_model.curve_name,
            curve_model.analysis_date
        )
        
        if not yield_curve:
            raise HTTPException(status_code=404, detail="Could not load yield curve data")
        
        # Get original (non-interpolated) rates for comparison
        original_rates = {rate.maturity_month: float(rate.spot_rate) 
                         for rate in curve_model.rates if not rate.is_interpolated}
        
        # Calculate all requested rates
        calculated_rates = []
        for maturity_months in request.maturity_months_list:
            spot_rate = yield_curve.spot_rate(request.calculation_date, maturity_months)
            is_interpolated = maturity_months not in original_rates
            
            calculated_rates.append({
                "maturity_months": maturity_months,
                "spot_rate": spot_rate,
                "is_interpolated": is_interpolated
            })
        
        return BulkRateCalculationResponse(
            curve_id=request.curve_id,
            curve_name=curve_model.curve_name,
            calculation_date=request.calculation_date,
            rates=calculated_rates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating bulk rates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")