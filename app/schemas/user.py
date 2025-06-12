"""
User-related Pydantic schemas.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")
    phone_number: Optional[str] = Field(None, description="User phone number")
    timezone: str = Field(default="UTC", description="User timezone")
    currency: str = Field(default="USD", description="User preferred currency")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    
    full_name: Optional[str] = Field(None, description="User full name")
    phone_number: Optional[str] = Field(None, description="User phone number")
    timezone: Optional[str] = Field(None, description="User timezone")
    currency: Optional[str] = Field(None, description="User preferred currency")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")


class UserInDB(UserBase):
    """Schema for user data stored in database."""
    
    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user schema (excludes sensitive information)."""
    
    pass


class UserProfile(BaseModel):
    """User profile schema with statistics."""
    
    user: User
    total_receipts: int = Field(..., description="Total number of receipts")
    total_transactions: int = Field(..., description="Total number of transactions")
    total_spent_this_month: float = Field(..., description="Total spent this month")
    connected_accounts: int = Field(..., description="Number of connected bank accounts")
