"""
Service for automatic transaction and receipt categorization.
"""
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.category import Category
from app.models.receipt import Receipt
from app.models.transaction import Transaction
from app.services.base_service import BaseService
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategorizationService(BaseService[Category, CategoryCreate, CategoryUpdate]):
    """Service for automatic categorization of transactions and receipts."""
    
    def __init__(self, db: Session):
        super().__init__(Category, db)
    
    def auto_categorize_receipt(self, receipt: Receipt) -> Optional[Category]:
        """Automatically categorize a receipt based on merchant name and keywords."""
        if not receipt.merchant_name:
            return None
        
        merchant_name = receipt.merchant_name.lower()
        
        # Try to find category by merchant name keywords
        categories = self.db.query(Category).filter(
            Category.is_active == True,
            Category.keywords.isnot(None)
        ).all()
        
        for category in categories:
            if category.keywords:
                try:
                    keywords = json.loads(category.keywords) if isinstance(category.keywords, str) else category.keywords
                    for keyword in keywords:
                        if keyword.lower() in merchant_name:
                            return category
                except:
                    continue
        
        # Fallback to predefined merchant patterns
        category_patterns = {
            "food": ["restaurant", "cafe", "pizza", "burger", "food", "kitchen", "diner", "grill", "bistro"],
            "groceries": ["grocery", "supermarket", "market", "walmart", "target", "costco", "safeway"],
            "gas": ["gas", "fuel", "shell", "exxon", "bp", "chevron", "mobil"],
            "shopping": ["store", "shop", "retail", "amazon", "ebay", "mall"],
            "transport": ["uber", "lyft", "taxi", "bus", "train", "metro", "parking"],
            "entertainment": ["movie", "cinema", "theater", "netflix", "spotify", "game"],
            "utilities": ["electric", "water", "gas", "internet", "phone", "cable"],
            "healthcare": ["hospital", "clinic", "pharmacy", "doctor", "medical", "health"]
        }
        
        for category_name, patterns in category_patterns.items():
            for pattern in patterns:
                if pattern in merchant_name:
                    category = self.get_or_create_category(category_name)
                    return category
        
        return None
    
    def auto_categorize_transaction(self, transaction: Transaction) -> Optional[Category]:
        """Automatically categorize a transaction."""
        # Use merchant name if available
        if transaction.merchant_name:
            merchant_name = transaction.merchant_name.lower()
            
            # Check existing categories with keywords
            categories = self.db.query(Category).filter(
                Category.is_active == True,
                Category.keywords.isnot(None)
            ).all()
            
            for category in categories:
                if category.keywords:
                    try:
                        keywords = json.loads(category.keywords) if isinstance(category.keywords, str) else category.keywords
                        for keyword in keywords:
                            if keyword.lower() in merchant_name:
                                return category
                    except:
                        continue
        
        # Use description if merchant name not available
        if transaction.description:
            description = transaction.description.lower()
            
            # Predefined patterns for common transaction types
            if any(word in description for word in ["atm", "withdrawal", "cash"]):
                return self.get_or_create_category("cash")
            
            if any(word in description for word in ["transfer", "deposit"]):
                return self.get_or_create_category("transfer")
            
            if any(word in description for word in ["fee", "charge", "service"]):
                return self.get_or_create_category("fees")
        
        return None
    
    def get_or_create_category(self, name: str) -> Category:
        """Get existing category or create new one."""
        category = self.db.query(Category).filter(
            func.lower(Category.name) == name.lower()
        ).first()
        
        if not category:
            category = Category(
                name=name.title(),
                is_system=True,
                is_active=True,
                level=0
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
        
        return category
    
    def initialize_default_categories(self) -> List[Category]:
        """Initialize default categories."""
        default_categories = [
            {
                "name": "Food & Dining",
                "description": "Restaurants, cafes, and dining out",
                "color": "#FF6B6B",
                "icon": "restaurant",
                "keywords": ["restaurant", "cafe", "pizza", "burger", "food", "dining", "kitchen", "diner", "grill", "bistro", "bar", "pub"]
            },
            {
                "name": "Groceries",
                "description": "Grocery stores and food shopping",
                "color": "#4ECDC4",
                "icon": "shopping_cart",
                "keywords": ["grocery", "supermarket", "market", "walmart", "target", "costco", "safeway", "kroger", "whole foods"]
            },
            {
                "name": "Transportation",
                "description": "Gas, public transport, rideshare",
                "color": "#45B7D1",
                "icon": "directions_car",
                "keywords": ["gas", "fuel", "uber", "lyft", "taxi", "bus", "train", "metro", "parking", "shell", "exxon", "bp"]
            },
            {
                "name": "Shopping",
                "description": "Retail purchases and online shopping",
                "color": "#96CEB4",
                "icon": "shopping_bag",
                "keywords": ["amazon", "ebay", "store", "shop", "retail", "mall", "clothing", "electronics"]
            },
            {
                "name": "Entertainment",
                "description": "Movies, games, streaming services",
                "color": "#FFEAA7",
                "icon": "movie",
                "keywords": ["netflix", "spotify", "movie", "cinema", "theater", "game", "entertainment", "music"]
            },
            {
                "name": "Utilities",
                "description": "Electric, water, internet, phone bills",
                "color": "#DDA0DD",
                "icon": "flash_on",
                "keywords": ["electric", "water", "gas", "internet", "phone", "cable", "utility", "bill"]
            },
            {
                "name": "Healthcare",
                "description": "Medical expenses and pharmacy",
                "color": "#FFB6C1",
                "icon": "local_hospital",
                "keywords": ["hospital", "clinic", "pharmacy", "doctor", "medical", "health", "dentist"]
            },
            {
                "name": "Income",
                "description": "Salary, freelance, and other income",
                "color": "#90EE90",
                "icon": "attach_money",
                "keywords": ["salary", "payroll", "freelance", "income", "payment", "deposit"],
                "is_income": True
            },
            {
                "name": "Fees & Charges",
                "description": "Bank fees, service charges",
                "color": "#F08080",
                "icon": "account_balance",
                "keywords": ["fee", "charge", "service", "bank", "atm", "overdraft"]
            },
            {
                "name": "Cash & ATM",
                "description": "Cash withdrawals and ATM transactions",
                "color": "#D3D3D3",
                "icon": "local_atm",
                "keywords": ["atm", "withdrawal", "cash", "money"]
            }
        ]
        
        created_categories = []
        for cat_data in default_categories:
            existing = self.db.query(Category).filter(
                func.lower(Category.name) == cat_data["name"].lower()
            ).first()
            
            if not existing:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    color=cat_data["color"],
                    icon=cat_data["icon"],
                    keywords=json.dumps(cat_data["keywords"]),
                    is_income=cat_data.get("is_income", False),
                    is_system=True,
                    is_active=True,
                    level=0
                )
                self.db.add(category)
                created_categories.append(category)
        
        if created_categories:
            self.db.commit()
            for category in created_categories:
                self.db.refresh(category)
        
        return created_categories
