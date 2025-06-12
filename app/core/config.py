"""
Application configuration settings.
"""
import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Spendlot Receipt Tracker"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API for Spendlot Receipt Tracker mobile app"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # Database
    DATABASE_URL: str = "postgresql://spendlot_user:spendlot_password@localhost:5432/spendlot"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Google Cloud Vision API
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = None
    
    # Gmail API
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/auth/gmail/callback"
    
    # Plaid API
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENVIRONMENT: str = "sandbox"  # sandbox, development, or production
    PLAID_PRODUCTS: str = "transactions,auth,identity"
    PLAID_COUNTRY_CODES: str = "US,CA"
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,pdf"
    UPLOAD_DIRECTORY: str = "uploads"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Email (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Superuser
    FIRST_SUPERUSER: EmailStr = "admin@spendlot.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
