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
    reports
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