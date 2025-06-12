"""
Plaid integration service for bank account and transaction sync.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from app.core.config import settings
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.models.plaid_item import PlaidItem
from app.models.bank_account import BankAccount
from app.schemas.plaid_item import PlaidItemCreate, PlaidItemUpdate
from app.services.base_service import BaseService
from app.services.transaction_service import TransactionService
from app.services.data_source_service import DataSourceService
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlaidService(BaseService[PlaidItem, PlaidItemCreate, PlaidItemUpdate]):
    """Service for Plaid integration operations."""
    
    def __init__(self, db: Session):
        super().__init__(PlaidItem, db)
        
        # Configure Plaid client
        configuration = Configuration(
            host=getattr(plaid_api.Environment, settings.PLAID_ENVIRONMENT, plaid_api.Environment.sandbox),
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_SECRET
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def create_link_token(self, user_id: int) -> Dict[str, Any]:
        """Create a link token for Plaid Link."""
        try:
            request = LinkTokenCreateRequest(
                products=[getattr(Products, product) for product in settings.PLAID_PRODUCTS.split(',')],
                client_name="Spendlot Receipt Tracker",
                country_codes=[getattr(CountryCode, code) for code in settings.PLAID_COUNTRY_CODES.split(',')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=str(user_id))
            )
            
            response = self.client.link_token_create(request)
            return {
                "link_token": response['link_token'],
                "expiration": response['expiration']
            }
            
        except Exception as e:
            logger.error(f"Error creating Plaid link token: {str(e)}")
            raise Exception(f"Failed to create link token: {str(e)}")
    
    def exchange_public_token(
        self,
        user_id: int,
        public_token: str,
        institution_id: str,
        institution_name: str,
        account_ids: List[str]
    ) -> PlaidItem:
        """Exchange public token for access token and create Plaid item."""
        try:
            # Exchange public token for access token
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            access_token = response['access_token']
            item_id = response['item_id']
            
            # Create Plaid item record
            plaid_item = PlaidItem(
                user_id=user_id,
                plaid_item_id=item_id,
                plaid_access_token=encrypt_sensitive_data(access_token),
                plaid_public_token=encrypt_sensitive_data(public_token),
                institution_id=institution_id,
                institution_name=institution_name,
                is_active=True,
                status="good"
            )
            
            self.db.add(plaid_item)
            self.db.commit()
            self.db.refresh(plaid_item)
            
            # Create bank accounts
            self.sync_accounts(plaid_item.id, account_ids)
            
            return plaid_item
            
        except Exception as e:
            logger.error(f"Error exchanging public token: {str(e)}")
            raise Exception(f"Failed to exchange public token: {str(e)}")
    
    def sync_accounts(self, plaid_item_id: int, selected_account_ids: Optional[List[str]] = None) -> List[BankAccount]:
        """Sync bank accounts from Plaid."""
        plaid_item = self.get(plaid_item_id)
        if not plaid_item:
            raise Exception("Plaid item not found")
        
        try:
            access_token = decrypt_sensitive_data(plaid_item.plaid_access_token)
            
            # Get accounts from Plaid
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            accounts = []
            for account in response['accounts']:
                # Skip if specific accounts were selected and this isn't one of them
                if selected_account_ids and account['account_id'] not in selected_account_ids:
                    continue
                
                # Check if account already exists
                existing_account = self.db.query(BankAccount).filter(
                    BankAccount.plaid_account_id == account['account_id']
                ).first()
                
                if existing_account:
                    # Update existing account
                    existing_account.account_name = account['name']
                    existing_account.account_type = account['type']
                    existing_account.account_subtype = account.get('subtype')
                    existing_account.current_balance = account['balances']['current']
                    existing_account.available_balance = account['balances'].get('available')
                    existing_account.last_balance_update = datetime.utcnow()
                    accounts.append(existing_account)
                else:
                    # Create new account
                    bank_account = BankAccount(
                        user_id=plaid_item.user_id,
                        plaid_item_id=plaid_item.id,
                        plaid_account_id=account['account_id'],
                        account_name=account['name'],
                        account_type=account['type'],
                        account_subtype=account.get('subtype'),
                        institution_name=plaid_item.institution_name,
                        institution_id=plaid_item.institution_id,
                        current_balance=account['balances']['current'],
                        available_balance=account['balances'].get('available'),
                        currency=account['balances'].get('iso_currency_code', 'USD'),
                        is_active=True,
                        auto_sync=True,
                        sync_status="active",
                        last_balance_update=datetime.utcnow()
                    )
                    self.db.add(bank_account)
                    accounts.append(bank_account)
            
            self.db.commit()
            
            # Refresh all accounts
            for account in accounts:
                self.db.refresh(account)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error syncing accounts for Plaid item {plaid_item_id}: {str(e)}")
            raise Exception(f"Failed to sync accounts: {str(e)}")
    
    def sync_transactions(
        self,
        plaid_item_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Sync transactions from Plaid."""
        plaid_item = self.get(plaid_item_id)
        if not plaid_item:
            raise Exception("Plaid item not found")
        
        try:
            access_token = decrypt_sensitive_data(plaid_item.plaid_access_token)
            
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Get transactions from Plaid
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            response = self.client.transactions_get(request)
            
            # Get data source for Plaid transactions
            data_source_service = DataSourceService(self.db)
            plaid_source = data_source_service.get_by_name("plaid_transactions")
            if not plaid_source:
                plaid_source = data_source_service.create_plaid_source()
            
            transaction_service = TransactionService(self.db)
            new_transactions = 0
            
            for transaction in response['transactions']:
                # Check if transaction already exists
                existing = transaction_service.get_by_plaid_id(transaction['transaction_id'])
                if existing:
                    continue
                
                # Find corresponding bank account
                bank_account = self.db.query(BankAccount).filter(
                    BankAccount.plaid_account_id == transaction['account_id']
                ).first()
                
                if not bank_account:
                    logger.warning(f"Bank account not found for Plaid account {transaction['account_id']}")
                    continue
                
                # Create transaction
                transaction_service.create_from_plaid(
                    user_id=plaid_item.user_id,
                    plaid_transaction=transaction,
                    account_id=bank_account.id,
                    data_source_id=plaid_source.id
                )
                new_transactions += 1
            
            # Update last sync time
            plaid_item.last_successful_update = datetime.utcnow()
            self.db.commit()
            
            return new_transactions
            
        except Exception as e:
            logger.error(f"Error syncing transactions for Plaid item {plaid_item_id}: {str(e)}")
            plaid_item.last_failed_update = datetime.utcnow()
            plaid_item.error_message = str(e)
            self.db.commit()
            raise Exception(f"Failed to sync transactions: {str(e)}")
    
    def get_by_user(self, user_id: int) -> List[PlaidItem]:
        """Get all Plaid items for a user."""
        return self.db.query(PlaidItem).filter(PlaidItem.user_id == user_id).all()
    
    def deactivate_item(self, plaid_item_id: int) -> PlaidItem:
        """Deactivate a Plaid item."""
        plaid_item = self.get(plaid_item_id)
        if plaid_item:
            plaid_item.is_active = False
            plaid_item.status = "disabled"
            
            # Deactivate associated bank accounts
            accounts = self.db.query(BankAccount).filter(
                BankAccount.plaid_item_id == plaid_item_id
            ).all()
            
            for account in accounts:
                account.is_active = False
                account.auto_sync = False
                account.sync_status = "disabled"
            
            self.db.commit()
            self.db.refresh(plaid_item)
        
        return plaid_item
