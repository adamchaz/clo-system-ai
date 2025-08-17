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

def create_analyst_user():
    """Create an analyst user for the CLO system"""
    
    print("=== Creating CLO System Analyst User ===")
    
    # User details
    email = "analyst@clo-system.com"
    password = "analyst123"
    
    try:
        # Get database session
        with db_config.get_db_session('postgresql') as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                print(f"Analyst user already exists: {email}")
                print(f"Role: {existing_user.role}")
                return
            
            # Create new analyst user  
            auth_service = AuthService()
            hashed_password = auth_service.get_password_hash(password)
            
            analyst_user = User(
                user_id="analyst_001",
                username="analyst",
                email=email,
                password_hash=hashed_password,
                first_name="Risk",
                last_name="Analyst",
                role=UserRole.ANALYST,
                is_active=True
            )
            
            db.add(analyst_user)
            db.commit()
            db.refresh(analyst_user)
            
            print(f"Analyst user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Role: {analyst_user.role}")
            print(f"Full Name: {analyst_user.first_name} {analyst_user.last_name}")
            print(f"User ID: {analyst_user.user_id}")
            print(f"\nUse these credentials to log in at: http://localhost:3002")
            
    except Exception as e:
        print(f"Error creating analyst user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_analyst_user()