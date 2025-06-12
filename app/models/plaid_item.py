"""
Plaid item model for managing Plaid connections.
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PlaidItem(BaseModel):
    """Plaid item model for managing bank connections via Plaid."""
    
    __tablename__ = "plaid_items"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Plaid identifiers
    plaid_item_id = Column(String(255), nullable=False, unique=True, index=True)
    plaid_access_token = Column(Text, nullable=False)  # Encrypted
    plaid_public_token = Column(Text, nullable=True)   # Encrypted
    
    # Institution information
    institution_id = Column(String(100), nullable=False)
    institution_name = Column(String(255), nullable=False)
    
    # Item status
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="good", nullable=False)  # good, bad, requires_update
    
    # Error handling
    error_type = Column(String(100), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Webhook information
    webhook_url = Column(String(500), nullable=True)
    
    # Available products
    available_products = Column(JSON, nullable=True)  # Array of available Plaid products
    billed_products = Column(JSON, nullable=True)     # Array of billed Plaid products
    
    # Consent information
    consent_expiration_time = Column(DateTime, nullable=True)
    update_type = Column(String(50), nullable=True)
    
    # Sync information
    last_successful_update = Column(DateTime, nullable=True)
    last_failed_update = Column(DateTime, nullable=True)
    cursor = Column(String(255), nullable=True)  # For incremental updates
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="plaid_items")
    accounts = relationship("BankAccount", back_populates="plaid_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PlaidItem(id={self.id}, institution='{self.institution_name}', status='{self.status}')>"
