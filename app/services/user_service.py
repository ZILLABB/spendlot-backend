"""
User service for user management operations.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base_service import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, obj_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            phone_number=obj_in.phone_number,
            timezone=obj_in.timezone,
            currency=obj_in.currency,
            is_active=True,
            is_verified=False
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.last_activity_at = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_password(self, user_id: int, new_password: str) -> User:
        """Update user password."""
        user = self.get(user_id)
        if user:
            user.hashed_password = get_password_hash(new_password)
            # Clear refresh token to force re-login
            user.refresh_token = None
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def update_refresh_token(self, user_id: int, refresh_token: Optional[str]) -> User:
        """Update user's refresh token."""
        user = self.get(user_id)
        if user:
            user.refresh_token = refresh_token
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def generate_password_reset_token(self, user_id: int) -> str:
        """Generate password reset token for user."""
        user = self.get(user_id)
        if user:
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            self.db.commit()
            return reset_token
        return None
    
    def verify_password_reset_token(self, token: str) -> Optional[User]:
        """Verify password reset token and return user if valid."""
        user = self.db.query(User).filter(
            User.password_reset_token == token,
            User.password_reset_expires > datetime.utcnow()
        ).first()
        
        if user:
            # Clear reset token after use
            user.password_reset_token = None
            user.password_reset_expires = None
            self.db.commit()
        
        return user
    
    def verify_email(self, user_id: int) -> User:
        """Mark user email as verified."""
        user = self.get(user_id)
        if user:
            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            user.email_verification_token = None
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def update_activity(self, user_id: int) -> None:
        """Update user's last activity timestamp."""
        user = self.get(user_id)
        if user:
            user.last_activity_at = datetime.utcnow()
            self.db.commit()
    
    def deactivate(self, user_id: int) -> User:
        """Deactivate user account."""
        user = self.get(user_id)
        if user:
            user.is_active = False
            user.refresh_token = None
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def activate(self, user_id: int) -> User:
        """Activate user account."""
        user = self.get(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user
