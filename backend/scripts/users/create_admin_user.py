#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database_config import db_config
from app.models.auth import User
from app.schemas.auth import UserRole
from app.core.security import hash_password

def create_admin_user():
    """Create an admin user for testing"""
    
    print("=== Creating CLO System Admin User ===")
    
    # User details
    email = "admin@clo-system.com"
    password = "admin123"
    
    try:
        # Get database session
        with db_config.get_db_session('postgresql') as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                print(f"Admin user already exists: {email}")
                print(f"Role: {existing_user.role}")
                return
            
            # Create new admin user
            hashed_password = hash_password(password)
            
            admin_user = User(
                user_id="admin_001",
                username="admin",
                email=email,
                password_hash=hashed_password,
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"Admin user created successfully!")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"Role: {admin_user.role}")
            print(f"Full Name: {admin_user.first_name} {admin_user.last_name}")
            print(f"User ID: {admin_user.user_id}")
            print(f"\nUse these credentials to log in at: http://localhost:3003")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()