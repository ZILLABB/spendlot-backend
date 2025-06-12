"""
Background tasks for automatic categorization.
"""
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.categorization_service import CategorizationService
from app.services.receipt_service import ReceiptService
from app.services.transaction_service import TransactionService

logger = get_logger(__name__)


@celery_app.task
def categorize_uncategorized_transactions():
    """Categorize all uncategorized transactions."""
    db = SessionLocal()
    try:
        categorization_service = CategorizationService(db)
        transaction_service = TransactionService(db)
        
        # Get uncategorized transactions
        uncategorized = db.query(transaction_service.model).filter(
            transaction_service.model.category_id.is_(None),
            transaction_service.model.auto_categorized == False
        ).limit(100).all()
        
        categorized_count = 0
        for transaction in uncategorized:
            category = categorization_service.auto_categorize_transaction(transaction)
            if category:
                transaction.category_id = category.id
                transaction.auto_categorized = True
                categorized_count += 1
        
        db.commit()
        
        logger.info(f"Auto-categorized {categorized_count} transactions")
        return {"categorized": categorized_count}
        
    except Exception as e:
        logger.error(f"Error categorizing transactions: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def categorize_uncategorized_receipts():
    """Categorize all uncategorized receipts."""
    db = SessionLocal()
    try:
        categorization_service = CategorizationService(db)
        receipt_service = ReceiptService(db)
        
        # Get uncategorized receipts
        uncategorized = db.query(receipt_service.model).filter(
            receipt_service.model.category_id.is_(None),
            receipt_service.model.auto_categorized == False,
            receipt_service.model.processing_status == "completed"
        ).limit(100).all()
        
        categorized_count = 0
        for receipt in uncategorized:
            category = categorization_service.auto_categorize_receipt(receipt)
            if category:
                receipt.category_id = category.id
                receipt.auto_categorized = True
                categorized_count += 1
        
        db.commit()
        
        logger.info(f"Auto-categorized {categorized_count} receipts")
        return {"categorized": categorized_count}
        
    except Exception as e:
        logger.error(f"Error categorizing receipts: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def initialize_default_categories():
    """Initialize default categories if they don't exist."""
    db = SessionLocal()
    try:
        categorization_service = CategorizationService(db)
        categories = categorization_service.initialize_default_categories()
        
        logger.info(f"Initialized {len(categories)} default categories")
        return {"created": len(categories)}
        
    except Exception as e:
        logger.error(f"Error initializing categories: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()
