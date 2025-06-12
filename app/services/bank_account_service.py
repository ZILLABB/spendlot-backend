"""
Bank account service for bank account management operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.schemas.bank_account import BankAccountCreate, BankAccountUpdate
from app.services.base_service import BaseService


class BankAccountService(BaseService[BankAccount, BankAccountCreate, BankAccountUpdate]):
    """Service for bank account management operations."""
    
    def __init__(self, db: Session):
        super().__init__(BankAccount, db)
    
    def get_by_user(self, user_id: int) -> List[BankAccount]:
        """Get all bank accounts for a user."""
        return self.db.query(BankAccount).filter(
            BankAccount.user_id == user_id,
            BankAccount.is_active == True
        ).order_by(BankAccount.is_primary.desc(), BankAccount.account_name).all()
    
    def get_by_plaid_item(self, plaid_item_id: int) -> List[BankAccount]:
        """Get all bank accounts for a Plaid item."""
        return self.db.query(BankAccount).filter(
            BankAccount.plaid_item_id == plaid_item_id
        ).all()
    
    def get_by_plaid_account_id(self, plaid_account_id: str) -> Optional[BankAccount]:
        """Get bank account by Plaid account ID."""
        return self.db.query(BankAccount).filter(
            BankAccount.plaid_account_id == plaid_account_id
        ).first()
    
    def set_primary(self, account_id: int, user_id: int) -> BankAccount:
        """Set an account as primary and unset others."""
        # Unset all other primary accounts for the user
        self.db.query(BankAccount).filter(
            BankAccount.user_id == user_id,
            BankAccount.id != account_id
        ).update({"is_primary": False})
        
        # Set the specified account as primary
        account = self.get(account_id)
        if account and account.user_id == user_id:
            account.is_primary = True
            self.db.commit()
            self.db.refresh(account)
        
        return account
    
    def deactivate(self, account_id: int) -> BankAccount:
        """Deactivate a bank account."""
        account = self.get(account_id)
        if account:
            account.is_active = False
            account.auto_sync = False
            account.sync_status = "disabled"
            self.db.commit()
            self.db.refresh(account)
        return account
    
    def activate(self, account_id: int) -> BankAccount:
        """Activate a bank account."""
        account = self.get(account_id)
        if account:
            account.is_active = True
            account.sync_status = "active"
            self.db.commit()
            self.db.refresh(account)
        return account
