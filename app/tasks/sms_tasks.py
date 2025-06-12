"""
Background tasks for SMS processing.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.receipt_service import ReceiptService
from app.services.data_source_service import DataSourceService
from app.services.user_service import UserService
from app.services.categorization_service import CategorizationService

logger = get_logger(__name__)


@celery_app.task
def process_sms_receipt(
    sms_body: str,
    sender: str,
    message_sid: str,
    receipt_data: Dict[str, Any]
):
    """Process SMS receipt and create receipt record."""
    db = SessionLocal()
    try:
        logger.info(f"Processing SMS receipt from {sender}, message: {message_sid}")
        
        # Find user by phone number
        user = find_user_by_phone(db, sender)
        if not user:
            logger.warning(f"No user found for phone number {sender}")
            return {"error": "User not found", "sender": sender}
        
        # Get SMS data source
        data_source_service = DataSourceService(db)
        sms_source = data_source_service.get_by_name("sms_receipts")
        if not sms_source:
            sms_source = data_source_service.create_sms_source()
        
        # Create receipt record
        receipt_service = ReceiptService(db)
        receipt = receipt_service.model(
            user_id=user.id,
            data_source_id=sms_source.id,
            external_id=message_sid,
            merchant_name=receipt_data.get('merchant_name'),
            amount=receipt_data.get('amount'),
            transaction_date=receipt_data.get('transaction_date'),
            processing_status="completed",
            extra_metadata={
                "sms_body": sms_body,
                "sms_sender": sender,
                "card_last_four": receipt_data.get('card_last_four')
            },
            notes=f"Received via SMS from {sender}"
        )
        
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        # Auto-categorize if possible
        if receipt_data.get('merchant_name'):
            categorization_service = CategorizationService(db)
            category = categorization_service.auto_categorize_receipt(receipt)
            if category:
                receipt.category_id = category.id
                receipt.auto_categorized = True
                db.commit()
        
        logger.info(f"Created receipt {receipt.id} from SMS {message_sid}")
        return {
            "receipt_id": receipt.id,
            "user_id": user.id,
            "merchant": receipt_data.get('merchant_name'),
            "amount": str(receipt_data.get('amount', 0))
        }
        
    except Exception as e:
        logger.error(f"Error processing SMS receipt {message_sid}: {str(e)}")
        return {"error": str(e), "message_sid": message_sid}
    finally:
        db.close()


def find_user_by_phone(db: Session, phone_number: str) -> Optional[Any]:
    """Find user by phone number."""
    from app.models.user import User
    
    # Clean phone number (remove +1, spaces, dashes, etc.)
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    if clean_phone.startswith('1') and len(clean_phone) == 11:
        clean_phone = clean_phone[1:]  # Remove country code
    
    # Try exact match first
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user:
        return user
    
    # Try with cleaned phone number
    users = db.query(User).filter(User.phone_number.isnot(None)).all()
    for user in users:
        if user.phone_number:
            user_clean = ''.join(filter(str.isdigit, user.phone_number))
            if user_clean.startswith('1') and len(user_clean) == 11:
                user_clean = user_clean[1:]
            
            if user_clean == clean_phone:
                return user
    
    return None


@celery_app.task
def send_sms_notification(user_id: int, message: str):
    """Send SMS notification to user."""
    db = SessionLocal()
    try:
        from app.services.twilio_service import TwilioService
        
        user_service = UserService(db)
        user = user_service.get(user_id)
        
        if not user or not user.phone_number:
            logger.warning(f"Cannot send SMS to user {user_id}: no phone number")
            return {"error": "No phone number"}
        
        twilio_service = TwilioService()
        success = twilio_service.send_sms(user.phone_number, message)
        
        if success:
            logger.info(f"SMS notification sent to user {user_id}")
            return {"status": "sent", "user_id": user_id}
        else:
            logger.error(f"Failed to send SMS to user {user_id}")
            return {"error": "Send failed", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Error sending SMS notification to user {user_id}: {str(e)}")
        return {"error": str(e), "user_id": user_id}
    finally:
        db.close()


@celery_app.task
def process_pending_sms_receipts():
    """Process any pending SMS receipts that failed initial processing."""
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        
        # Get SMS receipts that are pending
        pending_sms_receipts = db.query(receipt_service.model).filter(
            receipt_service.model.processing_status == "pending"
        ).join(
            receipt_service.model.data_source
        ).filter(
            receipt_service.model.data_source.has(source_type="sms")
        ).limit(10).all()
        
        processed = 0
        for receipt in pending_sms_receipts:
            try:
                # Re-attempt processing
                if receipt.extra_metadata and 'sms_body' in receipt.extra_metadata:
                    from app.services.twilio_service import TwilioService
                    twilio_service = TwilioService()
                    
                    receipt_data = twilio_service.parse_receipt_sms(
                        receipt.extra_metadata['sms_body'],
                        receipt.extra_metadata.get('sms_sender', '')
                    )
                    
                    if receipt_data:
                        # Update receipt with parsed data
                        if not receipt.merchant_name and receipt_data.get('merchant_name'):
                            receipt.merchant_name = receipt_data['merchant_name']
                        if not receipt.amount and receipt_data.get('amount'):
                            receipt.amount = receipt_data['amount']
                        
                        receipt.processing_status = "completed"
                        processed += 1
                
            except Exception as e:
                logger.error(f"Error reprocessing SMS receipt {receipt.id}: {str(e)}")
                receipt.processing_status = "failed"
                receipt.processing_error = str(e)
        
        db.commit()
        
        logger.info(f"Reprocessed {processed} pending SMS receipts")
        return {"processed": processed}
        
    except Exception as e:
        logger.error(f"Error processing pending SMS receipts: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()
