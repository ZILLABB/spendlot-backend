"""
Background tasks for Gmail integration.
"""
import base64
import email
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.security import decrypt_sensitive_data
from app.services.receipt_service import ReceiptService
from app.services.data_source_service import DataSourceService
from app.services.user_service import UserService

logger = get_logger(__name__)


@celery_app.task
def poll_gmail_receipts():
    """Poll Gmail for receipt emails for all users with Gmail integration."""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        
        # Get users with Gmail tokens
        users_with_gmail = db.query(user_service.model).filter(
            user_service.model.gmail_token.isnot(None),
            user_service.model.is_active == True
        ).all()
        
        total_receipts = 0
        processed_users = 0
        
        for user in users_with_gmail:
            try:
                receipts_found = process_user_gmail_receipts(user.id)
                total_receipts += receipts_found
                processed_users += 1
                
                logger.info(f"Processed Gmail for user {user.id}: {receipts_found} receipts found")
                
            except Exception as e:
                logger.error(f"Error processing Gmail for user {user.id}: {str(e)}")
                continue
        
        logger.info(f"Gmail polling completed: {processed_users} users, {total_receipts} receipts")
        return {
            "processed_users": processed_users,
            "total_users": len(users_with_gmail),
            "total_receipts": total_receipts
        }
        
    except Exception as e:
        logger.error(f"Error in poll_gmail_receipts: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def process_user_gmail_receipts(user_id: int):
    """Process Gmail receipts for a specific user."""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user = user_service.get(user_id)
        
        if not user or not user.gmail_token:
            logger.warning(f"User {user_id} not found or no Gmail token")
            return 0
        
        # Build Gmail service
        gmail_service = build_gmail_service(user.gmail_token)
        if not gmail_service:
            logger.error(f"Failed to build Gmail service for user {user_id}")
            return 0
        
        # Search for receipt emails
        receipt_emails = search_receipt_emails(gmail_service)
        
        # Get Gmail data source
        data_source_service = DataSourceService(db)
        gmail_source = data_source_service.get_by_name("gmail_receipts")
        if not gmail_source:
            gmail_source = data_source_service.create_gmail_source()
        
        receipt_service = ReceiptService(db)
        new_receipts = 0
        
        for email_data in receipt_emails:
            try:
                # Check if we already processed this email
                existing = db.query(receipt_service.model).filter(
                    receipt_service.model.user_id == user_id,
                    receipt_service.model.external_id == email_data["id"],
                    receipt_service.model.data_source_id == gmail_source.id
                ).first()
                
                if existing:
                    continue
                
                # Extract receipt data from email
                receipt_data = extract_receipt_from_email(email_data)
                
                if receipt_data:
                    # Create receipt record
                    receipt = receipt_service.model(
                        user_id=user_id,
                        data_source_id=gmail_source.id,
                        external_id=email_data["id"],
                        merchant_name=receipt_data.get("merchant_name"),
                        amount=receipt_data.get("amount"),
                        transaction_date=receipt_data.get("transaction_date"),
                        processing_status="completed",
                        metadata={"email_subject": email_data.get("subject", "")}
                    )
                    
                    db.add(receipt)
                    new_receipts += 1
            
            except Exception as e:
                logger.error(f"Error processing email {email_data.get('id')}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"Processed {new_receipts} new receipts from Gmail for user {user_id}")
        return new_receipts
        
    except Exception as e:
        logger.error(f"Error processing Gmail receipts for user {user_id}: {str(e)}")
        return 0
    finally:
        db.close()


def build_gmail_service(encrypted_token: str):
    """Build Gmail service from encrypted token."""
    try:
        # Decrypt token
        token_data = decrypt_sensitive_data(encrypted_token)
        
        # Create credentials
        creds = Credentials.from_authorized_user_info(eval(token_data))
        
        # Refresh if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        return service
        
    except Exception as e:
        logger.error(f"Error building Gmail service: {str(e)}")
        return None


def search_receipt_emails(gmail_service, max_results: int = 50) -> List[Dict[str, Any]]:
    """Search for receipt emails in Gmail."""
    try:
        # Search query for receipts
        query = 'subject:(receipt OR invoice OR purchase OR order) OR from:(noreply OR no-reply)'
        
        # Get recent emails (last 7 days)
        since_date = (datetime.now() - timedelta(days=7)).strftime('%Y/%m/%d')
        query += f' after:{since_date}'
        
        # Search emails
        results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        email_data = []
        for message in messages:
            try:
                # Get email details
                msg = gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract email data
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Get email body
                body = extract_email_body(msg['payload'])
                
                email_data.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date_str,
                    'body': body
                })
                
            except Exception as e:
                logger.error(f"Error processing email {message['id']}: {str(e)}")
                continue
        
        return email_data
        
    except Exception as e:
        logger.error(f"Error searching Gmail: {str(e)}")
        return []


def extract_email_body(payload: Dict[str, Any]) -> str:
    """Extract text body from email payload."""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        if payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    
    return body


def extract_receipt_from_email(email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract receipt information from email content."""
    subject = email_data.get('subject', '').lower()
    body = email_data.get('body', '').lower()
    sender = email_data.get('sender', '').lower()
    
    # Check if this looks like a receipt email
    receipt_keywords = ['receipt', 'invoice', 'purchase', 'order', 'payment', 'transaction']
    if not any(keyword in subject or keyword in body for keyword in receipt_keywords):
        return None
    
    extracted = {}
    
    # Extract merchant name from sender or subject
    if 'amazon' in sender:
        extracted['merchant_name'] = 'Amazon'
    elif 'uber' in sender:
        extracted['merchant_name'] = 'Uber'
    elif 'lyft' in sender:
        extracted['merchant_name'] = 'Lyft'
    elif 'paypal' in sender:
        extracted['merchant_name'] = 'PayPal'
    else:
        # Try to extract from sender domain
        domain_match = re.search(r'@([^.]+)', sender)
        if domain_match:
            extracted['merchant_name'] = domain_match.group(1).title()
    
    # Extract amount
    amount_patterns = [
        r'\$(\d+\.?\d*)',
        r'total[:\s]*\$?(\d+\.?\d*)',
        r'amount[:\s]*\$?(\d+\.?\d*)',
        r'(\d+\.\d{2})'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, body)
        if matches:
            try:
                extracted['amount'] = float(matches[-1])  # Take the last match
                break
            except:
                continue
    
    # Extract date
    date_str = email_data.get('date', '')
    if date_str:
        try:
            # Parse email date
            from email.utils import parsedate_to_datetime
            extracted['transaction_date'] = parsedate_to_datetime(date_str)
        except:
            extracted['transaction_date'] = datetime.now()
    
    return extracted if extracted else None
