"""
Authentication-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class Token(BaseModel):
    """JWT token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data schema."""
    
    sub: Optional[str] = Field(None, description="Subject (user ID)")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    type: Optional[str] = Field(None, description="Token type")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
