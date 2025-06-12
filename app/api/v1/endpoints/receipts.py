"""
Receipt management endpoints.
"""
import os
import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.receipt import (
    Receipt,
    ReceiptCreate,
    ReceiptUpdate,
    ReceiptUploadResponse
)
from app.schemas.common import PaginatedResponse
from app.services.receipt_service import ReceiptService
from app.services.data_source_service import DataSourceService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User
from app.tasks.ocr_tasks import process_receipt_ocr

router = APIRouter()


@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    merchant_name: Optional[str] = Form(None),
    amount: Optional[Decimal] = Form(None),
    transaction_date: Optional[datetime] = Form(None),
    category_id: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a receipt image or PDF for processing.
    """
    # Validate file type
    allowed_extensions = settings.ALLOWED_EXTENSIONS.split(",")
    file_extension = file.filename.split(".")[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique filename
    upload_id = str(uuid.uuid4())
    filename = f"{upload_id}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get manual upload data source
    data_source_service = DataSourceService(db)
    manual_source = data_source_service.get_by_name("manual_upload")
    if not manual_source:
        # Create manual upload data source if it doesn't exist
        manual_source = data_source_service.create_manual_upload_source()
    
    # Create receipt record
    receipt_service = ReceiptService(db)
    receipt = receipt_service.create_from_upload(
        user_id=current_user.id,
        file_path=file_path,
        original_filename=file.filename,
        file_size=file.size,
        mime_type=file.content_type,
        data_source_id=manual_source.id
    )
    
    # Update with manual data if provided
    if any([merchant_name, amount, transaction_date, category_id, notes]):
        update_data = {}
        if merchant_name:
            update_data["merchant_name"] = merchant_name
        if amount:
            update_data["amount"] = amount
        if transaction_date:
            update_data["transaction_date"] = transaction_date
        if category_id:
            update_data["category_id"] = category_id
        if notes:
            update_data["notes"] = notes
        
        receipt = receipt_service.update(db_obj=receipt, obj_in=update_data)
    
    # Queue OCR processing
    process_receipt_ocr.delay(receipt.id)
    
    return ReceiptUploadResponse(
        receipt_id=receipt.id,
        upload_id=upload_id,
        processing_status=receipt.processing_status,
        message="Receipt uploaded successfully and queued for processing"
    )


@router.get("/", response_model=PaginatedResponse[Receipt])
async def get_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    merchant_name: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    processing_status: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's receipts with pagination and filtering.
    """
    receipt_service = ReceiptService(db)
    
    # Build filters
    filters = {}
    if merchant_name:
        filters["merchant_name"] = merchant_name
    if category_id:
        filters["category_id"] = category_id
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if min_amount:
        filters["min_amount"] = min_amount
    if max_amount:
        filters["max_amount"] = max_amount
    if processing_status:
        filters["processing_status"] = processing_status
    if is_verified is not None:
        filters["is_verified"] = is_verified
    
    # Get receipts and count
    skip = (page - 1) * size
    receipts = receipt_service.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        filters=filters
    )
    total = receipt_service.count_by_user(current_user.id, filters)
    
    # Calculate pagination info
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=receipts,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{receipt_id}", response_model=Receipt)
async def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific receipt by ID.
    """
    receipt_service = ReceiptService(db)
    receipt = receipt_service.get(receipt_id)
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this receipt"
        )
    
    return receipt


@router.put("/{receipt_id}", response_model=Receipt)
async def update_receipt(
    receipt_id: int,
    receipt_update: ReceiptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a receipt.
    """
    receipt_service = ReceiptService(db)
    receipt = receipt_service.get(receipt_id)
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this receipt"
        )
    
    updated_receipt = receipt_service.update(db_obj=receipt, obj_in=receipt_update)
    return updated_receipt


@router.delete("/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a receipt.
    """
    receipt_service = ReceiptService(db)
    receipt = receipt_service.get(receipt_id)
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this receipt"
        )
    
    # Delete file if it exists
    if receipt.file_path and os.path.exists(receipt.file_path):
        try:
            os.remove(receipt.file_path)
        except Exception:
            pass  # Continue even if file deletion fails
    
    receipt_service.delete(id=receipt_id)
    return {"message": "Receipt deleted successfully"}


@router.post("/{receipt_id}/reprocess")
async def reprocess_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reprocess a receipt with OCR.
    """
    receipt_service = ReceiptService(db)
    receipt = receipt_service.get(receipt_id)
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    if receipt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reprocess this receipt"
        )
    
    # Reset processing status
    receipt_service.update_processing_status(receipt_id, "pending")
    
    # Queue OCR processing
    process_receipt_ocr.delay(receipt_id)
    
    return {"message": "Receipt queued for reprocessing"}
