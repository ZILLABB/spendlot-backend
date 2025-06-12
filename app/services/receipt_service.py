"""
Receipt service for receipt management operations.
"""
import os
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.receipt import Receipt
from app.models.data_source import DataSource
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate
from app.services.base_service import BaseService
from app.core.config import settings


class ReceiptService(BaseService[Receipt, ReceiptCreate, ReceiptUpdate]):
    """Service for receipt management operations."""
    
    def __init__(self, db: Session):
        super().__init__(Receipt, db)
    
    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Receipt]:
        """Get receipts for a specific user."""
        query = self.db.query(Receipt).filter(Receipt.user_id == user_id)
        
        # Apply additional filters
        if filters:
            if filters.get("merchant_name"):
                query = query.filter(
                    Receipt.merchant_name.ilike(f"%{filters['merchant_name']}%")
                )
            
            if filters.get("category_id"):
                query = query.filter(Receipt.category_id == filters["category_id"])
            
            if filters.get("date_from"):
                query = query.filter(Receipt.transaction_date >= filters["date_from"])
            
            if filters.get("date_to"):
                query = query.filter(Receipt.transaction_date <= filters["date_to"])
            
            if filters.get("min_amount"):
                query = query.filter(Receipt.amount >= filters["min_amount"])
            
            if filters.get("max_amount"):
                query = query.filter(Receipt.amount <= filters["max_amount"])
            
            if filters.get("processing_status"):
                query = query.filter(Receipt.processing_status == filters["processing_status"])
            
            if filters.get("is_verified") is not None:
                query = query.filter(Receipt.is_verified == filters["is_verified"])
        
        return query.order_by(Receipt.transaction_date.desc()).offset(skip).limit(limit).all()
    
    def count_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count receipts for a specific user."""
        query = self.db.query(Receipt).filter(Receipt.user_id == user_id)
        
        # Apply same filters as get_by_user
        if filters:
            if filters.get("merchant_name"):
                query = query.filter(
                    Receipt.merchant_name.ilike(f"%{filters['merchant_name']}%")
                )
            
            if filters.get("category_id"):
                query = query.filter(Receipt.category_id == filters["category_id"])
            
            if filters.get("date_from"):
                query = query.filter(Receipt.transaction_date >= filters["date_from"])
            
            if filters.get("date_to"):
                query = query.filter(Receipt.transaction_date <= filters["date_to"])
            
            if filters.get("min_amount"):
                query = query.filter(Receipt.amount >= filters["min_amount"])
            
            if filters.get("max_amount"):
                query = query.filter(Receipt.amount <= filters["max_amount"])
            
            if filters.get("processing_status"):
                query = query.filter(Receipt.processing_status == filters["processing_status"])
            
            if filters.get("is_verified") is not None:
                query = query.filter(Receipt.is_verified == filters["is_verified"])
        
        return query.count()
    
    def create_from_upload(
        self,
        user_id: int,
        file_path: str,
        original_filename: str,
        file_size: int,
        mime_type: str,
        data_source_id: int
    ) -> Receipt:
        """Create receipt from file upload."""
        receipt = Receipt(
            user_id=user_id,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            data_source_id=data_source_id,
            processing_status="pending"
        )
        
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
    
    def update_processing_status(
        self,
        receipt_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Receipt]:
        """Update receipt processing status."""
        receipt = self.get(receipt_id)
        if receipt:
            receipt.processing_status = status
            if error_message:
                receipt.processing_error = error_message
            self.db.commit()
            self.db.refresh(receipt)
        return receipt
    
    def update_ocr_data(
        self,
        receipt_id: int,
        ocr_text: str,
        confidence: float,
        extracted_data: Dict[str, Any]
    ) -> Optional[Receipt]:
        """Update receipt with OCR results."""
        receipt = self.get(receipt_id)
        if receipt:
            receipt.ocr_text = ocr_text
            receipt.ocr_confidence = confidence
            
            # Update extracted fields
            if "merchant_name" in extracted_data:
                receipt.merchant_name = extracted_data["merchant_name"]
            
            if "amount" in extracted_data:
                receipt.amount = extracted_data["amount"]
            
            if "transaction_date" in extracted_data:
                receipt.transaction_date = extracted_data["transaction_date"]
            
            if "tax_amount" in extracted_data:
                receipt.tax_amount = extracted_data["tax_amount"]
            
            if "tip_amount" in extracted_data:
                receipt.tip_amount = extracted_data["tip_amount"]
            
            if "subtotal" in extracted_data:
                receipt.subtotal = extracted_data["subtotal"]
            
            if "line_items" in extracted_data:
                receipt.line_items = extracted_data["line_items"]
            
            receipt.processing_status = "completed"
            self.db.commit()
            self.db.refresh(receipt)
        
        return receipt
    
    def find_duplicates(self, receipt: Receipt) -> List[Receipt]:
        """Find potential duplicate receipts."""
        if not receipt.merchant_name or not receipt.amount or not receipt.transaction_date:
            return []
        
        # Look for receipts with same merchant, amount, and date (within 1 day)
        from datetime import timedelta
        
        date_range_start = receipt.transaction_date - timedelta(days=1)
        date_range_end = receipt.transaction_date + timedelta(days=1)
        
        duplicates = self.db.query(Receipt).filter(
            and_(
                Receipt.user_id == receipt.user_id,
                Receipt.id != receipt.id,
                Receipt.merchant_name == receipt.merchant_name,
                Receipt.amount == receipt.amount,
                Receipt.transaction_date >= date_range_start,
                Receipt.transaction_date <= date_range_end
            )
        ).all()
        
        return duplicates
    
    def mark_as_duplicate(self, receipt_id: int, duplicate_of_id: int) -> Optional[Receipt]:
        """Mark receipt as duplicate of another receipt."""
        receipt = self.get(receipt_id)
        if receipt:
            receipt.is_duplicate = True
            receipt.duplicate_of_id = duplicate_of_id
            self.db.commit()
            self.db.refresh(receipt)
        return receipt
    
    def get_unprocessed(self, limit: int = 10) -> List[Receipt]:
        """Get unprocessed receipts for background processing."""
        return self.db.query(Receipt).filter(
            Receipt.processing_status == "pending"
        ).limit(limit).all()
