"""
Background tasks for Plaid integration.
"""
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.plaid_service import PlaidService

logger = get_logger(__name__)


@celery_app.task
def sync_plaid_transactions(plaid_item_id: int):
    """Sync transactions for a specific Plaid item."""
    db = SessionLocal()
    try:
        plaid_service = PlaidService(db)
        new_transactions = plaid_service.sync_transactions(plaid_item_id)
        
        logger.info(f"Synced {new_transactions} new transactions for Plaid item {plaid_item_id}")
        return {"plaid_item_id": plaid_item_id, "new_transactions": new_transactions}
        
    except Exception as e:
        logger.error(f"Error syncing Plaid transactions for item {plaid_item_id}: {str(e)}")
        return {"error": str(e), "plaid_item_id": plaid_item_id}
    finally:
        db.close()


@celery_app.task
def sync_all_plaid_transactions():
    """Sync transactions for all active Plaid items."""
    db = SessionLocal()
    try:
        plaid_service = PlaidService(db)
        
        # Get all active Plaid items
        active_items = db.query(plaid_service.model).filter(
            plaid_service.model.is_active == True,
            plaid_service.model.status == "good"
        ).all()
        
        total_new_transactions = 0
        synced_items = 0
        
        for item in active_items:
            try:
                new_transactions = plaid_service.sync_transactions(item.id)
                total_new_transactions += new_transactions
                synced_items += 1
                
                logger.info(f"Synced {new_transactions} transactions for Plaid item {item.id}")
                
            except Exception as e:
                logger.error(f"Error syncing Plaid item {item.id}: {str(e)}")
                continue
        
        logger.info(f"Completed sync for {synced_items} Plaid items, {total_new_transactions} new transactions")
        return {
            "synced_items": synced_items,
            "total_items": len(active_items),
            "new_transactions": total_new_transactions
        }
        
    except Exception as e:
        logger.error(f"Error in sync_all_plaid_transactions: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def sync_plaid_accounts(plaid_item_id: int):
    """Sync bank accounts for a specific Plaid item."""
    db = SessionLocal()
    try:
        plaid_service = PlaidService(db)
        accounts = plaid_service.sync_accounts(plaid_item_id)
        
        logger.info(f"Synced {len(accounts)} accounts for Plaid item {plaid_item_id}")
        return {"plaid_item_id": plaid_item_id, "synced_accounts": len(accounts)}
        
    except Exception as e:
        logger.error(f"Error syncing Plaid accounts for item {plaid_item_id}: {str(e)}")
        return {"error": str(e), "plaid_item_id": plaid_item_id}
    finally:
        db.close()


@celery_app.task
def handle_plaid_webhook(webhook_type: str, webhook_code: str, item_id: str, **kwargs):
    """Handle Plaid webhook events."""
    db = SessionLocal()
    try:
        plaid_service = PlaidService(db)
        
        # Find Plaid item
        plaid_item = db.query(plaid_service.model).filter(
            plaid_service.model.plaid_item_id == item_id
        ).first()
        
        if not plaid_item:
            logger.warning(f"Plaid item not found: {item_id}")
            return {"status": "ignored", "reason": "item_not_found"}
        
        logger.info(f"Processing Plaid webhook: {webhook_type}.{webhook_code} for item {item_id}")
        
        # Handle different webhook types
        if webhook_type == "TRANSACTIONS":
            if webhook_code in ["INITIAL_UPDATE", "HISTORICAL_UPDATE", "DEFAULT_UPDATE"]:
                # Sync transactions
                new_transactions = plaid_service.sync_transactions(plaid_item.id)
                logger.info(f"Webhook sync completed: {new_transactions} new transactions")
                return {"status": "processed", "new_transactions": new_transactions}
                
        elif webhook_type == "ITEM":
            if webhook_code == "ERROR":
                # Handle item error
                error_info = kwargs.get("error", {})
                plaid_item.error_type = error_info.get("error_type")
                plaid_item.error_code = error_info.get("error_code")
                plaid_item.error_message = error_info.get("error_message")
                plaid_item.status = "bad"
                db.commit()
                
                logger.warning(f"Plaid item error: {plaid_item.error_message}")
                return {"status": "processed", "action": "error_recorded"}
                
            elif webhook_code == "PENDING_EXPIRATION":
                # Handle pending expiration
                plaid_item.status = "requires_update"
                db.commit()
                
                logger.info(f"Plaid item requires update: {item_id}")
                return {"status": "processed", "action": "marked_for_update"}
        
        return {"status": "ignored", "reason": "unhandled_webhook"}
        
    except Exception as e:
        logger.error(f"Error processing Plaid webhook: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
