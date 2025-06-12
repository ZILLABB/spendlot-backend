"""
Transaction management endpoints.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionSummary,
    SpendingSummary
)
from app.schemas.common import PaginatedResponse
from app.services.transaction_service import TransactionService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Transaction])
async def get_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    merchant_name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    is_pending: Optional[bool] = Query(None),
    has_receipt: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's transactions with pagination and filtering.
    """
    transaction_service = TransactionService(db)
    
    # Build filters
    filters = {}
    if account_id:
        filters["account_id"] = account_id
    if category_id:
        filters["category_id"] = category_id
    if merchant_name:
        filters["merchant_name"] = merchant_name
    if description:
        filters["description"] = description
    if transaction_type:
        filters["transaction_type"] = transaction_type
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if min_amount:
        filters["min_amount"] = min_amount
    if max_amount:
        filters["max_amount"] = max_amount
    if is_pending is not None:
        filters["is_pending"] = is_pending
    if has_receipt is not None:
        filters["has_receipt"] = has_receipt
    
    # Get transactions and count
    skip = (page - 1) * size
    transactions = transaction_service.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        filters=filters
    )
    total = transaction_service.count_by_user(current_user.id, filters)
    
    # Calculate pagination info
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=transactions,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific transaction by ID.
    """
    transaction_service = TransactionService(db)
    transaction = transaction_service.get(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this transaction"
        )
    
    return transaction


@router.post("/", response_model=Transaction)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction manually.
    """
    transaction_service = TransactionService(db)
    
    # Add user_id to transaction data
    transaction_dict = transaction_data.dict()
    transaction_dict["user_id"] = current_user.id
    
    # Get manual data source
    from app.services.data_source_service import DataSourceService
    data_source_service = DataSourceService(db)
    manual_source = data_source_service.get_by_name("manual_entry")
    if not manual_source:
        # Create manual entry data source if it doesn't exist
        manual_source = data_source_service.create({
            "name": "manual_entry",
            "display_name": "Manual Entry",
            "description": "Manually entered transactions",
            "source_type": "manual",
            "is_system": True
        })
    
    transaction_dict["data_source_id"] = manual_source.id
    transaction_dict["processing_status"] = "completed"
    
    transaction = transaction_service.create(obj_in=transaction_dict)
    return transaction


@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a transaction.
    """
    transaction_service = TransactionService(db)
    transaction = transaction_service.get(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this transaction"
        )
    
    updated_transaction = transaction_service.update(
        db_obj=transaction,
        obj_in=transaction_update
    )
    return updated_transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a transaction.
    """
    transaction_service = TransactionService(db)
    transaction = transaction_service.get(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this transaction"
        )
    
    transaction_service.delete(id=transaction_id)
    return {"message": "Transaction deleted successfully"}


@router.get("/summary/current-month", response_model=TransactionSummary)
async def get_current_month_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction summary for current month.
    """
    transaction_service = TransactionService(db)
    
    # Get current month date range
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    
    summary = transaction_service.get_spending_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return TransactionSummary(
        total_income=summary["total_income"],
        total_expenses=summary["total_expenses"],
        net_amount=summary["net_amount"],
        transaction_count=summary["transaction_count"],
        avg_transaction_amount=summary["avg_transaction_amount"]
    )


@router.get("/summary/spending", response_model=SpendingSummary)
async def get_spending_summary(
    period: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed spending summary with category breakdown.
    """
    transaction_service = TransactionService(db)
    
    # Set default date range if not provided
    if not start_date or not end_date:
        now = datetime.now()
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "weekly":
            start_date = now - timedelta(days=7)
            end_date = now
        else:  # monthly
            start_date = datetime(now.year, now.month, 1)
            if now.month == 12:
                end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    
    # Get summary data
    summary = transaction_service.get_spending_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get category breakdown
    top_categories = transaction_service.get_category_breakdown(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get daily breakdown
    daily_breakdown = transaction_service.get_daily_spending(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return SpendingSummary(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total_spent=summary["total_expenses"],
        total_income=summary["total_income"],
        transaction_count=summary["transaction_count"],
        top_categories=top_categories,
        daily_breakdown=daily_breakdown
    )
