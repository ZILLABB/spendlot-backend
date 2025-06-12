"""
Transaction model for bank transactions and financial data.
"""
from sqlalchemy import Column, String, Text, Numeric, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.models.base import BaseModel


class Transaction(BaseModel):
    """Transaction model for bank transactions and financial data."""
    
    __tablename__ = "transactions"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic transaction information
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    description = Column(Text, nullable=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    
    # Transaction type
    transaction_type = Column(String(20), nullable=False, index=True)  # 'debit', 'credit', 'transfer'
    is_pending = Column(Boolean, default=False, nullable=False)
    
    # Merchant information
    merchant_name = Column(String(255), nullable=True, index=True)
    merchant_category = Column(String(100), nullable=True)
    
    # Account information
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True, index=True)
    account_name = Column(String(255), nullable=True)
    
    # External system IDs
    plaid_transaction_id = Column(String(255), nullable=True, unique=True, index=True)
    bank_transaction_id = Column(String(255), nullable=True)
    
    # Location information
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    address = Column(Text, nullable=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    auto_categorized = Column(Boolean, default=False, nullable=False)
    subcategory = Column(String(100), nullable=True)
    
    # Receipt linking
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=True, index=True)
    has_receipt = Column(Boolean, default=False, nullable=False)
    
    # Duplicate detection
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Data source
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    
    # Processing status
    processing_status = Column(String(50), default="completed", nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Additional data
    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    account = relationship("BankAccount", back_populates="transactions")
    receipt = relationship("Receipt")
    data_source = relationship("DataSource", back_populates="transactions")
    duplicate_of = relationship("Transaction", remote_side="Transaction.id")
    duplicates = relationship("Transaction", remote_side="Transaction.duplicate_of_id")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, merchant='{self.merchant_name}')>"
    
    @property
    def is_income(self) -> bool:
        """Check if transaction is income (positive amount)."""
        return self.amount > 0
    
    @property
    def is_expense(self) -> bool:
        """Check if transaction is expense (negative amount)."""
        return self.amount < 0
    
    @property
    def absolute_amount(self) -> Decimal:
        """Get absolute value of transaction amount."""
        return abs(self.amount)
