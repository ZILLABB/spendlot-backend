"""
Analytics and reporting endpoints.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import SpendingSummary
from app.schemas.category import CategoryStats
from app.services.transaction_service import TransactionService
from app.services.categorization_service import CategorizationService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/spending-summary", response_model=SpendingSummary)
async def get_spending_summary(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive spending summary with category breakdown.
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
        elif period == "yearly":
            start_date = datetime(now.year, 1, 1)
            end_date = datetime(now.year, 12, 31, 23, 59, 59)
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


@router.get("/category-stats", response_model=List[CategoryStats])
async def get_category_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for all categories.
    """
    from sqlalchemy import func
    from app.models.category import Category
    from app.models.transaction import Transaction
    
    # Set default date range (current month)
    if not start_date or not end_date:
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    
    # Query category statistics
    query = db.query(
        Category,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.avg(func.abs(Transaction.amount)).label('avg_amount')
    ).outerjoin(
        Transaction,
        (Transaction.category_id == Category.id) &
        (Transaction.user_id == current_user.id) &
        (Transaction.transaction_date >= start_date) &
        (Transaction.transaction_date <= end_date) &
        (Transaction.amount < 0)  # Only expenses
    ).filter(
        Category.is_active == True
    ).group_by(Category.id).order_by(func.sum(func.abs(Transaction.amount)).desc()).limit(limit)
    
    results = query.all()
    
    # Calculate total spending for percentage calculation
    total_spending = sum(r.total_amount for r in results if r.total_amount)
    
    category_stats = []
    for result in results:
        total_amount = float(result.total_amount) if result.total_amount else 0.0
        avg_amount = float(result.avg_amount) if result.avg_amount else 0.0
        percentage = (total_amount / total_spending * 100) if total_spending > 0 else 0.0
        
        category_stats.append(CategoryStats(
            category=result.Category,
            transaction_count=result.transaction_count,
            total_amount=total_amount,
            avg_amount=avg_amount,
            percentage_of_total=round(percentage, 2)
        ))
    
    return category_stats


@router.get("/monthly-trends")
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly spending trends.
    """
    from sqlalchemy import func, extract
    from app.models.transaction import Transaction
    
    # Calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # Query monthly spending
    query = db.query(
        extract('year', Transaction.transaction_date).label('year'),
        extract('month', Transaction.transaction_date).label('month'),
        func.sum(func.abs(Transaction.amount)).label('total_spent'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= start_date,
        Transaction.amount < 0  # Only expenses
    ).group_by(
        extract('year', Transaction.transaction_date),
        extract('month', Transaction.transaction_date)
    ).order_by('year', 'month')
    
    results = query.all()
    
    monthly_trends = []
    for result in results:
        monthly_trends.append({
            "year": int(result.year),
            "month": int(result.month),
            "total_spent": float(result.total_spent),
            "transaction_count": result.transaction_count,
            "month_name": datetime(int(result.year), int(result.month), 1).strftime("%B %Y")
        })
    
    return {
        "trends": monthly_trends,
        "period": f"Last {months} months"
    }


@router.get("/receipt-stats")
async def get_receipt_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get receipt processing statistics.
    """
    from sqlalchemy import func
    from app.models.receipt import Receipt
    
    # Query receipt statistics
    total_receipts = db.query(func.count(Receipt.id)).filter(
        Receipt.user_id == current_user.id
    ).scalar()
    
    processed_receipts = db.query(func.count(Receipt.id)).filter(
        Receipt.user_id == current_user.id,
        Receipt.processing_status == "completed"
    ).scalar()
    
    pending_receipts = db.query(func.count(Receipt.id)).filter(
        Receipt.user_id == current_user.id,
        Receipt.processing_status == "pending"
    ).scalar()
    
    failed_receipts = db.query(func.count(Receipt.id)).filter(
        Receipt.user_id == current_user.id,
        Receipt.processing_status == "failed"
    ).scalar()
    
    verified_receipts = db.query(func.count(Receipt.id)).filter(
        Receipt.user_id == current_user.id,
        Receipt.is_verified == True
    ).scalar()
    
    # Calculate average OCR confidence
    avg_confidence = db.query(func.avg(Receipt.ocr_confidence)).filter(
        Receipt.user_id == current_user.id,
        Receipt.ocr_confidence.isnot(None)
    ).scalar()
    
    return {
        "total_receipts": total_receipts,
        "processed_receipts": processed_receipts,
        "pending_receipts": pending_receipts,
        "failed_receipts": failed_receipts,
        "verified_receipts": verified_receipts,
        "processing_rate": (processed_receipts / total_receipts * 100) if total_receipts > 0 else 0,
        "verification_rate": (verified_receipts / total_receipts * 100) if total_receipts > 0 else 0,
        "avg_ocr_confidence": float(avg_confidence) if avg_confidence else 0.0
    }
