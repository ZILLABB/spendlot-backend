"""
Security utilities for authentication and encryption.
"""
from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import secrets

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for sensitive data
def get_encryption_key() -> bytes:
    """Get or generate encryption key for sensitive data."""
    key = settings.ENCRYPTION_KEY
    if len(key) < 32:
        key = key.ljust(32, '0')
    return base64.urlsafe_b64encode(key[:32].encode())

fernet = Fernet(get_encryption_key())


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like API keys, tokens."""
    return fernet.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return fernet.decrypt(encrypted_data.encode()).decode()


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify JWT token and return subject if valid."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_sub: str = payload.get("sub")
        token_type_claim: str = payload.get("type")
        
        if token_sub is None or token_type_claim != token_type:
            return None
        return token_sub
    except jwt.JWTError:
        return None
