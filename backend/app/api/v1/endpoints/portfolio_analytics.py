"""
Portfolio Analytics API Endpoints
FastAPI routes for advanced portfolio analysis, optimization, and performance measurement
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_200_OK

from ....core.security import get_current_user
from ....core.unified_auth import get_optional_user
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







@router.post("/{portfolio_id}/concentration-test")  
async def analyze_concentration_test(
    portfolio_id: str,
    request: ConcentrationAnalysisRequest,
):
    """
    Database-driven concentration test endpoint (no authentication required for testing)
    """
    
    try:
        from datetime import date
        from ....core.database import get_db
        from ....services.concentration_test_integration_service import get_concentration_integration_service
        
        # Get analysis date from request or use CLO system default
        analysis_date = getattr(request, 'analysis_date', None)
        if not analysis_date:
            analysis_date = date(2016, 3, 23)  # Default CLO analysis date
        
        # Get database connection and run database-driven concentration tests
        db = next(get_db())
        integration_service = get_concentration_integration_service(db)
        
        result = integration_service.run_portfolio_concentration_tests(
            portfolio_id, 
            analysis_date
        )
        
        
        # Return in format expected by frontend
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": result['analysis_date'],
            "concentration_tests": result['concentration_tests'],
            "summary": result['summary'],
            "total_tests": result.get('total_tests', 0),
            "passed_tests": result.get('passed_tests', 0),
            "failed_tests": result.get('failed_tests', 0)
        }
        
    except Exception as e:
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": date(2016, 3, 23).isoformat(),
            "concentration_tests": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warning_tests": 0,
                "compliance_score": "N/A"
            },
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error": str(e)
        }

@router.post("/{portfolio_id}/concentration")
async def analyze_concentration(
    portfolio_id: str,
    request: ConcentrationAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """
    Database-driven concentration analysis endpoint (production)
    Returns comprehensive concentration test results using real portfolio data
    """
    
    try:
        from datetime import date
        from ....core.database import get_db
        from ....services.concentration_test_integration_service import get_concentration_integration_service
        
        
        # Get database connection
        db = next(get_db())
        integration_service = get_concentration_integration_service(db)
        
        # Get analysis date from request or use CLO system default
        analysis_date = getattr(request, 'analysis_date', None)
        if not analysis_date:
            analysis_date = date(2016, 3, 23)  # Default CLO analysis date
        
        # Run database-driven concentration tests
        result = integration_service.run_portfolio_concentration_tests(
            portfolio_id, 
            analysis_date
        )
        
        
        # Return in format expected by frontend
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": result['analysis_date'],
            "concentration_tests": result['concentration_tests'],
            "summary": result['summary'],
            "total_tests": result.get('total_tests', 0),
            "passed_tests": result.get('passed_tests', 0),
            "failed_tests": result.get('failed_tests', 0)
        }
        
    except Exception as e:
        
        # Return error response instead of falling back to mock data
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": date(2016, 3, 23).isoformat(),
            "concentration_tests": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warning_tests": 0,
                "compliance_score": "N/A"
            },
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error": str(e)
        }


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