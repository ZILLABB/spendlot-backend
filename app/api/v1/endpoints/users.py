"""
User management endpoints.
"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserProfile
from app.services.user_service import UserService
from app.services.receipt_service import ReceiptService
from app.services.transaction_service import TransactionService
from app.services.bank_account_service import BankAccountService
from app.api.v1.dependencies import get_current_active_user, get_current_superuser

router = APIRouter()


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information.
    """
    user_service = UserService(db)
    updated_user = user_service.update(db_obj=current_user, obj_in=user_update)
    return updated_user


@router.get("/me/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user profile with statistics.
    """
    # Initialize services
    receipt_service = ReceiptService(db)
    transaction_service = TransactionService(db)
    bank_account_service = BankAccountService(db)

    # Calculate total receipts
    total_receipts = receipt_service.count_by_user(current_user.id)

    # Calculate total transactions
    total_transactions = transaction_service.count_by_user(current_user.id)

    # Calculate total spent this month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    end_of_month = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)

    # Get spending summary for current month
    monthly_summary = transaction_service.get_spending_summary(
        user_id=current_user.id,
        start_date=start_of_month,
        end_date=end_of_month
    )
    total_spent_this_month = float(monthly_summary.get("total_expenses", 0.0))

    # Count connected bank accounts
    connected_accounts = len(bank_account_service.get_by_user(current_user.id))

    return UserProfile(
        user=current_user,
        total_receipts=total_receipts,
        total_transactions=total_transactions,
        total_spent_this_month=total_spent_this_month,
        connected_accounts=connected_accounts
    )


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user account.
    """
    user_service = UserService(db)
    user_service.deactivate(current_user.id)
    return {"message": "Account deactivated successfully"}


# Admin endpoints
@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only).
    """
    user_service = UserService(db)
    users = user_service.get_multi(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).
    """
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Update user by ID (admin only).
    """
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_service.update(db_obj=user, obj_in=user_update)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Deactivate user by ID (admin only).
    """
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_service.deactivate(user_id)
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Activate user by ID (admin only).
    """
    user_service = UserService(db)
    user = user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_service.activate(user_id)
    return {"message": "User activated successfully"}
