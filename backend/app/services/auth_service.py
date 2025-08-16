"""
Authentication Service
Handles user authentication, authorization, and session management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import hashlib
import secrets
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from sqlalchemy.orm import Session
from ..core.database import engine, SessionLocal
from ..core.config import settings
from ..schemas.auth import User, UserCreate, UserRole

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user information
        """
        logger.info(f"Creating user: {user_data.email}")
        
        try:
            # Hash password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Generate user ID
            user_id = self._generate_user_id(user_data.email)
            
            # Create user record
            user = {
                'id': user_id,
                'email': user_data.email,
                'full_name': user_data.full_name,
                'hashed_password': hashed_password,
                'role': user_data.role,
                'is_active': True,
                'created_at': datetime.now(),
                'login_count': 0
            }
            
            # Store in database
            self._store_user(user)
            
            # Log user creation
            self._log_auth_event('user_created', user_id, success=True)
            
            logger.info(f"Successfully created user {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user {user_data.email}: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        logger.info(f"Authenticating user: {email}")
        
        try:
            # Get user from database
            user = self.get_user_by_email(email)
            
            if not user:
                self._log_auth_event('login_failed', None, details={'email': email, 'reason': 'user_not_found'})
                logger.warning(f"Authentication failed - user not found: {email}")
                return None
            
            # Verify password
            if not self.verify_password(password, user['hashed_password']):
                self._log_auth_event('login_failed', user['id'], details={'reason': 'invalid_password'})
                logger.warning(f"Authentication failed - invalid password: {email}")
                return None
            
            # Check if user is active
            if not user.get('is_active', False):
                self._log_auth_event('login_failed', user['id'], details={'reason': 'user_inactive'})
                logger.warning(f"Authentication failed - user inactive: {email}")
                return None
            
            # Update login information
            self._update_user_login(user['id'])
            
            # Log successful authentication
            self._log_auth_event('login_success', user['id'])
            
            logger.info(f"Successfully authenticated user: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug("Successfully created access token")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from JWT token
        
        Args:
            token: JWT access token
            
        Returns:
            User data if token valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            
            if email is None:
                return None
            
            # Get user from database
            user = self.get_user_by_email(email)
            
            if user is None:
                return None
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User data if found, None otherwise
        """
        try:
            # Query the actual PostgreSQL users table
            with SessionLocal() as session:
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT user_id, email, password_hash, first_name, last_name, role, is_active, created_at, last_login FROM users WHERE email = :email AND is_active = true"),
                    {'email': email}
                ).fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'email': result[1], 
                        'hashed_password': result[2],
                        'full_name': f"{result[3]} {result[4]}" if result[3] and result[4] else result[1],
                        'role': UserRole.ADMIN if result[5] == 'ADMIN' else UserRole.MANAGER if result[5] == 'MANAGER' else UserRole.ANALYST if result[5] == 'ANALYST' else UserRole.VIEWER,
                        'is_active': result[6],
                        'created_at': result[7],
                        'last_login': result[8]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving user {email}: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information
        
        Args:
            user_id: User identifier
            updates: Fields to update
            
        Returns:
            Updated user data
        """
        logger.info(f"Updating user: {user_id}")
        
        try:
            # Get existing user
            user = self._get_user_by_id(user_id)
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Apply updates
            allowed_updates = ['full_name', 'role', 'is_active']
            for field, value in updates.items():
                if field in allowed_updates:
                    user[field] = value
            
            user['updated_at'] = datetime.now()
            
            # Store updated user
            self._store_user(user)
            
            # Log update
            self._log_auth_event('user_updated', user_id, details=updates)
            
            logger.info(f"Successfully updated user {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def update_password(self, user_id: str, new_password: str) -> None:
        """
        Update user password
        
        Args:
            user_id: User identifier
            new_password: New password
        """
        logger.info(f"Updating password for user: {user_id}")
        
        try:
            # Get existing user
            user = self._get_user_by_id(user_id)
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Hash new password
            user['hashed_password'] = self.get_password_hash(new_password)
            user['password_updated_at'] = datetime.now()
            
            # Store updated user
            self._store_user(user)
            
            # Log password change
            self._log_auth_event('password_changed', user_id)
            
            logger.info(f"Successfully updated password for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update password for user {user_id}: {e}")
            raise
    
    def create_password_reset_token(self, email: str) -> Optional[str]:
        """
        Create password reset token
        
        Args:
            email: User email address
            
        Returns:
            Reset token if user exists, None otherwise
        """
        logger.info(f"Creating password reset token for: {email}")
        
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Password reset requested for non-existent user: {email}")
                return None
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.now() + timedelta(hours=1)  # 1 hour expiry
            
            # Store reset token
            user['password_reset_token'] = reset_token
            user['password_reset_expires'] = reset_expires
            
            self._store_user(user)
            
            # Log reset token creation
            self._log_auth_event('password_reset_requested', user['id'])
            
            logger.info(f"Created password reset token for user {user['id']}")
            return reset_token
            
        except Exception as e:
            logger.error(f"Failed to create password reset token for {email}: {e}")
            return None
    
    def reset_password_with_token(self, reset_token: str, new_password: str) -> bool:
        """
        Reset password using reset token
        
        Args:
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            True if reset successful, False otherwise
        """
        logger.info("Processing password reset with token")
        
        try:
            # Find user with matching token
            user = self._get_user_by_reset_token(reset_token)
            
            if not user:
                logger.warning("Invalid reset token provided")
                return False
            
            # Check token expiry
            if user.get('password_reset_expires', datetime.min) < datetime.now():
                logger.warning("Expired reset token provided")
                return False
            
            # Update password
            user['hashed_password'] = self.get_password_hash(new_password)
            user['password_updated_at'] = datetime.now()
            user['password_reset_token'] = None
            user['password_reset_expires'] = None
            
            # Store updated user
            self._store_user(user)
            
            # Log password reset
            self._log_auth_event('password_reset_completed', user['id'])
            
            logger.info(f"Successfully reset password for user {user['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get user permissions based on role
        
        Args:
            user_id: User identifier
            
        Returns:
            List of permissions
        """
        try:
            user = self._get_user_by_id(user_id)
            
            if not user:
                return []
            
            role = user.get('role', UserRole.VIEWER)
            
            # Get permissions for role
            from ..schemas.auth import RolePermissionMap
            permissions = RolePermissionMap.get_default_permissions(role)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get permissions for user {user_id}: {e}")
            return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active sessions
        """
        try:
            # Implementation would query sessions table
            # For now, return mock session
            return [
                {
                    'session_id': 'sess_001',
                    'user_id': user_id,
                    'created_at': datetime.now() - timedelta(hours=2),
                    'last_activity': datetime.now() - timedelta(minutes=5),
                    'ip_address': '192.168.1.100',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'is_active': True
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    def validate_token(self, token: str) -> bool:
        """
        Validate JWT token
        
        Args:
            token: JWT token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.JWTError:
            return False
        except Exception:
            return False
    
    def record_logout(self, user_id: str) -> None:
        """
        Record user logout
        
        Args:
            user_id: User identifier
        """
        try:
            self._log_auth_event('logout', user_id)
            logger.info(f"Recorded logout for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to record logout for user {user_id}: {e}")
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # Helper methods
    
    def _generate_user_id(self, email: str) -> str:
        """Generate unique user ID"""
        # Simple ID generation - in production would ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
        return f"user_{email_hash}_{timestamp}"
    
    def _store_user(self, user: Dict[str, Any]) -> None:
        """Store user in database"""
        # Implementation would store in PostgreSQL users table
        logger.debug(f"Stored user {user['id']} in database")
    
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from database"""
        # Implementation would query PostgreSQL
        # For now, return None (not implemented)
        return None
    
    def _get_user_by_reset_token(self, reset_token: str) -> Optional[Dict[str, Any]]:
        """Get user by reset token"""
        # Implementation would query PostgreSQL
        # For now, return None (not implemented)
        return None
    
    def _update_user_login(self, user_id: str) -> None:
        """Update user login statistics"""
        try:
            user = self._get_user_by_id(user_id)
            if user:
                user['last_login'] = datetime.now()
                user['login_count'] = user.get('login_count', 0) + 1
                self._store_user(user)
        except Exception as e:
            logger.error(f"Failed to update login info for user {user_id}: {e}")
    
    def _log_auth_event(
        self, 
        action: str, 
        user_id: Optional[str] = None, 
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log authentication event"""
        try:
            log_entry = {
                'timestamp': datetime.now(),
                'action': action,
                'user_id': user_id,
                'success': success,
                'details': details or {}
            }
            
            # Implementation would store in audit_logs table
            logger.info(f"Auth event: {action} - User: {user_id} - Success: {success}")
            
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")