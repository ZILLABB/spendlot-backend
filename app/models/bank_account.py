"""
Bank account model for storing user's connected bank accounts.
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BankAccount(BaseModel):
    """Bank account model for user's connected financial accounts."""
    
    __tablename__ = "bank_accounts"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Account identification
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # 'checking', 'savings', 'credit', 'investment'
    account_subtype = Column(String(50), nullable=True)
    
    # Bank information
    institution_name = Column(String(255), nullable=False)
    institution_id = Column(String(100), nullable=True)
    
    # Account numbers (encrypted)
    account_number_encrypted = Column(Text, nullable=True)
    routing_number_encrypted = Column(Text, nullable=True)
    
    # Plaid integration
    plaid_account_id = Column(String(255), nullable=True, unique=True, index=True)
    plaid_item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=True, index=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Balance information
    current_balance = Column(Numeric(12, 2), nullable=True)
    available_balance = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    last_balance_update = Column(DateTime, nullable=True)
    
    # Sync settings
    auto_sync = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="active", nullable=False)  # active, error, disabled
    sync_error = Column(Text, nullable=True)
    
    # Account metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bank_accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    
    def __repr__(self):
        return f"<BankAccount(id={self.id}, name='{self.account_name}', type='{self.account_type}')>"
    
    @property
    def masked_account_number(self) -> str:
        """Get masked account number for display."""
        if not self.account_number_encrypted:
            return "****"
        # In a real implementation, you'd decrypt and mask
        return "****1234"
