"""
Concentration Test Threshold Management API Endpoints
RESTful API for database-driven concentration test threshold management
"""

from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.auth import User
from ....repositories.concentration_threshold_repository import ConcentrationThresholdRepository
from ....services.concentration_threshold_service import (
    ConcentrationThresholdService, ConcentrationThresholdCache
)
from ....core.database import get_redis
import redis


router = APIRouter()


# ========================================
# Pydantic Schemas
# ========================================

class ThresholdOverrideRequest(BaseModel):
    """Request to create or update threshold override"""
    threshold_value: float
    effective_date: date
    expiry_date: Optional[date] = None
    mag_version: Optional[str] = None
    rating_agency: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('threshold_value')
    def validate_threshold_value(cls, v):
        if v < 0:
            raise ValueError('Threshold value must be non-negative')
        return v
    
    @validator('expiry_date')
    def validate_expiry_date(cls, v, values):
        if v and 'effective_date' in values and v <= values['effective_date']:
            raise ValueError('Expiry date must be after effective date')
        return v
    
    @validator('mag_version')
    def validate_mag_version(cls, v):
        if v and v not in ['MAG6', 'MAG14', 'MAG17']:
            raise ValueError('MAG version must be one of: MAG6, MAG14, MAG17')
        return v


class ThresholdResponse(BaseModel):
    """Response schema for threshold configuration"""
    test_id: int
    test_number: int
    test_name: str
    test_category: str
    result_type: str
    threshold_value: float
    threshold_source: str
    is_custom_override: bool
    effective_date: date
    expiry_date: Optional[date] = None
    mag_version: Optional[str] = None
    default_threshold: Optional[float] = None


class ThresholdHistoryResponse(BaseModel):
    """Response schema for threshold history"""
    id: int
    threshold_value: float
    effective_date: date
    expiry_date: Optional[date] = None
    mag_version: Optional[str] = None
    rating_agency: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: str
    updated_at: str


class TestDefinitionResponse(BaseModel):
    """Response schema for test definition"""
    test_id: int
    test_number: int
    test_name: str
    test_description: Optional[str] = None
    test_category: str
    result_type: str
    default_threshold: Optional[float] = None
    calculation_method: Optional[str] = None
    is_active: bool


class ConcentrationTestResultResponse(BaseModel):
    """Response schema for enhanced concentration test results"""
    test_id: int
    test_number: int
    test_name: str
    threshold: float
    result: float
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    pass_fail_status: str
    excess_amount: Optional[float] = None
    threshold_source: str
    is_custom_override: bool
    effective_date: str
    mag_version: Optional[str] = None
    comments: Optional[str] = None


class ConcentrationTestSummaryResponse(BaseModel):
    """Response schema for test execution summary"""
    deal_id: str
    analysis_date: str
    test_results: List[ConcentrationTestResultResponse]
    summary: Dict[str, Any]


# ========================================
# Dependency Injection
# ========================================

def get_threshold_service(
    db: Session = Depends(get_db),
    redis_client: Optional[redis.Redis] = Depends(get_redis)
) -> ConcentrationThresholdService:
    """Get threshold service with dependencies"""
    repository = ConcentrationThresholdRepository(db)
    cache = ConcentrationThresholdCache(redis_client) if redis_client else None
    return ConcentrationThresholdService(repository, cache)


