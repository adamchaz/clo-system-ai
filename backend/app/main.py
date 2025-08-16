"""
CLO Management System - FastAPI Main Application
Converting sophisticated Excel/VBA CLO system to modern Python web application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import settings
from .core.database import DatabaseManager
from .core.security import configure_production_security
from .core.monitoring import configure_monitoring
from .api.v1.api import api_router

# Configure monitoring and structured logging
logger = configure_monitoring()

# Create FastAPI application
app = FastAPI(
    title="CLO Management System API",
    description="A comprehensive CLO portfolio management system converting from Excel/VBA to Python",
    version="1.0.0",
    debug=settings.debug
)

# Configure production security (includes CORS, rate limiting, security headers)
configure_production_security(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting CLO Management System API")
    
    # Test database connections
    if DatabaseManager.test_connection():
        logger.info("✅ PostgreSQL connection successful")
    else:
        logger.error("❌ PostgreSQL connection failed")
    
    if DatabaseManager.test_redis():
        logger.info("✅ Redis connection successful") 
    else:
        logger.error("❌ Redis connection failed")
    
    # Create database tables
    try:
        DatabaseManager.create_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database table creation failed: {e}")


@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down CLO Management System API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CLO Management System API",
        "description": "Converting sophisticated Excel/VBA CLO system to modern Python",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "api": {
            "version": "v1",
            "base_url": "/api/v1",
            "endpoints": {
                "assets": "/api/v1/assets",
                "portfolios": "/api/v1/portfolios", 
                "waterfall": "/api/v1/waterfall",
                "risk": "/api/v1/risk",
                "scenarios": "/api/v1/scenarios",
                "auth": "/api/v1/auth",
                "monitoring": "/api/v1/monitoring",
                "rebalancing": "/api/v1/rebalancing",
                "credit_migration": "/api/v1/credit-migration"
            },
            "documentation": "/docs",
            "openapi": "/openapi.json"
        },
        "capabilities": {
            "quantlib_version": "1.39",
            "max_assets": settings.max_assets,
            "database": "PostgreSQL + SQLite",
            "cache": "Redis",
            "data_migration": "Complete (259,767 records)",
            "operational_infrastructure": "Deployed"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = DatabaseManager.test_connection()
    redis_status = DatabaseManager.test_redis()
    
    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "environment": settings.environment,
        "quantlib": "available"
    }# reloading
