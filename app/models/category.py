"""
Category model for transaction categorization.
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Category(BaseModel):
    """Category model for organizing transactions and receipts."""
    
    __tablename__ = "categories"
    
    # Basic category information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # Category hierarchy
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)  # 0 = top level, 1 = subcategory, etc.
    
    # Category properties
    is_system = Column(Boolean, default=False, nullable=False)  # System-defined vs user-defined
    is_active = Column(Boolean, default=True, nullable=False)
    is_income = Column(Boolean, default=False, nullable=False)  # True for income categories
    
    # Keywords for automatic categorization
    keywords = Column(Text, nullable=True)  # JSON array of keywords
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="category")
    receipts = relationship("Receipt", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    @property
    def full_name(self) -> str:
        """Get full category name including parent hierarchy."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
