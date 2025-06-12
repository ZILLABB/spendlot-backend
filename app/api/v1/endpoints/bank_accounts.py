"""
Bank account and Plaid integration endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bank_account import (
    BankAccount,
    BankAccountUpdate,
    PlaidLinkRequest,
    PlaidLinkResponse
)
from app.schemas.plaid_item import (
    PlaidLinkTokenResponse,
    PlaidPublicTokenExchangeRequest,
    PlaidWebhookRequest
)
from app.services.plaid_service import PlaidService
from app.services.bank_account_service import BankAccountService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[BankAccount])
async def get_bank_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's bank accounts.
    """
    bank_account_service = BankAccountService(db)
    accounts = bank_account_service.get_by_user(current_user.id)
    return accounts


@router.get("/{account_id}", response_model=BankAccount)
async def get_bank_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific bank account by ID.
    """
    bank_account_service = BankAccountService(db)
    account = bank_account_service.get(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this bank account"
        )
    
    return account


@router.put("/{account_id}", response_model=BankAccount)
async def update_bank_account(
    account_id: int,
    account_update: BankAccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a bank account.
    """
    bank_account_service = BankAccountService(db)
    account = bank_account_service.get(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this bank account"
        )
    
    updated_account = bank_account_service.update(
        db_obj=account,
        obj_in=account_update
    )
    return updated_account


@router.delete("/{account_id}")
async def delete_bank_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a bank account.
    """
    bank_account_service = BankAccountService(db)
    account = bank_account_service.get(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this bank account"
        )
    
    bank_account_service.deactivate(account_id)
    return {"message": "Bank account deactivated successfully"}


# Plaid integration endpoints
@router.post("/plaid/link-token", response_model=PlaidLinkTokenResponse)
async def create_plaid_link_token(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Plaid Link token for connecting bank accounts.
    """
    plaid_service = PlaidService(db)
    
    try:
        token_data = plaid_service.create_link_token(current_user.id)
        return PlaidLinkTokenResponse(**token_data)
    except Exception as e:
        logger.error(f"Error creating Plaid link token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create link token"
        )


@router.post("/plaid/exchange-token", response_model=PlaidLinkResponse)
async def exchange_plaid_public_token(
    exchange_request: PlaidPublicTokenExchangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Exchange Plaid public token for access token and create bank accounts.
    """
    plaid_service = PlaidService(db)
    
    try:
        plaid_item = plaid_service.exchange_public_token(
            user_id=current_user.id,
            public_token=exchange_request.public_token,
            institution_id=exchange_request.institution_id,
            institution_name=exchange_request.institution_name,
            account_ids=exchange_request.account_ids
        )
        
        # Get created bank accounts
        bank_account_service = BankAccountService(db)
        accounts = bank_account_service.get_by_plaid_item(plaid_item.id)
        
        return PlaidLinkResponse(
            item_id=plaid_item.id,
            accounts=[account.dict() for account in accounts],
            message="Bank accounts connected successfully"
        )
        
    except Exception as e:
        logger.error(f"Error exchanging Plaid public token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect bank accounts"
        )


@router.post("/{account_id}/sync")
async def sync_account_transactions(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually sync transactions for a specific bank account.
    """
    bank_account_service = BankAccountService(db)
    account = bank_account_service.get(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to sync this bank account"
        )
    
    if not account.plaid_item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not connected via Plaid"
        )
    
    try:
        plaid_service = PlaidService(db)
        new_transactions = plaid_service.sync_transactions(account.plaid_item_id)
        
        return {
            "message": f"Sync completed successfully",
            "new_transactions": new_transactions
        }
        
    except Exception as e:
        logger.error(f"Error syncing account {account_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync transactions"
        )


@router.post("/plaid/webhook")
async def handle_plaid_webhook(
    webhook_data: PlaidWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Handle Plaid webhooks for real-time updates.
    """
    logger.info(f"Received Plaid webhook: {webhook_data.webhook_type}.{webhook_data.webhook_code}")
    
    try:
        plaid_service = PlaidService(db)
        
        # Find Plaid item
        plaid_item = db.query(plaid_service.model).filter(
            plaid_service.model.plaid_item_id == webhook_data.item_id
        ).first()
        
        if not plaid_item:
            logger.warning(f"Plaid item not found: {webhook_data.item_id}")
            return {"status": "ignored", "reason": "item_not_found"}
        
        # Handle different webhook types
        if webhook_data.webhook_type == "TRANSACTIONS":
            if webhook_data.webhook_code == "INITIAL_UPDATE":
                # Initial transaction data available
                plaid_service.sync_transactions(plaid_item.id)
                
            elif webhook_data.webhook_code == "HISTORICAL_UPDATE":
                # Historical transaction data available
                plaid_service.sync_transactions(plaid_item.id)
                
            elif webhook_data.webhook_code == "DEFAULT_UPDATE":
                # New transaction data available
                plaid_service.sync_transactions(plaid_item.id)
                
        elif webhook_data.webhook_type == "ITEM":
            if webhook_data.webhook_code == "ERROR":
                # Item error occurred
                if webhook_data.error:
                    plaid_item.error_type = webhook_data.error.get("error_type")
                    plaid_item.error_code = webhook_data.error.get("error_code")
                    plaid_item.error_message = webhook_data.error.get("error_message")
                    plaid_item.status = "bad"
                    db.commit()
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing Plaid webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
