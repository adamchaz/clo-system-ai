"""
Production Security Configuration for CLO Management System
Implements rate limiting, CORS hardening, security headers, input validation, and authentication
"""

import hashlib
import secrets
import time
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Authentication dependencies (get_current_user, require_admin_role, ...) live in
# app.core.unified_auth - import them from there. This module only provides the
# security middleware and the legacy password/token helpers below.
# Imported without try/except on purpose: if unified_auth fails to import, the app
# must fail to start rather than run without authentication.
from .unified_auth import get_auth_service

# Legacy password utilities (kept so existing imports keep working).
# They delegate to AuthService so there is exactly one hashing scheme (bcrypt)
# that matches what login verifies against.
def hash_password(password: str) -> str:
    """Hash a password with bcrypt (delegates to AuthService)"""
    return get_auth_service().get_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash (delegates to AuthService)"""
    return get_auth_service().verify_password(password, hashed)

# Legacy token utilities (kept for backward compatibility)
def create_access_token(data: Dict[str, Any]) -> str:
    """Create a signed JWT access token (delegates to AuthService)"""
    return get_auth_service().create_access_token(data)

def decode_token(token: str) -> Dict[str, Any]:
    """Decode JWT token using PyJWT (legacy - use unified_auth instead)"""
    try:
        auth_service = get_auth_service()
        user = auth_service.get_current_user(token)
        if user:
            return {"sub": user.get("email"), "user_data": user}
        else:
            raise ValueError("Invalid token")
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise ValueError("Invalid token")





# ==== PRODUCTION SECURITY MIDDLEWARE ====

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # HSTS (only in production)
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        client_ip = get_remote_address(request)
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        logger.info(f"Request: {method} {url} from {client_ip} - {user_agent}")
        
        response = await call_next(request)
        
        # Log response details
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response


# ==== SECURITY CONFIGURATION FUNCTIONS ====

def configure_cors(app: FastAPI):
    """Configure CORS middleware with production-ready settings"""
    
    # More restrictive CORS for production
    allowed_origins = settings.cors_origins
    if settings.environment == "production":
        # Remove wildcard origins in production
        allowed_origins = [origin for origin in allowed_origins if "*" not in origin]
    else:
        # Use specific localhost origins in development (can't use "*" with credentials)
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002", 
            "http://localhost:3003",
            "http://localhost:3004",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:3004",
            "null"  # For file:// protocol testing
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-Client-Version"
        ],
        expose_headers=["X-Total-Count", "X-Rate-Limit-*"],
        max_age=3600,  # Cache preflight for 1 hour
    )


def configure_rate_limiting(app: FastAPI):
    """Configure rate limiting"""
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info(f"✅ Rate limiting configured for {settings.environment}")


def configure_security_middleware(app: FastAPI):
    """Configure all security middleware"""
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("✅ Security middleware configured")


def configure_production_security(app: FastAPI):
    """
    Complete production security configuration
    Call this function to apply all security measures
    """
    
    logger.info("🔒 Configuring production security...")
    
    # Configure CORS - MUST be first middleware
    configure_cors(app)
    
    # Configure rate limiting  
    configure_rate_limiting(app)
    
    # Configure security middleware
    configure_security_middleware(app)
    
    logger.info("🔒 Production security configuration complete")


# ==== RATE LIMITING DECORATORS ====

def rate_limit_strict():
    """Strict rate limiting: 10 requests per minute"""
    return limiter.limit("10/minute")


def rate_limit_moderate():
    """Moderate rate limiting: 100 requests per minute"""
    return limiter.limit("100/minute")


def rate_limit_lenient():
    """Lenient rate limiting: 1000 requests per minute"""
    return limiter.limit("1000/minute")


def rate_limit_auth():
    """Authentication rate limiting: 5 attempts per minute"""
    return limiter.limit("5/minute")


def rate_limit_upload():
    """File upload rate limiting: 20 uploads per minute"""
    return limiter.limit("20/minute")


# ==== INPUT VALIDATION ====

class InputValidator:
    """Input validation utilities for CLO system"""
    
    @staticmethod
    def validate_deal_id(deal_id: str) -> bool:
        """Validate CLO deal ID format"""
        if not deal_id or len(deal_id) < 3 or len(deal_id) > 50:
            return False
        return deal_id.replace("_", "").replace("-", "").isalnum()
    
    @staticmethod
    def validate_asset_id(asset_id: str) -> bool:
        """Validate asset ID format"""
        if not asset_id or len(asset_id) < 5 or len(asset_id) > 100:
            return False
        return True
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validate monetary amounts"""
        return isinstance(amount, (int, float)) and amount >= 0 and amount < 1e15
    
    @staticmethod
    def validate_rating(rating: str) -> bool:
        """Validate credit rating format"""
        if not rating:
            return False
        valid_ratings = [
            # S&P ratings
            "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", 
            "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
            "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D",
            # Moody's ratings  
            "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
            "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3",
            "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"
        ]
        return rating in valid_ratings