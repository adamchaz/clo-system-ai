"""
Main API Router for CLO Management System v1
Aggregates all API endpoints into a single router
"""

from fastapi import APIRouter

from .endpoints import (
    assets,
    portfolios,
    waterfall,
    risk_analytics,
    scenarios,
    auth,
    monitoring,
    rebalancing,
    credit_migration,
    reports,
    documents,
    portfolio_analytics,
    user_management,
    websocket,
    admin,
    yield_curves
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Authentication"]
)

api_router.include_router(
    assets.router, 
    prefix="/assets", 
    tags=["Asset Management"]
)

api_router.include_router(
    portfolios.router, 
    prefix="/portfolios", 
    tags=["Portfolio Management"]
)

api_router.include_router(
    waterfall.router, 
    prefix="/waterfall", 
    tags=["Waterfall Calculations"]
)

api_router.include_router(
    risk_analytics.router, 
    prefix="/risk", 
    tags=["Risk Analytics"]
)

api_router.include_router(
    scenarios.router, 
    prefix="/scenarios", 
    tags=["Scenario Analysis"]
)

api_router.include_router(
    monitoring.router, 
    prefix="/monitoring", 
    tags=["System Monitoring"]
)

api_router.include_router(
    rebalancing.router, 
    prefix="/rebalancing", 
    tags=["Portfolio Rebalancing"]
)

api_router.include_router(
    credit_migration.router, 
    prefix="/credit-migration", 
    tags=["Credit Migration"]
)

api_router.include_router(
    reports.router, 
    prefix="/reports", 
    tags=["Reports"]
)

api_router.include_router(
    documents.router, 
    prefix="/documents", 
    tags=["Document Management"]
)

api_router.include_router(
    portfolio_analytics.router, 
    prefix="/portfolio-analytics", 
    tags=["Portfolio Analytics"]
)

api_router.include_router(
    user_management.router, 
    prefix="/users", 
    tags=["User Management"]
)

api_router.include_router(
    websocket.router, 
    prefix="/websocket", 
    tags=["Real-time Communication"]
)

# Test endpoint to diagnose authentication issue  
@api_router.get("/test")
async def test_endpoint():
    """Simple test endpoint with no dependencies"""
    return {"message": "Test endpoint working", "status": "success"}

api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["Administration"]
)

api_router.include_router(
    yield_curves.router, 
    prefix="/yield-curves", 
    tags=["Yield Curves"]
)