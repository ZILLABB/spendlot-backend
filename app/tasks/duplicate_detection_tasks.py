"""
Background tasks for duplicate detection.
"""
from datetime import timedelta
from sqlalchemy import and_
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.receipt_service import ReceiptService
from app.services.transaction_service import TransactionService

logger = get_logger(__name__)


@celery_app.task
def detect_receipt_duplicates():
    """Detect duplicate receipts."""
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        
        # Get receipts that haven't been checked for duplicates
        receipts = db.query(receipt_service.model).filter(
            receipt_service.model.is_duplicate == False,
            receipt_service.model.processing_status == "completed",
            receipt_service.model.merchant_name.isnot(None),
            receipt_service.model.amount.isnot(None),
            receipt_service.model.transaction_date.isnot(None)
        ).limit(100).all()
        
        duplicates_found = 0
        for receipt in receipts:
            duplicates = receipt_service.find_duplicates(receipt)
            
            if duplicates:
                # Mark as duplicate of the first (oldest) duplicate
                oldest_duplicate = min(duplicates, key=lambda x: x.created_at)
                receipt_service.mark_as_duplicate(receipt.id, oldest_duplicate.id)
                duplicates_found += 1
        
        logger.info(f"Found {duplicates_found} duplicate receipts")
        return {"duplicates_found": duplicates_found}
        
    except Exception as e:
        logger.error(f"Error detecting receipt duplicates: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def detect_transaction_duplicates():
    """Detect duplicate transactions."""
    db = SessionLocal()
    try:
        transaction_service = TransactionService(db)
        
        # Get transactions that haven't been checked for duplicates
        transactions = db.query(transaction_service.model).filter(
            transaction_service.model.is_duplicate == False,
            transaction_service.model.amount.isnot(None),
            transaction_service.model.transaction_date.isnot(None)
        ).limit(100).all()
        
        duplicates_found = 0
        for transaction in transactions:
            # Look for potential duplicates
            date_range_start = transaction.transaction_date - timedelta(days=1)
            date_range_end = transaction.transaction_date + timedelta(days=1)
            
            duplicates = db.query(transaction_service.model).filter(
                and_(
                    transaction_service.model.user_id == transaction.user_id,
                    transaction_service.model.id != transaction.id,
                    transaction_service.model.amount == transaction.amount,
                    transaction_service.model.transaction_date >= date_range_start,
                    transaction_service.model.transaction_date <= date_range_end,
                    transaction_service.model.is_duplicate == False
                )
            ).all()
            
            if duplicates:
                # Mark as duplicate of the first (oldest) duplicate
                oldest_duplicate = min(duplicates, key=lambda x: x.created_at)
                transaction.is_duplicate = True
                transaction.duplicate_of_id = oldest_duplicate.id
                duplicates_found += 1
        
        db.commit()
        
        logger.info(f"Found {duplicates_found} duplicate transactions")
        return {"duplicates_found": duplicates_found}
        
    except Exception as e:
        logger.error(f"Error detecting transaction duplicates: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def detect_all_duplicates():
    """Detect duplicates for both receipts and transactions."""
    receipt_result = detect_receipt_duplicates.delay()
    transaction_result = detect_transaction_duplicates.delay()
    
    return {
        "receipt_task_id": receipt_result.id,
        "transaction_task_id": transaction_result.id
    }
