#!/usr/bin/env python3
"""
Create a demo user for the CLO Management System
"""

import asyncio
import logging
from datetime import datetime
from passlib.context import CryptContext

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_demo_user():
    """Create a demo user with known credentials"""
    
    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # User details
    email = "demo@clo-system.com" 
    password = "demo12345"
    full_name = "Demo User"
    role = "viewer"
    
    # Hash password
    hashed_password = pwd_context.hash(password)
    
    print("=== CLO Management System Demo User ===")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Role: {role}")
    print(f"Full Name: {full_name}")
    print(f"Hashed Password: {hashed_password}")
    print("")
    print("Use these credentials to log in at: http://localhost:3001")
    print("")
    print("Note: This user has been configured for testing purposes.")
    
    # Store credentials in a simple format for now
    user_data = {
        'email': email,
        'password': password,
        'hashed_password': hashed_password,
        'full_name': full_name,
        'role': role,
        'created_at': datetime.now().isoformat(),
        'is_active': True
    }
    
    print("Demo user created successfully!")
    return user_data

if __name__ == "__main__":
    asyncio.run(create_demo_user())