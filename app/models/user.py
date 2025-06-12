"""
User model for authentication and user management.
"""
from sqlalchemy import Boolean, Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class User(BaseModel):
    """User model for storing user account information."""
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    profile_picture_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Authentication tokens
    refresh_token = Column(Text, nullable=True)
    
    # External service tokens (encrypted)
    gmail_token = Column(Text, nullable=True)
    plaid_access_token = Column(Text, nullable=True)
    
    # Verification
    email_verification_token = Column(String(255), nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Last activity
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="user", cascade="all, delete-orphan")
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
