"""
Gmail OAuth and email processing service.
"""
import json
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.core.logging import get_logger

logger = get_logger(__name__)


class GmailService:
    """Service for Gmail OAuth and email processing."""
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GMAIL_REDIRECT_URI]
            }
        }
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
    
    def get_authorization_url(self, user_id: int) -> str:
        """Get Gmail OAuth authorization URL."""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GMAIL_REDIRECT_URI
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=str(user_id)  # Pass user ID in state
            )
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error creating Gmail authorization URL: {str(e)}")
            raise Exception(f"Failed to create authorization URL: {str(e)}")
    
    def exchange_code_for_tokens(self, authorization_code: str, user_id: int) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=settings.GMAIL_REDIRECT_URI
            )
            
            # Exchange code for tokens
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Get user info
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Prepare token data
            token_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            return {
                'token_data': token_data,
                'user_info': user_info
            }
            
        except Exception as e:
            logger.error(f"Error exchanging Gmail authorization code: {str(e)}")
            raise Exception(f"Failed to exchange authorization code: {str(e)}")
    
    def refresh_access_token(self, encrypted_token_data: str) -> Optional[str]:
        """Refresh Gmail access token."""
        try:
            # Decrypt token data
            token_data = json.loads(decrypt_sensitive_data(encrypted_token_data))
            
            # Create credentials
            credentials = Credentials.from_authorized_user_info(token_data)
            
            # Refresh if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update token data
                token_data.update({
                    'token': credentials.token,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None
                })
                
                # Return encrypted updated token data
                return encrypt_sensitive_data(json.dumps(token_data))
            
            return encrypted_token_data
            
        except Exception as e:
            logger.error(f"Error refreshing Gmail token: {str(e)}")
            return None
    
    def build_gmail_service(self, encrypted_token_data: str):
        """Build Gmail service from encrypted token data."""
        try:
            # Decrypt and refresh token if needed
            refreshed_token = self.refresh_access_token(encrypted_token_data)
            if not refreshed_token:
                return None
            
            token_data = json.loads(decrypt_sensitive_data(refreshed_token))
            
            # Create credentials
            credentials = Credentials.from_authorized_user_info(token_data)
            
            # Build service
            service = build('gmail', 'v1', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Error building Gmail service: {str(e)}")
            return None
    
    def test_gmail_connection(self, encrypted_token_data: str) -> bool:
        """Test Gmail connection."""
        try:
            service = self.build_gmail_service(encrypted_token_data)
            if not service:
                return False
            
            # Try to get user profile
            profile = service.users().getProfile(userId='me').execute()
            logger.info(f"Gmail connection test successful for {profile.get('emailAddress')}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail connection test failed: {str(e)}")
            return False
    
    def revoke_gmail_access(self, encrypted_token_data: str) -> bool:
        """Revoke Gmail access token."""
        try:
            token_data = json.loads(decrypt_sensitive_data(encrypted_token_data))
            credentials = Credentials.from_authorized_user_info(token_data)
            
            # Revoke the token
            credentials.revoke(Request())
            logger.info("Gmail access revoked successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking Gmail access: {str(e)}")
            return False
