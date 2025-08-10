"""
Scenario Analysis API Endpoints
Handles MAG scenario data, custom scenarios, and scenario-based analytics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....services.data_integration import DataIntegrationService
from ....services.scenario_service import ScenarioService
from ....schemas.scenarios import (
    ScenarioResponse,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioParametersResponse,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse
)

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_integration_service():
    """Data integration service dependency"""
    return DataIntegrationService()

def get_scenario_service():
    """Scenario analysis service dependency"""
    return ScenarioService()

@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(
    scenario_type: Optional[str] = Query(None, regex="^(MAG|custom|regulatory)$"),
    active_only: bool = Query(True),
    integration_service: DataIntegrationService = Depends(get_integration_service),
    db: Session = Depends(get_db)
):
    """List available scenarios"""
    try:
        # Get MAG scenarios from migration database
        mag_scenarios = integration_service.get_available_scenarios()
        
        # Get custom scenarios from operational database
        custom_scenarios = []  # Implementation will query scenarios table
        
        all_scenarios = []
        
        # Add MAG scenarios
        for scenario_name in mag_scenarios:
            all_scenarios.append(ScenarioResponse(
                id=scenario_name,
                name=scenario_name,
                scenario_type="MAG",
                description=f"MAG {scenario_name} scenario parameters",
                is_active=True,
                created_date=None,  # Not available for MAG scenarios
                parameter_count=len(integration_service.get_scenario_parameters(scenario_name))
            ))
        
        # Filter by type if specified
        if scenario_type:
            all_scenarios = [s for s in all_scenarios if s.scenario_type == scenario_type]
        
        # Filter by active status
        if active_only:
            all_scenarios = [s for s in all_scenarios if s.is_active]
        
        return all_scenarios
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scenarios: {str(e)}")

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    integration_service: DataIntegrationService = Depends(get_integration_service),
    db: Session = Depends(get_db)
):
    """Get a specific scenario by ID"""
    try:
        # Check if it's a MAG scenario
        mag_scenarios = integration_service.get_available_scenarios()
        
        if scenario_id in mag_scenarios:
            parameters = integration_service.get_scenario_parameters(scenario_id)
            return ScenarioResponse(
                id=scenario_id,
                name=scenario_id,
                scenario_type="MAG",
                description=f"MAG {scenario_id} scenario parameters",
                is_active=True,
                parameter_count=len(parameters)
            )
        
        # Otherwise, check custom scenarios in operational database
        # Implementation will query scenarios table
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scenario: {str(e)}")

@router.get("/{scenario_id}/parameters", response_model=ScenarioParametersResponse)
async def get_scenario_parameters(
    scenario_id: str,
    category: Optional[str] = Query(None),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get parameters for a specific scenario"""
    try:
        parameters = integration_service.get_scenario_parameters(scenario_id)
        
        if not parameters:
            raise HTTPException(status_code=404, detail="Scenario parameters not found")
        
        # Filter by category if specified
        if category:
            parameters = [p for p in parameters if p.get('category') == category]
        
        return ScenarioParametersResponse(
            scenario_id=scenario_id,
            parameter_count=len(parameters),
            parameters=parameters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scenario parameters: {str(e)}")

@router.post("/", response_model=ScenarioResponse)
async def create_custom_scenario(
    scenario: ScenarioCreate,
    scenario_service: ScenarioService = Depends(get_scenario_service),
    db: Session = Depends(get_db)
):
    """Create a new custom scenario"""
    try:
        result = scenario_service.create_scenario(
            name=scenario.name,
            description=scenario.description,
            scenario_type=scenario.scenario_type,
            parameters=scenario.parameters
        )
        
        return ScenarioResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")

@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    scenario_update: ScenarioUpdate,
    scenario_service: ScenarioService = Depends(get_scenario_service),
    db: Session = Depends(get_db)
):
    """Update an existing custom scenario"""
    try:
        result = scenario_service.update_scenario(
            scenario_id=scenario_id,
            updates=scenario_update.dict(exclude_unset=True)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return ScenarioResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scenario: {str(e)}")

@router.post("/{scenario_id}/analyze", response_model=ScenarioAnalysisResponse)
async def run_scenario_analysis(
    scenario_id: str,
    analysis_request: ScenarioAnalysisRequest,
    scenario_service: ScenarioService = Depends(get_scenario_service),
    db: Session = Depends(get_db)
):
    """Run comprehensive scenario analysis"""
    try:
        results = scenario_service.run_scenario_analysis(
            scenario_id=scenario_id,
            deal_ids=analysis_request.deal_ids,
            analysis_type=analysis_request.analysis_type,
            time_horizon=analysis_request.time_horizon,
            custom_parameters=analysis_request.custom_parameters
        )
        
        return ScenarioAnalysisResponse(**results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario analysis failed: {str(e)}")

@router.post("/compare")
async def compare_scenarios(
    scenario_ids: List[str] = Query(..., min_items=2, max_items=5),
    deal_id: str = Query(...),
    metrics: List[str] = Query(["portfolio_value", "risk_metrics", "cash_flows"]),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    db: Session = Depends(get_db)
):
    """Compare multiple scenarios for a deal"""
    try:
        comparison = scenario_service.compare_scenarios(
            scenario_ids=scenario_ids,
            deal_id=deal_id,
            metrics=metrics
        )
        
        return {
            "deal_id": deal_id,
            "scenarios_compared": scenario_ids,
            "metrics": metrics,
            "comparison_results": comparison,
            "summary": {
                "best_scenario": comparison.get("best_performing"),
                "worst_scenario": comparison.get("worst_performing"),
                "recommendation": comparison.get("recommendation")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario comparison failed: {str(e)}")

@router.get("/categories/available")
async def get_parameter_categories(
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get available parameter categories across all scenarios"""
    try:
        categories = integration_service.get_scenario_parameter_categories()
        
        return {
            "categories": categories,
            "category_descriptions": {
                "Economic": "Macroeconomic scenario parameters",
                "Market": "Market condition parameters", 
                "Credit": "Credit environment parameters",
                "Liquidity": "Liquidity scenario parameters",
                "Operational": "Operational scenario parameters"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch parameter categories: {str(e)}")

@router.get("/mag/versions")
async def get_mag_versions(
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get available MAG scenario versions"""
    try:
        versions = integration_service.get_available_scenarios()
        
        return {
            "mag_versions": versions,
            "total_versions": len(versions),
            "description": "Available MAG scenario versions with parameter sets"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch MAG versions: {str(e)}")

@router.post("/{scenario_id}/export")
async def export_scenario(
    scenario_id: str,
    export_format: str = Query("json", regex="^(json|excel|csv)$"),
    include_analysis: bool = Query(False),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Export scenario parameters and analysis"""
    try:
        export_data = integration_service.export_scenario_data(
            scenario_id=scenario_id,
            format=export_format,
            include_analysis=include_analysis
        )
        
        return {
            "scenario_id": scenario_id,
            "export_format": export_format,
            "data_size": len(str(export_data)),
            "download_url": f"/scenarios/{scenario_id}/download/{export_format}",
            "expires_at": "2024-12-31T23:59:59Z"  # Implementation will set proper expiry
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario export failed: {str(e)}")

@router.delete("/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    scenario_service: ScenarioService = Depends(get_scenario_service),
    db: Session = Depends(get_db)
):
    """Delete a custom scenario (soft delete)"""
    try:
        success = scenario_service.delete_scenario(scenario_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return {"message": f"Scenario {scenario_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scenario: {str(e)}")