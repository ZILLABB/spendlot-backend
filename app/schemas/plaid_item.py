"""
Plaid item-related Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PlaidItemBase(BaseModel):
    """Base Plaid item schema with common fields."""
    
    institution_id: str = Field(..., description="Institution ID")
    institution_name: str = Field(..., description="Institution name")


class PlaidItemCreate(PlaidItemBase):
    """Schema for creating a new Plaid item."""
    
    plaid_item_id: str = Field(..., description="Plaid item ID")
    plaid_access_token: str = Field(..., description="Plaid access token")
    plaid_public_token: Optional[str] = Field(None, description="Plaid public token")


class PlaidItemUpdate(BaseModel):
    """Schema for updating Plaid item information."""
    
    status: Optional[str] = Field(None, description="Item status")
    error_type: Optional[str] = Field(None, description="Error type")
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")


class PlaidItemInDB(PlaidItemBase):
    """Schema for Plaid item data stored in database."""
    
    id: int = Field(..., description="Plaid item ID")
    user_id: int = Field(..., description="User ID")
    plaid_item_id: str = Field(..., description="Plaid item ID")
    is_active: bool = Field(..., description="Active status")
    status: str = Field(..., description="Item status")
    error_type: Optional[str] = Field(None, description="Error type")
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    available_products: Optional[List[str]] = Field(None, description="Available products")
    billed_products: Optional[List[str]] = Field(None, description="Billed products")
    consent_expiration_time: Optional[datetime] = Field(None, description="Consent expiration")
    last_successful_update: Optional[datetime] = Field(None, description="Last successful update")
    last_failed_update: Optional[datetime] = Field(None, description="Last failed update")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class PlaidItem(PlaidItemInDB):
    """Public Plaid item schema."""
    
    pass


class PlaidLinkTokenRequest(BaseModel):
    """Plaid Link token request schema."""
    
    user_id: int = Field(..., description="User ID")


class PlaidLinkTokenResponse(BaseModel):
    """Plaid Link token response schema."""
    
    link_token: str = Field(..., description="Link token")
    expiration: str = Field(..., description="Token expiration")


class PlaidPublicTokenExchangeRequest(BaseModel):
    """Plaid public token exchange request schema."""
    
    public_token: str = Field(..., description="Public token from Plaid Link")
    institution_id: str = Field(..., description="Institution ID")
    institution_name: str = Field(..., description="Institution name")
    account_ids: List[str] = Field(..., description="Selected account IDs")


class PlaidWebhookRequest(BaseModel):
    """Plaid webhook request schema."""
    
    webhook_type: str = Field(..., description="Webhook type")
    webhook_code: str = Field(..., description="Webhook code")
    item_id: str = Field(..., description="Plaid item ID")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")
    new_transactions: Optional[int] = Field(None, description="Number of new transactions")
    removed_transactions: Optional[List[str]] = Field(None, description="Removed transaction IDs")
