"""
Bank account-related Pydantic schemas.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class BankAccountBase(BaseModel):
    """Base bank account schema with common fields."""
    
    account_name: str = Field(..., description="Account name")
    account_type: str = Field(..., description="Account type (checking, savings, credit, etc.)")
    institution_name: str = Field(..., description="Financial institution name")


class BankAccountCreate(BankAccountBase):
    """Schema for creating a new bank account."""
    
    account_subtype: Optional[str] = Field(None, description="Account subtype")
    is_primary: bool = Field(default=False, description="Primary account flag")


class BankAccountUpdate(BaseModel):
    """Schema for updating bank account information."""
    
    account_name: Optional[str] = Field(None, description="Account name")
    is_primary: Optional[bool] = Field(None, description="Primary account flag")
    auto_sync: Optional[bool] = Field(None, description="Auto-sync enabled")
    is_active: Optional[bool] = Field(None, description="Account active status")


class BankAccountInDB(BankAccountBase):
    """Schema for bank account data stored in database."""
    
    id: int = Field(..., description="Account ID")
    user_id: int = Field(..., description="User ID")
    account_subtype: Optional[str] = Field(None, description="Account subtype")
    institution_id: Optional[str] = Field(None, description="Institution ID")
    
    # Plaid integration
    plaid_account_id: Optional[str] = Field(None, description="Plaid account ID")
    plaid_item_id: Optional[int] = Field(None, description="Plaid item ID")
    
    # Account status
    is_active: bool = Field(..., description="Account active status")
    is_primary: bool = Field(..., description="Primary account flag")
    
    # Balance information
    current_balance: Optional[Decimal] = Field(None, description="Current balance")
    available_balance: Optional[Decimal] = Field(None, description="Available balance")
    currency: str = Field(..., description="Account currency")
    last_balance_update: Optional[datetime] = Field(None, description="Last balance update")
    
    # Sync information
    auto_sync: bool = Field(..., description="Auto-sync enabled")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_status: str = Field(..., description="Sync status")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class BankAccount(BankAccountInDB):
    """Public bank account schema."""
    
    masked_account_number: Optional[str] = Field(None, description="Masked account number")
    transaction_count: Optional[int] = Field(None, description="Number of transactions")


class PlaidLinkRequest(BaseModel):
    """Plaid Link request schema."""
    
    public_token: str = Field(..., description="Plaid public token")
    institution_id: str = Field(..., description="Institution ID")
    institution_name: str = Field(..., description="Institution name")
    accounts: list = Field(..., description="Selected accounts")


class PlaidLinkResponse(BaseModel):
    """Plaid Link response schema."""
    
    item_id: int = Field(..., description="Created Plaid item ID")
    accounts: list = Field(..., description="Created bank accounts")
    message: str = Field(..., description="Response message")
