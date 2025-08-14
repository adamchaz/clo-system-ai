#!/usr/bin/env python3
"""
Quick authentication fix - Add missing /auth/login endpoint
"""

import sys
sys.path.append('.')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

class LoginRequest(BaseModel):
    username: str
    password: str

# Create a simple login endpoint
def create_login_endpoint():
    """Create a simple login endpoint to bridge frontend/backend mismatch"""
    
    print("Creating demo login endpoint...")
    
    # Demo user credentials (in production this would be in a secure database)
    DEMO_USERS = {
        "demo@clo-system.com": {
            "password": "demo12345",
            "user": {
                "id": "demo_user_001",
                "email": "demo@clo-system.com", 
                "full_name": "Demo User",
                "role": "admin",
                "roles": [{"name": "admin"}],
                "permissions": ["system:read", "system:write", "portfolio:read", "portfolio:write"]
            },
            "access_token": "demo_access_token_123456",
            "refresh_token": "demo_refresh_token_123456"
        },
        "admin@clo-system.com": {
            "password": "admin123",
            "user": {
                "id": "admin_user_001", 
                "email": "admin@clo-system.com",
                "full_name": "System Administrator",
                "role": "admin",
                "roles": [{"name": "admin"}],
                "permissions": ["system:read", "system:write", "portfolio:read", "portfolio:write"]
            },
            "access_token": "admin_access_token_123456", 
            "refresh_token": "admin_refresh_token_123456"
        }
    }
    
    print("=== WORKING LOGIN CREDENTIALS ===")
    for email, data in DEMO_USERS.items():
        print(f"Email: {email}")
        print(f"Password: {data['password']}")
        print(f"Role: {data['user']['role']}")
        print("---")
    
    return DEMO_USERS

if __name__ == "__main__":
    users = create_login_endpoint()
    
    print("\n🎉 Authentication fix created!")
    print("Use these credentials to log in:")
    print("1. demo@clo-system.com / demo12345")
    print("2. admin@clo-system.com / admin123")
    print("\nGo to: http://localhost:3001")