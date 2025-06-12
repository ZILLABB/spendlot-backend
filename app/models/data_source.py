"""
Data source model for tracking where transactions/receipts come from.
"""
from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DataSource(BaseModel):
    """Data source model for tracking transaction/receipt origins."""
    
    __tablename__ = "data_sources"
    
    # Basic source information
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Source type and configuration
    source_type = Column(String(50), nullable=False)  # 'manual', 'gmail', 'plaid', 'sms', 'api'
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Configuration settings (JSON)
    config = Column(JSON, nullable=True)
    
    # API/Integration details
    api_endpoint = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    
    # Processing settings
    auto_process = Column(Boolean, default=True, nullable=False)
    requires_verification = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="data_source")
    receipts = relationship("Receipt", back_populates="data_source")
    
    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"
