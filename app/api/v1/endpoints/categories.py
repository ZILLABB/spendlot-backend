"""
Category management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryTree,
    CategoryStats
)
from app.services.categorization_service import CategorizationService
from app.api.v1.dependencies import get_current_active_user, get_current_superuser
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Category])
async def get_categories(
    include_inactive: bool = Query(False),
    parent_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all categories.
    """
    categorization_service = CategorizationService(db)
    
    filters = {}
    if not include_inactive:
        filters["is_active"] = True
    if parent_id is not None:
        filters["parent_id"] = parent_id
    
    categories = categorization_service.get_multi(filters=filters)
    return categories


@router.get("/tree", response_model=CategoryTree)
async def get_category_tree(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get categories in tree structure.
    """
    categorization_service = CategorizationService(db)
    
    # Get top-level categories
    top_level = categorization_service.get_multi(
        filters={"parent_id": None, "is_active": True}
    )
    
    # For each top-level category, get its children
    for category in top_level:
        children = categorization_service.get_multi(
            filters={"parent_id": category.id, "is_active": True}
        )
        category.children = children
    
    return CategoryTree(categories=top_level)


@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
    categorization_service = CategorizationService(db)
    category = categorization_service.get(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.post("/", response_model=Category)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new category.
    """
    categorization_service = CategorizationService(db)
    
    # Check if parent category exists
    if category_data.parent_id:
        parent = categorization_service.get(category_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )
    
    category = categorization_service.create(obj_in=category_data)
    return category


@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a category.
    """
    categorization_service = CategorizationService(db)
    category = categorization_service.get(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Don't allow updating system categories
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update system categories"
        )
    
    updated_category = categorization_service.update(
        db_obj=category,
        obj_in=category_update
    )
    return updated_category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a category (soft delete by setting is_active=False).
    """
    categorization_service = CategorizationService(db)
    category = categorization_service.get(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Don't allow deleting system categories
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system categories"
        )
    
    # Check if category has children
    children = categorization_service.get_multi(filters={"parent_id": category_id})
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories"
        )
    
    # Soft delete by setting is_active=False
    categorization_service.update(
        db_obj=category,
        obj_in={"is_active": False}
    )
    
    return {"message": "Category deleted successfully"}


@router.get("/{category_id}/stats", response_model=CategoryStats)
async def get_category_stats(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific category.
    """
    from app.services.transaction_service import TransactionService
    from sqlalchemy import func
    
    categorization_service = CategorizationService(db)
    category = categorization_service.get(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Get transaction statistics
    transaction_service = TransactionService(db)
    
    # Count transactions in this category
    transaction_count = db.query(transaction_service.model).filter(
        transaction_service.model.user_id == current_user.id,
        transaction_service.model.category_id == category_id
    ).count()
    
    # Calculate total and average amounts
    stats = db.query(
        func.sum(func.abs(transaction_service.model.amount)).label('total_amount'),
        func.avg(func.abs(transaction_service.model.amount)).label('avg_amount')
    ).filter(
        transaction_service.model.user_id == current_user.id,
        transaction_service.model.category_id == category_id
    ).first()
    
    total_amount = float(stats.total_amount) if stats.total_amount else 0.0
    avg_amount = float(stats.avg_amount) if stats.avg_amount else 0.0
    
    # Calculate percentage of total spending
    total_user_spending = db.query(
        func.sum(func.abs(transaction_service.model.amount))
    ).filter(
        transaction_service.model.user_id == current_user.id,
        transaction_service.model.amount < 0  # Only expenses
    ).scalar() or 0
    
    percentage_of_total = (total_amount / total_user_spending * 100) if total_user_spending > 0 else 0.0
    
    return CategoryStats(
        category=category,
        transaction_count=transaction_count,
        total_amount=total_amount,
        avg_amount=avg_amount,
        percentage_of_total=round(percentage_of_total, 2)
    )


@router.post("/initialize-defaults")
async def initialize_default_categories(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Initialize default categories (admin only).
    """
    categorization_service = CategorizationService(db)
    categories = categorization_service.initialize_default_categories()
    
    return {
        "message": f"Initialized {len(categories)} default categories",
        "categories": [cat.name for cat in categories]
    }
