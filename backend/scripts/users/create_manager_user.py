#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from app.core.database_config import db_config
from app.models.auth import User
from app.schemas.auth import UserRole
from app.services.auth_service import AuthService

def create_manager_user():
    """Create a manager user for the CLO system"""
    
    print("=== Creating CLO System Manager User ===")
    
    # User details
    email = "manager@clo-system.com"
    password = "manager123"
    
    try:
        # Get database session
        with db_config.get_db_session('postgresql') as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                print(f"Manager user already exists: {email}")
                print(f"Role: {existing_user.role}")
                return
            
            # Create new manager user  
            auth_service = AuthService()
            hashed_password = auth_service.get_password_hash(password)
            
            manager_user = User(
                user_id="manager_001",
                username="manager",
                email=email,
                password_hash=hashed_password,
                first_name="Portfolio",
                last_name="Manager",
                role=UserRole.MANAGER,
                is_active=True
            )
            
            db.add(manager_user)
            db.commit()
            db.refresh(manager_user)
            
            print(f"Manager user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Role: {manager_user.role}")
            print(f"Full Name: {manager_user.first_name} {manager_user.last_name}")
            print(f"User ID: {manager_user.user_id}")
            print(f"\nUse these credentials to log in at: http://localhost:3003")
            
    except Exception as e:
        print(f"Error creating manager user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_manager_user()