"""
Portfolio Analytics API Endpoints
FastAPI routes for advanced portfolio analysis, optimization, and performance measurement
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_200_OK

from ....core.security import get_current_user
from ....schemas.portfolio_analytics import (
    PortfolioOptimizationRequest, PortfolioOptimizationResult,
    PortfolioPerformanceAnalysisRequest, PortfolioPerformanceResult,
    PortfolioRiskAnalysisRequest, PortfolioRiskAnalysisResult,
    ConcentrationAnalysisRequest, ConcentrationAnalysisResult,
    PortfolioScenarioAnalysisRequest, PortfolioScenarioAnalysisResult,
    PortfolioComparisonRequest, PortfolioComparisonResult,
    PortfolioAnalyticsStatsResponse
)
from ....services.portfolio_analytics_service import PortfolioAnalyticsService
from ....core.exceptions import CLOBusinessError, CLOValidationError

router = APIRouter()
analytics_service = PortfolioAnalyticsService()


@router.post("/{portfolio_id}/optimize", response_model=PortfolioOptimizationResult)
async def optimize_portfolio(
    portfolio_id: str,
    request: PortfolioOptimizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Optimize portfolio based on specified criteria
    
    - **portfolio_id**: Portfolio identifier
    - **request**: Optimization parameters including type, constraints, and risk parameters
    
    Optimization Types:
    - risk_minimization: Minimize portfolio risk for given return
    - return_maximization: Maximize return for given risk level
    - sharpe_ratio: Optimize risk-adjusted returns
    - compliance_optimization: Optimize while maintaining regulatory compliance
    """
    try:
        # Set portfolio_id in request
        request.portfolio_id = portfolio_id
        
        result = analytics_service.optimize_portfolio(request, current_user["id"])
        return result
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/{portfolio_id}/performance", response_model=PortfolioPerformanceResult)
async def analyze_performance(
    portfolio_id: str,
    request: PortfolioPerformanceAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze portfolio performance over specified period
    
    - **portfolio_id**: Portfolio identifier
    - **request**: Performance analysis parameters including period, benchmark, and analysis options
    
    Analysis includes:
    - Return metrics (total, annualized, cumulative)
    - Risk metrics (volatility, Sharpe ratio, max drawdown, VaR)
    - Benchmark comparison and tracking error
    - Performance attribution by sector, security, and style factors
    """
    try:
        # Set portfolio_id in request
        request.portfolio_id = portfolio_id
        
        result = analytics_service.analyze_portfolio_performance(request, current_user["id"])
        return result
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")


@router.post("/{portfolio_id}/risk", response_model=PortfolioRiskAnalysisResult)
async def analyze_risk(
    portfolio_id: str,
    request: PortfolioRiskAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Comprehensive portfolio risk analysis
    
    - **portfolio_id**: Portfolio identifier
    - **request**: Risk analysis parameters including confidence levels, time horizons, and stress scenarios
    
    Analysis includes:
    - Value at Risk (VaR) at multiple confidence levels and time horizons
    - Expected Shortfall (Conditional VaR)
    - Stress testing with predefined and custom scenarios
    - Risk decomposition by sector and individual assets
    - Correlation analysis and diversification metrics
    """
    try:
        # Set portfolio_id in request
        request.portfolio_id = portfolio_id
        
        result = analytics_service.analyze_portfolio_risk(request, current_user["id"])
        return result
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.get("/test-debug")
async def test_debug_endpoint():
    """Debug endpoint to test if portfolio_analytics router is working"""
    print("DEBUG: Test endpoint called successfully")
    return {"message": "portfolio_analytics router is working", "endpoint": "test-debug"}

@router.post("/{portfolio_id}/concentration")
async def analyze_concentration(
    portfolio_id: str,
    request: ConcentrationAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze portfolio concentration with CLO-specific concentration tests
    
    - **portfolio_id**: Portfolio identifier (CLO Deal ID)
    - **request**: Concentration analysis parameters including analysis_date
    
    For CLO deals, returns database-driven concentration test results with proper thresholds.
    For other portfolios, uses general concentration analysis.
    """
    print(f"DEBUG: CONCENTRATION ENDPOINT CALLED for portfolio_id: {portfolio_id}")
    print(f"DEBUG: Request method and URL reached portfolio_analytics.py successfully")
    try:
        # Check if this is a CLO deal (starts with MAG, CLO, etc.)
        if portfolio_id.startswith(('MAG', 'CLO')):
            # Use CLO concentration test system with database-driven thresholds
            from datetime import date
            from ....core.database import get_db
            
            # Get analysis date from request or use default
            analysis_date = getattr(request, 'analysis_date', None)
            if not analysis_date:
                analysis_date = date(2016, 3, 23)  # Default CLO analysis date
            
            try:
                # Use a simple query to get MAG17 thresholds directly
                db = next(get_db())
                from ....models.database.concentration_threshold_models import ConcentrationTestDefinition, DealConcentrationThreshold
                from sqlalchemy import and_
                
                # Get thresholds for this deal
                thresholds_query = db.query(
                    ConcentrationTestDefinition.test_number,
                    ConcentrationTestDefinition.test_name,  
                    DealConcentrationThreshold.threshold_value,
                    ConcentrationTestDefinition.result_type
                ).join(
                    DealConcentrationThreshold, 
                    ConcentrationTestDefinition.test_id == DealConcentrationThreshold.test_id
                ).filter(
                    and_(
                        DealConcentrationThreshold.deal_id == portfolio_id,
                        DealConcentrationThreshold.effective_date <= analysis_date,
                        (DealConcentrationThreshold.expiry_date.is_(None) | (DealConcentrationThreshold.expiry_date > analysis_date))
                    )
                ).order_by(ConcentrationTestDefinition.test_number)
                
                thresholds = thresholds_query.all()
                
                # Format as concentration test results
                concentration_tests = []
                for test_number, test_name, threshold_value, result_type in thresholds:
                    concentration_tests.append({
                        "test_number": test_number,
                        "test_name": test_name,
                        "threshold": float(threshold_value),
                        "result": 0.0,  # Would need actual calculation
                        "pass_fail": "N/A",  # Would need actual calculation 
                        "threshold_source": "database"
                    })
                
                result = {
                    "analysis_date": analysis_date.isoformat(),
                    "test_results": concentration_tests,
                    "summary": {
                        "total_tests": len(concentration_tests),
                        "passed_tests": 0,
                        "failed_tests": 0,
                        "na_tests": len(concentration_tests)
                    }
                }
                
                # Return in format expected by frontend
                return {
                    "portfolio_id": portfolio_id,
                    "analysis_date": result['analysis_date'],
                    "concentration_tests": result['test_results'],
                    "summary": result['summary'],
                    "total_tests": result['summary'].get('total_tests', 0),
                    "passed_tests": result['summary'].get('passed_tests', 0),
                    "failed_tests": result['summary'].get('failed_tests', 0)
                }
                
            except Exception as e:
                # Fallback to general analysis if concentration test fails
                print(f"CLO concentration test failed, falling back to general analysis: {e}")
                import traceback
                traceback.print_exc()
        
        # Original general portfolio concentration analysis
        request.portfolio_id = portfolio_id
        result = analytics_service.analyze_concentration(request, current_user["id"])
        
        # Convert to dictionary and ensure all numeric values are properly typed
        result_dict = {
            "portfolio_id": result.portfolio_id,
            "analysis_date": result.analysis_date.isoformat(),
            "concentration_metrics": {},
            "herfindahl_indices": {},
            "concentration_levels": result.concentration_levels,
            "limit_violations": result.limit_violations,
            "concentration_warnings": result.concentration_warnings,
            "diversification_opportunities": result.diversification_opportunities,
            "recommended_adjustments": result.recommended_adjustments
        }
        
        # Convert concentration metrics to proper floats
        for dimension, metrics in result.concentration_metrics.items():
            result_dict["concentration_metrics"][dimension] = {}
            for key, value in metrics.items():
                if key == "total_positions":
                    result_dict["concentration_metrics"][dimension][key] = int(value)
                else:
                    result_dict["concentration_metrics"][dimension][key] = float(value) if isinstance(value, (str, int)) else value
        
        # Convert HHI to floats
        for dimension, value in result.herfindahl_indices.items():
            result_dict["herfindahl_indices"][dimension] = float(value) if isinstance(value, str) else value
        
        return result_dict
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concentration analysis failed: {str(e)}")


@router.post("/{portfolio_id}/scenarios", response_model=PortfolioScenarioAnalysisResult)
async def analyze_scenarios(
    portfolio_id: str,
    request: PortfolioScenarioAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Portfolio scenario analysis and Monte Carlo simulation
    
    - **portfolio_id**: Portfolio identifier
    - **request**: Scenario analysis parameters including scenarios and simulation parameters
    
    Analysis includes:
    - Predefined economic scenarios (recession, recovery, stress)
    - Custom scenario modeling
    - Monte Carlo simulations with path dependency
    - Statistical outcome analysis (mean, median, percentiles)
    - Tail risk and probability analysis
    """
    try:
        # Set portfolio_id in request
        request.portfolio_id = portfolio_id
        
        # Mock implementation for now
        from datetime import datetime
        from decimal import Decimal
        
        result = PortfolioScenarioAnalysisResult(
            portfolio_id=portfolio_id,
            analysis_date=datetime.utcnow(),
            scenarios_analyzed=request.scenarios or ["base_case", "stress", "optimistic"],
            scenario_outcomes={
                "base_case": {"return": Decimal("0.08"), "volatility": Decimal("0.12")},
                "stress": {"return": Decimal("-0.15"), "volatility": Decimal("0.25")},
                "optimistic": {"return": Decimal("0.18"), "volatility": Decimal("0.08")}
            },
            mean_outcome=Decimal("0.04"),
            median_outcome=Decimal("0.06"),
            std_deviation=Decimal("0.15"),
            skewness=Decimal("-0.5"),
            kurtosis=Decimal("3.2"),
            scenario_var=Decimal("0.12"),
            tail_risk=Decimal("0.08"),
            probability_of_loss=Decimal("0.15"),
            best_case_scenario="optimistic",
            worst_case_scenario="stress",
            most_likely_outcome={"return": Decimal("0.06"), "probability": Decimal("0.35")}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario analysis failed: {str(e)}")


@router.post("/compare", response_model=PortfolioComparisonResult)
async def compare_portfolios(
    request: PortfolioComparisonRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Compare multiple portfolios across various metrics
    
    - **request**: Comparison parameters including portfolio IDs, metrics, and analysis period
    
    Comparison includes:
    - Side-by-side metric comparison
    - Statistical significance testing
    - Correlation analysis between portfolios
    - Performance rankings and scoring
    - Relative strengths and weaknesses analysis
    """
    try:
        # Mock implementation for now
        from datetime import datetime
        from decimal import Decimal
        
        result = PortfolioComparisonResult(
            comparison_date=datetime.utcnow(),
            portfolios_analyzed=request.portfolio_ids,
            analysis_period=request.analysis_period.value,
            metric_comparisons={
                "return": {pid: Decimal("0.08") for pid in request.portfolio_ids},
                "volatility": {pid: Decimal("0.12") for pid in request.portfolio_ids},
                "sharpe_ratio": {pid: Decimal("1.2") for pid in request.portfolio_ids}
            },
            relative_rankings={
                "return": request.portfolio_ids,
                "volatility": request.portfolio_ids[::-1],
                "sharpe_ratio": request.portfolio_ids
            },
            significance_tests={},
            correlation_matrix={
                pid1: {pid2: 0.75 for pid2 in request.portfolio_ids} 
                for pid1 in request.portfolio_ids
            },
            best_performer={metric: request.portfolio_ids[0] for metric in request.comparison_metrics},
            worst_performer={metric: request.portfolio_ids[-1] for metric in request.comparison_metrics},
            overall_ranking=request.portfolio_ids
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio comparison failed: {str(e)}")


@router.get("/stats", response_model=PortfolioAnalyticsStatsResponse)
async def get_analytics_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get portfolio analytics system statistics
    
    Returns:
    - Usage statistics and patterns
    - Analysis performance metrics
    - Error rates and common issues
    - System performance indicators
    """
    try:
        # Mock implementation
        result = PortfolioAnalyticsStatsResponse(
            total_portfolios_analyzed=150,
            analysis_types_performed={
                "optimization": 45,
                "performance": 78,
                "risk": 56,
                "concentration": 34,
                "scenario": 23
            },
            average_analysis_time={
                "optimization": 12.5,
                "performance": 3.2,
                "risk": 8.7,
                "concentration": 2.1,
                "scenario": 45.3
            },
            most_requested_analytics=[
                {"type": "performance", "count": 78, "percentage": 33.2},
                {"type": "risk", "count": 56, "percentage": 23.8},
                {"type": "optimization", "count": 45, "percentage": 19.1}
            ],
            recent_analyses=[
                {"portfolio_id": "CLO_001", "type": "performance", "timestamp": "2024-01-15T10:30:00"},
                {"portfolio_id": "CLO_002", "type": "risk", "timestamp": "2024-01-15T09:45:00"}
            ],
            success_rate={
                "optimization": 0.92,
                "performance": 0.98,
                "risk": 0.95,
                "concentration": 0.99,
                "scenario": 0.89
            },
            error_summary={
                "data_unavailable": 8,
                "calculation_error": 3,
                "timeout": 2,
                "validation_error": 5
            }
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Convenience endpoints for common operations
@router.get("/{portfolio_id}/quick-metrics")
async def get_quick_portfolio_metrics(
    portfolio_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get quick portfolio overview metrics
    
    - **portfolio_id**: Portfolio identifier
    
    Returns basic metrics without full analysis:
    - Current value and asset count
    - Basic risk metrics
    - Top concentrations
    - Recent performance
    """
    try:
        # Mock implementation
        from datetime import datetime
        from decimal import Decimal
        
        return {
            "portfolio_id": portfolio_id,
            "as_of_date": datetime.utcnow(),
            "total_value": Decimal("25000000"),
            "asset_count": 125,
            "weighted_avg_rating": "B+",
            "portfolio_yield": Decimal("0.078"),
            "duration": Decimal("2.8"),
            "top_sector_concentrations": [
                {"sector": "Technology", "weight": Decimal("0.18")},
                {"sector": "Healthcare", "weight": Decimal("0.15")},
                {"sector": "Energy", "weight": Decimal("0.12")}
            ],
            "risk_metrics": {
                "volatility": Decimal("0.095"),
                "var_95_1day": Decimal("0.025"),
                "max_single_exposure": Decimal("0.035")
            },
            "recent_performance": {
                "1_day": Decimal("0.002"),
                "1_week": Decimal("0.008"),
                "1_month": Decimal("0.015"),
                "ytd": Decimal("0.045")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quick metrics: {str(e)}")


@router.post("/{portfolio_id}/alerts")
async def generate_portfolio_alerts(
    portfolio_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate portfolio alerts and warnings
    
    - **portfolio_id**: Portfolio identifier
    
    Checks for:
    - Concentration limit breaches
    - Risk threshold violations
    - Performance deterioration
    - Compliance issues
    """
    try:
        # Mock implementation
        return {
            "portfolio_id": portfolio_id,
            "alert_count": 3,
            "alerts": [
                {
                    "type": "concentration",
                    "severity": "warning",
                    "message": "Technology sector concentration exceeds 15% limit",
                    "current_value": "18.2%",
                    "threshold": "15.0%"
                },
                {
                    "type": "risk",
                    "severity": "info",
                    "message": "Portfolio volatility increased by 2.1% this month",
                    "current_value": "9.5%",
                    "previous_value": "7.4%"
                },
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": "Underperforming benchmark by 1.2% over last 3 months",
                    "portfolio_return": "2.8%",
                    "benchmark_return": "4.0%"
                }
            ],
            "recommendations": [
                "Consider reducing technology sector exposure",
                "Review recent asset additions for risk contribution",
                "Analyze underperforming assets for potential replacement"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate alerts: {str(e)}")