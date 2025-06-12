"""
User management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import User, UserUpdate, UserProfile
from app.services.user_service import UserService
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
    # TODO: Implement statistics calculation
    # For now, return basic profile
    return UserProfile(
        user=current_user,
        total_receipts=0,
        total_transactions=0,
        total_spent_this_month=0.0,
        connected_accounts=0
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
