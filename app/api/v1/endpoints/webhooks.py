"""
Webhook endpoints for external service integrations.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.services.twilio_service import TwilioService
from app.services.receipt_service import ReceiptService
from app.services.data_source_service import DataSourceService
from app.tasks.sms_tasks import process_sms_receipt

logger = get_logger(__name__)
router = APIRouter()


@router.post("/twilio/sms")
async def handle_twilio_sms_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle incoming SMS webhooks from Twilio.
    """
    try:
        # Get the full URL and signature for validation
        url = str(request.url)
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Get form data for validation
        form_data = await request.form()
        params = dict(form_data)
        
        # Validate webhook signature
        twilio_service = TwilioService()
        if not twilio_service.validate_webhook(url, params, signature):
            logger.warning(f"Invalid Twilio webhook signature from {From}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        logger.info(f"Received SMS from {From}: {Body[:100]}...")
        
        # Parse SMS for receipt information
        receipt_data = twilio_service.parse_receipt_sms(Body, From)
        
        if receipt_data:
            # Get SMS data source
            data_source_service = DataSourceService(db)
            sms_source = data_source_service.get_by_name("sms_receipts")
            if not sms_source:
                sms_source = data_source_service.create_sms_source()
            
            # Find user by phone number (simplified - in production you'd have a proper mapping)
            # For now, we'll queue the SMS for processing and let the background task handle user lookup
            
            # Queue SMS processing
            process_sms_receipt.delay(
                sms_body=Body,
                sender=From,
                message_sid=MessageSid,
                receipt_data=receipt_data
            )
            
            logger.info(f"Queued SMS receipt processing for message {MessageSid}")
        else:
            logger.info(f"SMS from {From} does not appear to be a receipt")
        
        # Return TwiML response (empty response is fine for SMS)
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error processing Twilio SMS webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process SMS webhook"
        )


@router.post("/twilio/status")
async def handle_twilio_status_webhook(
    request: Request,
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    To: str = Form(None),
    From: str = Form(None),
    ErrorCode: str = Form(None),
    ErrorMessage: str = Form(None)
):
    """
    Handle SMS delivery status webhooks from Twilio.
    """
    try:
        logger.info(f"SMS status update: {MessageSid} -> {MessageStatus}")
        
        if ErrorCode:
            logger.error(f"SMS delivery error {ErrorCode}: {ErrorMessage}")
        
        # You could store delivery status in database here
        # For now, just log it
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error processing Twilio status webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process status webhook"
        )


@router.post("/plaid/webhook")
async def handle_plaid_webhook(
    webhook_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Handle Plaid webhooks for real-time updates.
    This endpoint was already implemented in bank_accounts.py but moved here for organization.
    """
    from app.tasks.plaid_tasks import handle_plaid_webhook
    
    logger.info(f"Received Plaid webhook: {webhook_data.get('webhook_type')}.{webhook_data.get('webhook_code')}")
    
    try:
        # Queue webhook processing
        handle_plaid_webhook.delay(
            webhook_type=webhook_data.get('webhook_type'),
            webhook_code=webhook_data.get('webhook_code'),
            item_id=webhook_data.get('item_id'),
            **webhook_data
        )
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing Plaid webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/test/sms-parse")
async def test_sms_parsing(sms_body: str):
    """
    Test endpoint for SMS parsing (development only).
    """
    twilio_service = TwilioService()
    result = twilio_service.parse_receipt_sms(sms_body, "test_sender")
    return {"parsed_data": result}
