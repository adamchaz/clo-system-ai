"""
Waterfall Calculation API Endpoints
Handles waterfall calculations, payment distributions, and cash flow modeling
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....services.waterfall_service import WaterfallService
from ....schemas.waterfall import (
    WaterfallCalculationRequest,
    WaterfallCalculationResponse,
    PaymentSequenceResponse,
    CashFlowProjectionRequest,
    CashFlowProjectionResponse
)

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_waterfall_service():
    """Waterfall calculation service dependency"""
    return WaterfallService()

@router.post("/calculate", response_model=WaterfallCalculationResponse)
async def calculate_waterfall(
    request: WaterfallCalculationRequest,
    waterfall_service: WaterfallService = Depends(get_waterfall_service),
    db: Session = Depends(get_db)
):
    """Calculate waterfall distribution for a payment period"""
    try:
        result = waterfall_service.calculate_waterfall(
            deal_id=request.deal_id,
            payment_date=request.payment_date,
            available_funds=request.available_funds,
            principal_collections=request.principal_collections,
            interest_collections=request.interest_collections
        )
        
        return WaterfallCalculationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Waterfall calculation failed: {str(e)}")

@router.get("/{deal_id}/payment-sequence", response_model=PaymentSequenceResponse)
async def get_payment_sequence(
    deal_id: str,
    payment_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get payment sequence configuration for a CLO deal"""
    try:
        # Implementation will query waterfall_configurations table
        # For now, return placeholder structure
        sequence = {
            "deal_id": deal_id,
            "payment_date": payment_date or date.today(),
            "sequence": [
                {"priority": 1, "type": "fees", "description": "Management fees"},
                {"priority": 2, "type": "senior_interest", "description": "Senior tranche interest"},
                {"priority": 3, "type": "mezzanine_interest", "description": "Mezzanine tranche interest"},
                {"priority": 4, "type": "senior_principal", "description": "Senior tranche principal"},
                {"priority": 5, "type": "subordinate_payments", "description": "Subordinate payments"},
                {"priority": 6, "type": "equity_distribution", "description": "Equity distribution"}
            ]
        }
        
        return PaymentSequenceResponse(**sequence)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch payment sequence: {str(e)}")

@router.post("/{deal_id}/cash-flow-projection", response_model=CashFlowProjectionResponse)
async def project_cash_flows(
    deal_id: str,
    request: CashFlowProjectionRequest,
    waterfall_service: WaterfallService = Depends(get_waterfall_service),
    db: Session = Depends(get_db)
):
    """Generate cash flow projections for a CLO deal"""
    try:
        projection = waterfall_service.project_cash_flows(
            deal_id=deal_id,
            start_date=request.start_date,
            end_date=request.end_date,
            scenario=request.scenario,
            assumptions=request.assumptions
        )
        
        return CashFlowProjectionResponse(**projection)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cash flow projection failed: {str(e)}")

@router.get("/{deal_id}/historical-payments")
async def get_historical_payments(
    deal_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get historical payment data for a CLO deal"""
    try:
        # Implementation will query historical payment records
        return {
            "deal_id": deal_id,
            "payments": [],
            "summary": {
                "total_payments": 0,
                "total_principal": 0,
                "total_interest": 0,
                "average_payment": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical payments: {str(e)}")

@router.post("/{deal_id}/stress-test")
async def run_stress_test(
    deal_id: str,
    scenarios: List[dict],
    waterfall_service: WaterfallService = Depends(get_waterfall_service),
    db: Session = Depends(get_db)
):
    """Run stress testing scenarios on waterfall calculations"""
    try:
        results = waterfall_service.run_stress_tests(
            deal_id=deal_id,
            scenarios=scenarios
        )
        
        return {
            "deal_id": deal_id,
            "scenarios_tested": len(scenarios),
            "results": results,
            "summary": {
                "worst_case": results[0] if results else None,
                "best_case": results[-1] if results else None,
                "base_case": next((r for r in results if r.get('scenario_name') == 'base'), None)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress testing failed: {str(e)}")

@router.get("/{deal_id}/trigger-impact")
async def analyze_trigger_impact(
    deal_id: str,
    trigger_breach_scenario: str = Query(...),
    db: Session = Depends(get_db)
):
    """Analyze impact of trigger breaches on waterfall"""
    try:
        # Implementation will simulate trigger breach scenarios
        return {
            "deal_id": deal_id,
            "scenario": trigger_breach_scenario,
            "impact": {
                "payment_redirection": {},
                "affected_tranches": [],
                "estimated_loss": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trigger impact analysis failed: {str(e)}")

@router.get("/configuration/templates")
async def get_waterfall_templates():
    """Get available waterfall configuration templates"""
    try:
        templates = [
            {
                "name": "CLO 2.0 Standard",
                "description": "Standard CLO 2.0 waterfall structure",
                "version": "2.0",
                "features": ["oc_triggers", "ic_triggers", "reinvestment_period"]
            },
            {
                "name": "CLO 3.0 Enhanced",
                "description": "Enhanced CLO 3.0 with additional protections",
                "version": "3.0", 
                "features": ["enhanced_triggers", "dynamic_hedging", "esg_compliance"]
            }
        ]
        
        return {"templates": templates}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch waterfall templates: {str(e)}")

@router.post("/validate-configuration")
async def validate_waterfall_config(
    config: dict,
    db: Session = Depends(get_db)
):
    """Validate a waterfall configuration"""
    try:
        # Implementation will validate configuration structure
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {str(e)}")