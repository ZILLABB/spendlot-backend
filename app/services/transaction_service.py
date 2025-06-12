"""
Transaction service for transaction management operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.base_service import BaseService


class TransactionService(BaseService[Transaction, TransactionCreate, TransactionUpdate]):
    """Service for transaction management operations."""
    
    def __init__(self, db: Session):
        super().__init__(Transaction, db)
    
    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Transaction]:
        """Get transactions for a specific user."""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply filters
        if filters:
            if filters.get("account_id"):
                query = query.filter(Transaction.account_id == filters["account_id"])
            
            if filters.get("category_id"):
                query = query.filter(Transaction.category_id == filters["category_id"])
            
            if filters.get("merchant_name"):
                query = query.filter(
                    Transaction.merchant_name.ilike(f"%{filters['merchant_name']}%")
                )
            
            if filters.get("description"):
                query = query.filter(
                    Transaction.description.ilike(f"%{filters['description']}%")
                )
            
            if filters.get("transaction_type"):
                query = query.filter(Transaction.transaction_type == filters["transaction_type"])
            
            if filters.get("date_from"):
                query = query.filter(Transaction.transaction_date >= filters["date_from"])
            
            if filters.get("date_to"):
                query = query.filter(Transaction.transaction_date <= filters["date_to"])
            
            if filters.get("min_amount"):
                query = query.filter(Transaction.amount >= filters["min_amount"])
            
            if filters.get("max_amount"):
                query = query.filter(Transaction.amount <= filters["max_amount"])
            
            if filters.get("is_pending") is not None:
                query = query.filter(Transaction.is_pending == filters["is_pending"])
            
            if filters.get("has_receipt") is not None:
                query = query.filter(Transaction.has_receipt == filters["has_receipt"])
        
        return query.order_by(desc(Transaction.transaction_date)).offset(skip).limit(limit).all()
    
    def count_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count transactions for a specific user."""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply same filters as get_by_user
        if filters:
            if filters.get("account_id"):
                query = query.filter(Transaction.account_id == filters["account_id"])
            
            if filters.get("category_id"):
                query = query.filter(Transaction.category_id == filters["category_id"])
            
            if filters.get("merchant_name"):
                query = query.filter(
                    Transaction.merchant_name.ilike(f"%{filters['merchant_name']}%")
                )
            
            if filters.get("description"):
                query = query.filter(
                    Transaction.description.ilike(f"%{filters['description']}%")
                )
            
            if filters.get("transaction_type"):
                query = query.filter(Transaction.transaction_type == filters["transaction_type"])
            
            if filters.get("date_from"):
                query = query.filter(Transaction.transaction_date >= filters["date_from"])
            
            if filters.get("date_to"):
                query = query.filter(Transaction.transaction_date <= filters["date_to"])
            
            if filters.get("min_amount"):
                query = query.filter(Transaction.amount >= filters["min_amount"])
            
            if filters.get("max_amount"):
                query = query.filter(Transaction.amount <= filters["max_amount"])
            
            if filters.get("is_pending") is not None:
                query = query.filter(Transaction.is_pending == filters["is_pending"])
            
            if filters.get("has_receipt") is not None:
                query = query.filter(Transaction.has_receipt == filters["has_receipt"])
        
        return query.count()
    
    def get_spending_summary(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get spending summary for a date range."""
        query = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        
        transactions = query.all()
        
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
        net_amount = total_income - total_expenses
        
        return {
            "period": f"{start_date.date()} to {end_date.date()}",
            "start_date": start_date,
            "end_date": end_date,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": net_amount,
            "transaction_count": len(transactions),
            "avg_transaction_amount": (total_income + total_expenses) / len(transactions) if transactions else 0
        }
    
    def get_category_breakdown(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get spending breakdown by category."""
        from app.models.category import Category
        
        query = self.db.query(
            Category.name,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction, Transaction.category_id == Category.id
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.amount < 0  # Only expenses
            )
        ).group_by(Category.name).order_by(desc('total_amount'))
        
        results = query.all()
        
        total_spending = sum(r.total_amount for r in results)
        
        breakdown = []
        for result in results:
            percentage = (result.total_amount / total_spending * 100) if total_spending > 0 else 0
            breakdown.append({
                "category": result.name,
                "total_amount": float(result.total_amount),
                "transaction_count": result.transaction_count,
                "percentage": round(percentage, 2)
            })
        
        return breakdown
    
    def get_daily_spending(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily spending breakdown."""
        query = self.db.query(
            func.date(Transaction.transaction_date).label('date'),
            func.sum(func.abs(Transaction.amount)).label('total_spent'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.amount < 0  # Only expenses
            )
        ).group_by(func.date(Transaction.transaction_date)).order_by('date')
        
        results = query.all()
        
        daily_breakdown = []
        for result in results:
            daily_breakdown.append({
                "date": result.date.isoformat(),
                "total_spent": float(result.total_spent),
                "transaction_count": result.transaction_count
            })
        
        return daily_breakdown
    
    def create_from_plaid(
        self,
        user_id: int,
        plaid_transaction: Dict[str, Any],
        account_id: int,
        data_source_id: int
    ) -> Transaction:
        """Create transaction from Plaid transaction data."""
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            data_source_id=data_source_id,
            plaid_transaction_id=plaid_transaction["transaction_id"],
            amount=Decimal(str(-plaid_transaction["amount"])),  # Plaid uses positive for expenses
            currency=plaid_transaction.get("iso_currency_code", "USD"),
            description=plaid_transaction["name"],
            transaction_date=datetime.strptime(plaid_transaction["date"], "%Y-%m-%d"),
            transaction_type="debit" if plaid_transaction["amount"] > 0 else "credit",
            merchant_name=plaid_transaction.get("merchant_name"),
            is_pending=plaid_transaction.get("pending", False),
            processing_status="completed"
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_by_plaid_id(self, plaid_transaction_id: str) -> Optional[Transaction]:
        """Get transaction by Plaid transaction ID."""
        return self.db.query(Transaction).filter(
            Transaction.plaid_transaction_id == plaid_transaction_id
        ).first()
