"""
Risk Analytics API Endpoints
Handles risk calculations, correlation analysis, and portfolio risk metrics
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database_config import db_config
from ....services.data_integration import DataIntegrationService
from ....services.risk_service import RiskAnalyticsService
from ....schemas.risk import (
    RiskMetricsResponse,
    CorrelationMatrixResponse,
    ConcentrationAnalysisResponse,
    StressTestRequest,
    StressTestResponse,
    RiskReportRequest,
    RiskReportResponse
)

router = APIRouter()

def get_db():
    """Database dependency"""
    with db_config.get_db_session('postgresql') as session:
        yield session

def get_integration_service():
    """Data integration service dependency"""
    return DataIntegrationService()

def get_risk_service():
    """Risk analytics service dependency"""
    return RiskAnalyticsService()

@router.get("/{deal_id}/metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    deal_id: str,
    as_of_date: Optional[str] = Query(None),
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Get comprehensive risk metrics for a CLO deal"""
    try:
        metrics = risk_service.calculate_portfolio_risk_metrics(
            deal_id=deal_id,
            as_of_date=as_of_date
        )
        
        return RiskMetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk metrics: {str(e)}")

@router.get("/{deal_id}/correlation-matrix", response_model=CorrelationMatrixResponse)
async def get_correlation_matrix(
    deal_id: str,
    integration_service: DataIntegrationService = Depends(get_integration_service),
    db: Session = Depends(get_db)
):
    """Get correlation matrix for assets in a CLO deal"""
    try:
        # Get deal assets first
        deal_assets = []  # Implementation will query deal_assets table
        
        # Build correlation matrix from migrated correlation data
        matrix = integration_service.build_correlation_matrix(deal_assets)
        
        return CorrelationMatrixResponse(
            deal_id=deal_id,
            asset_count=len(deal_assets),
            correlation_matrix=matrix,
            eigenvalues=[],  # Will be calculated
            principal_components=[]  # Will be calculated
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build correlation matrix: {str(e)}")

@router.get("/{deal_id}/concentration", response_model=ConcentrationAnalysisResponse)
async def analyze_concentration(
    deal_id: str,
    dimension: str = Query("sector", regex="^(sector|industry|rating|geography)$"),
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Analyze portfolio concentration by various dimensions"""
    try:
        analysis = risk_service.analyze_concentration(
            deal_id=deal_id,
            dimension=dimension
        )
        
        return ConcentrationAnalysisResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concentration analysis failed: {str(e)}")

@router.post("/{deal_id}/stress-test", response_model=StressTestResponse)
async def run_stress_test(
    deal_id: str,
    request: StressTestRequest,
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Run comprehensive stress testing on a CLO portfolio"""
    try:
        results = risk_service.run_comprehensive_stress_test(
            deal_id=deal_id,
            scenarios=request.scenarios,
            time_horizon=request.time_horizon,
            monte_carlo_runs=request.monte_carlo_runs
        )
        
        return StressTestResponse(**results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress testing failed: {str(e)}")

@router.get("/{deal_id}/var", )
async def calculate_value_at_risk(
    deal_id: str,
    confidence_level: float = Query(0.95, ge=0.5, le=0.99),
    time_horizon_days: int = Query(30, ge=1, le=365),
    method: str = Query("monte_carlo", regex="^(parametric|historical|monte_carlo)$"),
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Calculate Value at Risk (VaR) for portfolio"""
    try:
        var_result = risk_service.calculate_var(
            deal_id=deal_id,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon_days,
            method=method
        )
        
        return {
            "deal_id": deal_id,
            "confidence_level": confidence_level,
            "time_horizon_days": time_horizon_days,
            "method": method,
            "var_amount": var_result["var"],
            "expected_shortfall": var_result.get("expected_shortfall"),
            "portfolio_value": var_result["portfolio_value"],
            "var_percentage": var_result["var_percentage"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VaR calculation failed: {str(e)}")

@router.get("/{deal_id}/attribution")
async def get_risk_attribution(
    deal_id: str,
    attribution_type: str = Query("sector", regex="^(sector|asset|rating)$"),
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Get risk attribution analysis"""
    try:
        attribution = risk_service.calculate_risk_attribution(
            deal_id=deal_id,
            attribution_type=attribution_type
        )
        
        return {
            "deal_id": deal_id,
            "attribution_type": attribution_type,
            "total_portfolio_risk": attribution["total_risk"],
            "attributions": attribution["attributions"],
            "top_contributors": attribution["top_contributors"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk attribution failed: {str(e)}")

@router.post("/portfolio-comparison")
async def compare_portfolio_risk(
    deal_ids: List[str],
    metrics: List[str] = Query(["volatility", "var", "concentration"]),
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Compare risk metrics across multiple portfolios"""
    try:
        if len(deal_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 portfolios can be compared")
            
        comparison = risk_service.compare_portfolios(
            deal_ids=deal_ids,
            metrics=metrics
        )
        
        return {
            "portfolios": deal_ids,
            "metrics": metrics,
            "comparison_results": comparison,
            "rankings": comparison.get("rankings", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio comparison failed: {str(e)}")

@router.post("/{deal_id}/risk-report", response_model=RiskReportResponse)
async def generate_risk_report(
    deal_id: str,
    request: RiskReportRequest,
    risk_service: RiskAnalyticsService = Depends(get_risk_service),
    db: Session = Depends(get_db)
):
    """Generate comprehensive risk report"""
    try:
        report = risk_service.generate_comprehensive_report(
            deal_id=deal_id,
            report_type=request.report_type,
            include_sections=request.include_sections,
            custom_parameters=request.custom_parameters
        )
        
        return RiskReportResponse(**report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk report generation failed: {str(e)}")

@router.get("/correlation-heatmap")
async def get_correlation_heatmap(
    asset_ids: List[str] = Query(..., max_items=50),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get correlation heatmap data for visualization"""
    try:
        heatmap_data = integration_service.get_correlation_heatmap(asset_ids)
        
        return {
            "asset_ids": asset_ids,
            "correlation_matrix": heatmap_data["matrix"],
            "labels": heatmap_data["labels"],
            "max_correlation": heatmap_data["max_corr"],
            "min_correlation": heatmap_data["min_corr"],
            "avg_correlation": heatmap_data["avg_corr"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation heatmap generation failed: {str(e)}")

@router.get("/market-data/correlations")
async def get_market_correlations(
    asset_types: Optional[List[str]] = Query(None),
    sectors: Optional[List[str]] = Query(None),
    integration_service: DataIntegrationService = Depends(get_integration_service)
):
    """Get market-wide correlation statistics"""
    try:
        stats = integration_service.get_correlation_statistics(
            asset_types=asset_types,
            sectors=sectors
        )
        
        return {
            "total_correlations": stats["count"],
            "average_correlation": stats["avg_correlation"],
            "correlation_distribution": stats["distribution"],
            "high_correlation_pairs": stats["high_correlation_pairs"],
            "low_correlation_pairs": stats["low_correlation_pairs"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market correlation analysis failed: {str(e)}")