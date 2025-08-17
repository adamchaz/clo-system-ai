#!/usr/bin/env python3

import requests
import json

def test_auth_endpoint():
    """Test what auth endpoints are available"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Available Auth Endpoints ===")
    
    # Try to get API docs first
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"API Docs Status: {response.status_code}")
    except Exception as e:
        print(f"API Docs Error: {e}")
    
    # Test different auth endpoints
    auth_endpoints = ["/api/v1/auth/login", "/auth/login", "/login"]
    
    for endpoint in auth_endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        try:
            # Try POST with form data
            login_data = {
                "username": "admin@clo-system.com",
                "password": "admin123"
            }
            
            response = requests.post(
                f"{base_url}{endpoint}",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"  Form data POST: {response.status_code}")
            if response.status_code != 404:
                print(f"  Response: {response.text[:200]}...")
                
            # Also try JSON
            response2 = requests.post(
                f"{base_url}{endpoint}",
                json={"email": "admin@clo-system.com", "password": "admin123"}
            )
            print(f"  JSON POST: {response2.status_code}")
            
        except Exception as e:
            print(f"  Error: {e}")

def test_user_exists():
    """Check if users exist in database"""
    print("\n=== Checking Database Users ===")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app.core.database_config import db_config
        from app.models.auth import User
        
        with db_config.get_db_session('postgresql') as db:
            users = db.query(User).all()
            print(f"Total users in database: {len(users)}")
            
            for user in users:
                print(f"  User: {user.email} | Role: {user.role} | Active: {user.is_active}")
                
    except Exception as e:
        print(f"Database check error: {e}")

if __name__ == "__main__":
    test_auth_endpoint()
    test_user_exists()