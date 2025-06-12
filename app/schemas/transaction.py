"""
Transaction-related Pydantic schemas.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    """Base transaction schema with common fields."""
    
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    description: Optional[str] = Field(None, description="Transaction description")
    transaction_date: datetime = Field(..., description="Transaction date")
    transaction_type: str = Field(..., description="Transaction type (debit/credit/transfer)")
    merchant_name: Optional[str] = Field(None, description="Merchant name")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    
    account_id: Optional[int] = Field(None, description="Bank account ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    receipt_id: Optional[int] = Field(None, description="Associated receipt ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Transaction tags")


class TransactionUpdate(BaseModel):
    """Schema for updating transaction information."""
    
    description: Optional[str] = Field(None, description="Transaction description")
    category_id: Optional[int] = Field(None, description="Category ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Transaction tags")
    is_verified: Optional[bool] = Field(None, description="Verification status")


class TransactionInDB(TransactionBase):
    """Schema for transaction data stored in database."""
    
    id: int = Field(..., description="Transaction ID")
    user_id: int = Field(..., description="User ID")
    account_id: Optional[int] = Field(None, description="Bank account ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    receipt_id: Optional[int] = Field(None, description="Associated receipt ID")
    data_source_id: int = Field(..., description="Data source ID")
    
    # External IDs
    plaid_transaction_id: Optional[str] = Field(None, description="Plaid transaction ID")
    bank_transaction_id: Optional[str] = Field(None, description="Bank transaction ID")
    
    # Status and flags
    is_pending: bool = Field(..., description="Pending status")
    is_verified: bool = Field(..., description="Verification status")
    is_duplicate: bool = Field(..., description="Duplicate status")
    has_receipt: bool = Field(..., description="Has associated receipt")
    auto_categorized: bool = Field(..., description="Auto-categorized status")
    
    # Additional data
    merchant_category: Optional[str] = Field(None, description="Merchant category")
    subcategory: Optional[str] = Field(None, description="Transaction subcategory")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Transaction tags")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class Transaction(TransactionInDB):
    """Public transaction schema."""
    
    category_name: Optional[str] = Field(None, description="Category name")
    account_name: Optional[str] = Field(None, description="Account name")
    data_source_name: Optional[str] = Field(None, description="Data source name")


class TransactionSummary(BaseModel):
    """Transaction summary schema."""
    
    total_income: Decimal = Field(..., description="Total income")
    total_expenses: Decimal = Field(..., description="Total expenses")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    transaction_count: int = Field(..., description="Total number of transactions")
    avg_transaction_amount: Decimal = Field(..., description="Average transaction amount")


class SpendingSummary(BaseModel):
    """Spending summary schema."""
    
    period: str = Field(..., description="Summary period (daily, weekly, monthly)")
    start_date: datetime = Field(..., description="Period start date")
    end_date: datetime = Field(..., description="Period end date")
    total_spent: Decimal = Field(..., description="Total amount spent")
    total_income: Decimal = Field(..., description="Total income")
    transaction_count: int = Field(..., description="Number of transactions")
    top_categories: List[dict] = Field(..., description="Top spending categories")
    daily_breakdown: List[dict] = Field(..., description="Daily spending breakdown")
