#!/usr/bin/env python3
"""
Debug script to diagnose admin route loading issues
"""

import sys
import traceback
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_imports():
    """Test if all modules import correctly"""
    print("=== TESTING MODULE IMPORTS ===")
    
    try:
        print("1. Testing unified_auth import...")
        from app.core.unified_auth import require_admin_role, get_current_user
        print("   [OK] unified_auth imports successfully")
    except Exception as e:
        print(f"   [ERROR] unified_auth import failed: {e}")
        traceback.print_exc()
    
    try:
        print("2. Testing admin endpoints import...")
        from app.api.v1.endpoints import admin
        print("   [OK] admin module imports successfully")
        print(f"   - Admin router: {admin.router}")
        print(f"   - Admin routes: {[route.path for route in admin.router.routes]}")
    except Exception as e:
        print(f"   [ERROR] admin module import failed: {e}")
        traceback.print_exc()
    
    try:
        print("3. Testing API router import...")
        from app.api.v1.api import api_router
        print("   [OK] API router imports successfully")
        
        # Check if admin routes are in the API router
        admin_routes = [route for route in api_router.routes if '/admin' in str(route)]
        print(f"   - Admin routes in API router: {len(admin_routes)}")
        for route in admin_routes:
            print(f"     - {route}")
            
    except Exception as e:
        print(f"   [ERROR] API router import failed: {e}")
        traceback.print_exc()
    
    try:
        print("4. Testing main app import...")
        from app.main import app
        print("   [OK] Main app imports successfully")
        
        # Check all routes in the main app
        all_routes = []
        for route in app.routes:
            if hasattr(route, 'routes'):  # APIRouter
                for subroute in route.routes:
                    all_routes.append(str(subroute))
            else:
                all_routes.append(str(route))
        
        admin_app_routes = [route for route in all_routes if '/admin' in route]
        print(f"   - Total routes in app: {len(all_routes)}")
        print(f"   - Admin routes in main app: {len(admin_app_routes)}")
        
        if admin_app_routes:
            print("   - Admin routes found:")
            for route in admin_app_routes:
                print(f"     - {route}")
        else:
            print("   [ERROR] No admin routes found in main app!")
            
    except Exception as e:
        print(f"   [ERROR] Main app import failed: {e}")
        traceback.print_exc()

def test_route_registration():
    """Test direct route registration"""
    print("\n=== TESTING ROUTE REGISTRATION ===")
    
    try:
        from app.api.v1.endpoints.admin import router as admin_router
        from app.api.v1.api import api_router
        
        print("Admin router routes:")
        for route in admin_router.routes:
            print(f"  - {route.path} {route.methods}")
        
        print("\nAPI router admin routes:")
        for route in api_router.routes:
            if hasattr(route, 'path') and '/admin' in route.path:
                print(f"  - {route.path} {route.methods}")
        
        # Test if we can manually create a simple router
        from fastapi import APIRouter
        test_router = APIRouter()
        
        @test_router.get("/test")
        async def test_endpoint():
            return {"message": "Test successful"}
        
        print(f"\nTest router routes: {[route.path for route in test_router.routes]}")
        
    except Exception as e:
        print(f"[ERROR] Route registration test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("CLO System Admin Route Debugging\n")
    test_imports()
    test_route_registration()
    print("\n=== DEBUG COMPLETE ===")