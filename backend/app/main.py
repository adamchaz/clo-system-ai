"""
CLO Management System - FastAPI Main Application
Converting sophisticated Excel/VBA CLO system to modern Python web application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import settings
from .core.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="CLO Management System API",
    description="A comprehensive CLO portfolio management system converting from Excel/VBA to Python",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "capabilities": {
            "quantlib_version": "1.39",
            "max_assets": settings.max_assets,
            "database": "PostgreSQL",
            "cache": "Redis"
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
    }