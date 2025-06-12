"""
Webhook security utilities for signature verification.
"""
import hmac
import hashlib
import time
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookVerifier:
    """Base class for webhook signature verification."""
    
    def __init__(self, secret: str):
        self.secret = secret.encode('utf-8')
    
    def verify_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """Verify webhook signature."""
        raise NotImplementedError


class PlaidWebhookVerifier(WebhookVerifier):
    """Plaid webhook signature verifier."""
    
    def verify_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """Verify Plaid webhook signature."""
        try:
            # Plaid uses HMAC-SHA256
            expected_signature = hmac.new(
                self.secret,
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Plaid webhook signature: {str(e)}")
            return False


class TwilioWebhookVerifier(WebhookVerifier):
    """Twilio webhook signature verifier."""
    
    def verify_signature(
        self, 
        url: str, 
        params: Dict[str, Any], 
        signature: str
    ) -> bool:
        """Verify Twilio webhook signature."""
        try:
            # Twilio signature verification
            # Create the string to sign
            data_string = url
            
            # Sort parameters and append to URL
            sorted_params = sorted(params.items())
            for key, value in sorted_params:
                data_string += f"{key}{value}"
            
            # Create HMAC-SHA1 signature
            expected_signature = hmac.new(
                self.secret,
                data_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Base64 encode
            import base64
            expected_signature_b64 = base64.b64encode(expected_signature).decode()
            
            return hmac.compare_digest(expected_signature_b64, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Twilio webhook signature: {str(e)}")
            return False


class GitHubWebhookVerifier(WebhookVerifier):
    """GitHub webhook signature verifier (for future use)."""
    
    def verify_signature(self, payload: bytes, signature: str, timestamp: Optional[str] = None) -> bool:
        """Verify GitHub webhook signature."""
        try:
            # GitHub uses HMAC-SHA256 with 'sha256=' prefix
            expected_signature = 'sha256=' + hmac.new(
                self.secret,
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying GitHub webhook signature: {str(e)}")
            return False


class StripeWebhookVerifier(WebhookVerifier):
    """Stripe webhook signature verifier (for future payment integration)."""
    
    def verify_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Verify Stripe webhook signature with timestamp validation."""
        try:
            # Extract timestamp and signatures from header
            elements = signature.split(',')
            timestamp_element = None
            signatures = []
            
            for element in elements:
                if element.startswith('t='):
                    timestamp_element = element[2:]
                elif element.startswith('v1='):
                    signatures.append(element[3:])
            
            if not timestamp_element or not signatures:
                return False
            
            # Check timestamp (prevent replay attacks)
            current_time = int(time.time())
            webhook_time = int(timestamp_element)
            
            # Allow 5 minutes tolerance
            if abs(current_time - webhook_time) > 300:
                logger.warning("Webhook timestamp too old")
                return False
            
            # Create expected signature
            signed_payload = f"{timestamp_element}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                self.secret,
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare with any of the provided signatures
            return any(
                hmac.compare_digest(expected_signature, sig)
                for sig in signatures
            )
            
        except Exception as e:
            logger.error(f"Error verifying Stripe webhook signature: {str(e)}")
            return False


def get_webhook_verifier(service: str, secret: str) -> WebhookVerifier:
    """Get appropriate webhook verifier for service."""
    verifiers = {
        'plaid': PlaidWebhookVerifier,
        'twilio': TwilioWebhookVerifier,
        'github': GitHubWebhookVerifier,
        'stripe': StripeWebhookVerifier
    }
    
    verifier_class = verifiers.get(service.lower())
    if not verifier_class:
        raise ValueError(f"Unknown webhook service: {service}")
    
    return verifier_class(secret)


def verify_webhook_timestamp(timestamp: str, tolerance: int = 300) -> bool:
    """Verify webhook timestamp is within tolerance."""
    try:
        webhook_time = int(timestamp)
        current_time = int(time.time())
        
        return abs(current_time - webhook_time) <= tolerance
        
    except (ValueError, TypeError):
        return False


class WebhookRateLimiter:
    """Rate limiter for webhook endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit."""
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Clean old entries
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True


# Global rate limiter instance
webhook_rate_limiter = WebhookRateLimiter()
