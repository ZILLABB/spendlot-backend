"""
Receipt-related Pydantic schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ReceiptLineItem(BaseModel):
    """Schema for receipt line items."""
    
    description: str = Field(..., description="Item description")
    quantity: Optional[float] = Field(None, description="Item quantity")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    total_price: Decimal = Field(..., description="Total price for this item")


class ReceiptBase(BaseModel):
    """Base receipt schema with common fields."""
    
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    amount: Optional[Decimal] = Field(None, description="Receipt total amount")
    currency: str = Field(default="USD", description="Currency code")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    tip_amount: Optional[Decimal] = Field(None, description="Tip amount")
    subtotal: Optional[Decimal] = Field(None, description="Subtotal before tax and tip")


class ReceiptCreate(ReceiptBase):
    """Schema for creating a new receipt."""
    
    category_id: Optional[int] = Field(None, description="Category ID")
    notes: Optional[str] = Field(None, description="Additional notes")


class ReceiptUpdate(BaseModel):
    """Schema for updating receipt information."""
    
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    amount: Optional[Decimal] = Field(None, description="Receipt total amount")
    transaction_date: Optional[datetime] = Field(None, description="Transaction date")
    category_id: Optional[int] = Field(None, description="Category ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_verified: Optional[bool] = Field(None, description="Verification status")


class ReceiptInDB(ReceiptBase):
    """Schema for receipt data stored in database."""
    
    id: int = Field(..., description="Receipt ID")
    user_id: int = Field(..., description="User ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    data_source_id: int = Field(..., description="Data source ID")
    
    # File information
    original_filename: Optional[str] = Field(None, description="Original filename")
    file_path: Optional[str] = Field(None, description="File storage path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="File MIME type")
    
    # Processing information
    processing_status: str = Field(..., description="Processing status")
    ocr_confidence: Optional[Decimal] = Field(None, description="OCR confidence score")
    
    # Status flags
    is_verified: bool = Field(..., description="Verification status")
    is_duplicate: bool = Field(..., description="Duplicate status")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class Receipt(ReceiptInDB):
    """Public receipt schema."""
    
    line_items: Optional[List[ReceiptLineItem]] = Field(None, description="Receipt line items")
    category_name: Optional[str] = Field(None, description="Category name")
    data_source_name: Optional[str] = Field(None, description="Data source name")


class ReceiptUploadResponse(BaseModel):
    """Receipt upload response schema."""
    
    receipt_id: int = Field(..., description="Created receipt ID")
    upload_id: str = Field(..., description="Upload identifier")
    processing_status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Response message")


class ReceiptOCRResult(BaseModel):
    """OCR processing result schema."""
    
    receipt_id: int = Field(..., description="Receipt ID")
    extracted_text: str = Field(..., description="Extracted text from OCR")
    confidence: float = Field(..., description="OCR confidence score")
    extracted_data: Dict[str, Any] = Field(..., description="Structured extracted data")
    line_items: List[ReceiptLineItem] = Field(..., description="Extracted line items")
    processing_time: float = Field(..., description="Processing time in seconds")
