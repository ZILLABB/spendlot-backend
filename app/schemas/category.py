"""
Category-related Pydantic schemas.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    
    name: str = Field(..., max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, description="Icon identifier")
    is_income: bool = Field(default=False, description="Whether this is an income category")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    keywords: Optional[List[str]] = Field(None, description="Keywords for auto-categorization")


class CategoryUpdate(BaseModel):
    """Schema for updating category information."""
    
    name: Optional[str] = Field(None, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, description="Icon identifier")
    is_active: Optional[bool] = Field(None, description="Category active status")
    keywords: Optional[List[str]] = Field(None, description="Keywords for auto-categorization")


class CategoryInDB(CategoryBase):
    """Schema for category data stored in database."""
    
    id: int = Field(..., description="Category ID")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    level: int = Field(..., description="Category hierarchy level")
    is_system: bool = Field(..., description="Whether this is a system category")
    is_active: bool = Field(..., description="Category active status")
    keywords: Optional[List[str]] = Field(None, description="Keywords for auto-categorization")
    
    class Config:
        from_attributes = True


class Category(CategoryInDB):
    """Public category schema."""
    
    full_name: Optional[str] = Field(None, description="Full category name with hierarchy")
    children: Optional[List["Category"]] = Field(None, description="Child categories")


class CategoryTree(BaseModel):
    """Category tree structure."""
    
    categories: List[Category] = Field(..., description="Top-level categories with children")


class CategoryStats(BaseModel):
    """Category statistics schema."""
    
    category: Category
    transaction_count: int = Field(..., description="Number of transactions in this category")
    total_amount: float = Field(..., description="Total amount spent in this category")
    avg_amount: float = Field(..., description="Average transaction amount")
    percentage_of_total: float = Field(..., description="Percentage of total spending")


# Update forward references
Category.model_rebuild()
