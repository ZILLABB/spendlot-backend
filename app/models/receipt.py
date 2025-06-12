"""
Receipt model for storing receipt information and OCR data.
"""
from sqlalchemy import Column, String, Text, Numeric, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.models.base import BaseModel


class Receipt(BaseModel):
    """Receipt model for storing receipt data from various sources."""
    
    __tablename__ = "receipts"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic receipt information
    merchant_name = Column(String(255), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    transaction_date = Column(DateTime, nullable=True, index=True)
    
    # Receipt details
    receipt_number = Column(String(100), nullable=True)
    tax_amount = Column(Numeric(10, 2), nullable=True)
    tip_amount = Column(Numeric(10, 2), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=True)
    
    # Location information
    merchant_address = Column(Text, nullable=True)
    merchant_phone = Column(String(20), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # File information
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # OCR and processing
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Numeric(5, 2), nullable=True)  # 0-100
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Extracted line items (JSON)
    line_items = Column(JSON, nullable=True)
    
    # Verification and status
    is_verified = Column(Boolean, default=False, nullable=False)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(Integer, ForeignKey("receipts.id"), nullable=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    auto_categorized = Column(Boolean, default=False, nullable=False)
    
    # Data source
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    external_id = Column(String(255), nullable=True)  # ID from external system
    
    # Additional metadata
    extra_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="receipts")
    category = relationship("Category", back_populates="receipts")
    data_source = relationship("DataSource", back_populates="receipts")
    duplicate_of = relationship("Receipt", remote_side="Receipt.id")
    duplicates = relationship("Receipt", remote_side="Receipt.duplicate_of_id")
    
    def __repr__(self):
        return f"<Receipt(id={self.id}, merchant='{self.merchant_name}', amount={self.amount})>"
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount including tax and tip."""
        total = self.amount or Decimal('0')
        if self.tax_amount:
            total += self.tax_amount
        if self.tip_amount:
            total += self.tip_amount
        return total