def require_threshold_management_permissions(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user has permissions to manage thresholds"""
    if current_user.role not in ['ADMIN', 'MANAGER']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage concentration test thresholds"
        )
    return current_user


# ========================================
# Test Definition Endpoints
# ========================================

@router.get("/test-definitions", response_model=List[TestDefinitionResponse])
async def get_test_definitions(
    category: Optional[str] = Query(None, description="Filter by test category"),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get all concentration test definitions"""
    try:
        if category:
            definitions = await threshold_service.repository.get_tests_by_category(category)
        else:
            definitions = await threshold_service.repository.get_all_test_definitions()
        
        return [
            TestDefinitionResponse(
                test_id=test_def.test_id,
                test_number=test_def.test_number,
                test_name=test_def.test_name,
                test_description=test_def.test_description,
                test_category=test_def.test_category,
                result_type=test_def.result_type,
                default_threshold=float(test_def.default_threshold) if test_def.default_threshold else None,
                calculation_method=test_def.calculation_method,
                is_active=test_def.is_active
            )
            for test_def in definitions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get test definitions: {str(e)}")


@router.get("/test-definitions/{test_id}", response_model=TestDefinitionResponse)
async def get_test_definition(
    test_id: int = Path(..., description="Test definition ID"),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get specific test definition by ID"""
    try:
        test_def = await threshold_service.repository.get_test_definition(test_id)
        if not test_def:
            raise HTTPException(status_code=404, detail="Test definition not found")
        
        return TestDefinitionResponse(
            test_id=test_def.test_id,
            test_number=test_def.test_number,
            test_name=test_def.test_name,
            test_description=test_def.test_description,
            test_category=test_def.test_category,
            result_type=test_def.result_type,
            default_threshold=float(test_def.default_threshold) if test_def.default_threshold else None,
            calculation_method=test_def.calculation_method,
            is_active=test_def.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get test definition: {str(e)}")


# ========================================
# Deal Threshold Management Endpoints
# ========================================

@router.get("/deals/{deal_id}/thresholds", response_model=List[ThresholdResponse])
async def get_deal_thresholds(
    deal_id: str = Path(..., description="CLO Deal ID"),
    analysis_date: Optional[date] = Query(default=date(2016, 3, 23), description="Analysis date for threshold resolution"),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get all concentration test thresholds for a deal"""
    try:
        threshold_configs = await threshold_service.get_deal_thresholds(deal_id, analysis_date)
        
        return [
            ThresholdResponse(
                test_id=config.test_id,
                test_number=config.test_number,
                test_name=config.test_name,
                test_category=config.test_category,
                result_type=config.result_type,
                threshold_value=config.threshold_value,
                threshold_source=config.threshold_source,
                is_custom_override=config.is_custom_override,
                effective_date=date.fromisoformat(config.effective_date),
                expiry_date=date.fromisoformat(config.expiry_date) if config.expiry_date else None,
                mag_version=config.mag_version
            )
            for config in threshold_configs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deal thresholds: {str(e)}")


@router.put("/deals/{deal_id}/thresholds/{test_id}")
async def update_deal_threshold(
    deal_id: str = Path(..., description="CLO Deal ID"),
    test_id: int = Path(..., description="Concentration Test ID"),
    threshold_request: ThresholdOverrideRequest = Body(...),
    current_user: User = Depends(require_threshold_management_permissions),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Create or update deal-specific threshold override"""
    try:
        threshold_config = await threshold_service.create_threshold_override(
            deal_id=deal_id,
            test_id=test_id,
            threshold_value=Decimal(str(threshold_request.threshold_value)),
            effective_date=threshold_request.effective_date,
            user_id=current_user.id,
            expiry_date=threshold_request.expiry_date,
            mag_version=threshold_request.mag_version,
            notes=threshold_request.notes
        )
        
        return {
            "message": "Threshold updated successfully",
            "threshold_config": {
                "test_id": threshold_config.test_id,
                "test_name": threshold_config.test_name,
                "threshold_value": threshold_config.threshold_value,
                "effective_date": threshold_config.effective_date,
                "threshold_source": threshold_config.threshold_source
            }
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update threshold: {str(e)}")


@router.get("/deals/{deal_id}/thresholds/{test_id}/history", response_model=List[ThresholdHistoryResponse])
async def get_threshold_history(
    deal_id: str = Path(..., description="CLO Deal ID"),
    test_id: int = Path(..., description="Concentration Test ID"),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get historical changes for a specific threshold"""
    try:
        history = await threshold_service.get_threshold_history(deal_id, test_id)
        
        return [
            ThresholdHistoryResponse(
                id=entry['id'],
                threshold_value=entry['threshold_value'],
                effective_date=date.fromisoformat(entry['effective_date']),
                expiry_date=date.fromisoformat(entry['expiry_date']) if entry['expiry_date'] else None,
                mag_version=entry['mag_version'],
                rating_agency=entry['rating_agency'],
                notes=entry['notes'],
                created_by=entry['created_by'],
                created_at=entry['created_at'],
                updated_at=entry['updated_at']
            )
            for entry in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threshold history: {str(e)}")


# ========================================
# Enhanced Concentration Test Execution Endpoints
# ========================================

@router.get("/deals/{deal_id}/concentration-tests", response_model=ConcentrationTestSummaryResponse)
async def get_concentration_tests_with_thresholds(
    deal_id: str = Path(..., description="CLO Deal ID"),
    analysis_date: Optional[date] = Query(default=date(2016, 3, 23), description="Analysis date for test execution"),
    include_threshold_details: bool = Query(default=True, description="Include detailed threshold information"),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get concentration test results with enhanced threshold details"""
    try:
        if include_threshold_details:
            # Get results with complete threshold details
            result = await threshold_service.get_test_results_with_thresholds(deal_id, analysis_date)
            
            test_results = [
                ConcentrationTestResultResponse(**test_result)
                for test_result in result['test_results']
            ]
            
            return ConcentrationTestSummaryResponse(
                deal_id=result['deal_id'],
                analysis_date=result['analysis_date'],
                test_results=test_results,
                summary=result['summary']
            )
        else:
            # Get basic execution results
            executions = await threshold_service.repository.get_test_executions(deal_id, analysis_date)
            
            test_results = [
                ConcentrationTestResultResponse(
                    test_id=execution.test_id,
                    test_number=0,  # Would need to join with test definition
                    test_name="",   # Would need to join with test definition
                    threshold=float(execution.threshold_used),
                    result=float(execution.calculated_value),
                    numerator=float(execution.numerator) if execution.numerator else None,
                    denominator=float(execution.denominator) if execution.denominator else None,
                    pass_fail_status=execution.pass_fail_status,
                    excess_amount=float(execution.excess_amount) if execution.excess_amount else None,
                    threshold_source=execution.threshold_source,
                    is_custom_override=False,
                    effective_date=analysis_date.isoformat(),
                    comments=execution.comments
                )
                for execution in executions
            ]
            
            summary = {
                'total_tests': len(test_results),
                'passed_tests': sum(1 for r in test_results if r.pass_fail_status == 'PASS'),
                'failed_tests': sum(1 for r in test_results if r.pass_fail_status == 'FAIL'),
                'na_tests': sum(1 for r in test_results if r.pass_fail_status == 'N/A')
            }
            
            return ConcentrationTestSummaryResponse(
                deal_id=deal_id,
                analysis_date=analysis_date.isoformat(),
                test_results=test_results,
                summary=summary
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get concentration test results: {str(e)}")


# ========================================
# System Management Endpoints
# ========================================

@router.get("/statistics")
async def get_threshold_statistics(
    current_user: User = Depends(get_current_user),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Get concentration test threshold system statistics"""
    try:
        stats = await threshold_service.get_system_statistics()
        return {
            "concentration_threshold_statistics": stats,
            "timestamp": date.today().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.delete("/deals/{deal_id}/cache")
async def invalidate_deal_cache(
    deal_id: str = Path(..., description="CLO Deal ID"),
    current_user: User = Depends(require_threshold_management_permissions),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Invalidate cached data for a specific deal"""
    try:
        if threshold_service.cache:
            await threshold_service.cache.invalidate_deal_cache(deal_id)
            return {"message": f"Cache invalidated for deal {deal_id}"}
        else:
            return {"message": "Caching not enabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


# ========================================
# Bulk Operations Endpoints
# ========================================

@router.post("/deals/{deal_id}/thresholds/bulk-update")
async def bulk_update_thresholds(
    deal_id: str = Path(..., description="CLO Deal ID"),
    threshold_updates: List[Dict[str, Any]] = Body(..., description="List of threshold updates"),
    current_user: User = Depends(require_threshold_management_permissions),
    threshold_service: ConcentrationThresholdService = Depends(get_threshold_service)
):
    """Bulk update multiple thresholds for a deal"""
    try:
        results = []
        errors = []
        
        for update in threshold_updates:
            try:
                threshold_config = await threshold_service.create_threshold_override(
                    deal_id=deal_id,
                    test_id=update['test_id'],
                    threshold_value=Decimal(str(update['threshold_value'])),
                    effective_date=date.fromisoformat(update['effective_date']),
                    user_id=current_user.id,
                    expiry_date=date.fromisoformat(update['expiry_date']) if update.get('expiry_date') else None,
                    mag_version=update.get('mag_version'),
                    notes=update.get('notes')
                )
                results.append({
                    "test_id": threshold_config.test_id,
                    "status": "success",
                    "message": f"Threshold updated for {threshold_config.test_name}"
                })
            except Exception as e:
                errors.append({
                    "test_id": update.get('test_id', 'unknown'),
                    "status": "error",
                    "message": str(e)
                })
        
        return {
            "message": f"Bulk update completed: {len(results)} successful, {len(errors)} errors",
            "results": results,
            "errors": errors
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk update: {str(e)}")