"""
Twilio SMS integration service.
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from twilio.rest import Client
from twilio.request_validator import RequestValidator

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TwilioService:
    """Service for Twilio SMS integration."""
    
    def __init__(self):
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        else:
            self.client = None
            self.validator = None
            logger.warning("Twilio credentials not configured")
    
    def validate_webhook(self, url: str, params: Dict[str, Any], signature: str) -> bool:
        """Validate Twilio webhook signature."""
        if not self.validator:
            logger.warning("Twilio validator not configured")
            return False
        
        return self.validator.validate(url, params, signature)
    
    def send_sms(self, to: str, message: str) -> bool:
        """Send SMS message."""
        if not self.client:
            logger.error("Twilio client not configured")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to
            )
            logger.info(f"SMS sent successfully: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False
    
    def parse_receipt_sms(self, sms_body: str, sender: str) -> Optional[Dict[str, Any]]:
        """Parse receipt information from SMS content."""
        if not sms_body:
            return None
        
        # Check if this looks like a receipt SMS
        receipt_keywords = ['receipt', 'purchase', 'transaction', 'payment', 'charged', 'paid']
        sms_lower = sms_body.lower()
        
        if not any(keyword in sms_lower for keyword in receipt_keywords):
            return None
        
        extracted = {}
        
        # Extract merchant name from common patterns
        merchant_patterns = [
            r'at\s+([A-Za-z\s]+?)(?:\s+on|\s+for|\s*\$)',
            r'from\s+([A-Za-z\s]+?)(?:\s+on|\s+for|\s*\$)',
            r'([A-Za-z\s]+?)\s+charged',
            r'([A-Za-z\s]+?)\s+transaction'
        ]
        
        for pattern in merchant_patterns:
            match = re.search(pattern, sms_body, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                if len(merchant) > 2 and not merchant.isdigit():
                    extracted['merchant_name'] = merchant
                    break
        
        # Extract amount
        amount_patterns = [
            r'\$(\d+\.?\d*)',
            r'amount[:\s]*\$?(\d+\.?\d*)',
            r'charged[:\s]*\$?(\d+\.?\d*)',
            r'paid[:\s]*\$?(\d+\.?\d*)',
            r'(\d+\.\d{2})'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, sms_body, re.IGNORECASE)
            if matches:
                try:
                    # Take the largest amount found (likely the total)
                    amounts = [Decimal(match) for match in matches]
                    extracted['amount'] = max(amounts)
                    break
                except:
                    continue
        
        # Extract date/time (default to now if not found)
        extracted['transaction_date'] = datetime.now()
        
        # Try to extract date from SMS
        date_patterns = [
            r'on\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, sms_body, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse the date
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y']:
                        try:
                            extracted['transaction_date'] = datetime.strptime(date_str, fmt)
                            break
                        except:
                            continue
                    break
                except:
                    continue
        
        # Extract card information if present
        card_patterns = [
            r'card\s+ending\s+in\s+(\d{4})',
            r'card\s+\*+(\d{4})',
            r'\*+(\d{4})'
        ]
        
        for pattern in card_patterns:
            match = re.search(pattern, sms_body, re.IGNORECASE)
            if match:
                extracted['card_last_four'] = match.group(1)
                break
        
        # Store original SMS data
        extracted['sms_body'] = sms_body
        extracted['sms_sender'] = sender
        
        return extracted if extracted else None
    
    def categorize_sms_merchant(self, merchant_name: str) -> Optional[str]:
        """Attempt to categorize based on merchant name."""
        if not merchant_name:
            return None
        
        merchant_lower = merchant_name.lower()
        
        # Common merchant patterns
        categories = {
            'food': ['restaurant', 'cafe', 'pizza', 'burger', 'food', 'kitchen', 'diner', 'grill', 'bistro', 'mcdonald', 'subway', 'starbucks'],
            'gas': ['gas', 'fuel', 'shell', 'exxon', 'bp', 'chevron', 'mobil', 'texaco'],
            'groceries': ['grocery', 'market', 'walmart', 'target', 'costco', 'safeway', 'kroger'],
            'shopping': ['store', 'shop', 'retail', 'amazon', 'ebay', 'mall'],
            'transport': ['uber', 'lyft', 'taxi', 'parking'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'cable'],
            'healthcare': ['pharmacy', 'cvs', 'walgreens', 'hospital', 'clinic']
        }
        
        for category, keywords in categories.items():
            if any(keyword in merchant_lower for keyword in keywords):
                return category
        
        return None
