"""
Authentication endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import json

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token
)
from app.schemas.auth import (
    Token,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest
)
from app.schemas.user import User, UserCreate
from app.services.user_service import UserService
from app.api.v1.dependencies import get_current_active_user
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    """
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = user_service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = user_service.create(user_data)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get access token.
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = user_service.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Update user's refresh token
    user_service.update_refresh_token(user.id, refresh_token)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    user_id = verify_token(refresh_data.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_service = UserService(db)
    user = user_service.get_by_id(int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )
    
    # Verify stored refresh token matches
    if user.refresh_token != refresh_data.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    # Update user's refresh token
    user_service.update_refresh_token(user.id, new_refresh_token)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by invalidating refresh token.
    """
    user_service = UserService(db)
    user_service.update_refresh_token(current_user.id, None)
    
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    """
    user_service = UserService(db)
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    user_service.update_password(current_user.id, password_data.new_password)
    
    return {"message": "Password updated successfully"}


@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.
    """
    user_service = UserService(db)
    
    # Check if user exists
    user = user_service.get_by_email(reset_data.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token and send email
    reset_token = user_service.generate_password_reset_token(user.id)

    # Send password reset email
    from app.services.email_service import EmailService
    email_service = EmailService()
    email_sent = email_service.send_password_reset_email(user.email, reset_token)

    if not email_sent:
        logger.warning(f"Failed to send password reset email to {user.email}")

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    """
    user_service = UserService(db)
    
    # Verify and use reset token
    user = user_service.verify_password_reset_token(reset_data.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user_service.update_password(user.id, reset_data.new_password)

    return {"message": "Password reset successfully"}


@router.get("/gmail/authorize")
async def gmail_authorize(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get Gmail authorization URL for OAuth flow.
    """
    from app.services.gmail_service import GmailService

    gmail_service = GmailService()

    try:
        auth_url = gmail_service.get_authorization_url(current_user.id)
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create authorization URL: {str(e)}"
        )


@router.get("/gmail/callback")
async def gmail_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Gmail OAuth callback.
    """
    from app.services.gmail_service import GmailService
    from app.core.security import encrypt_sensitive_data

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )

    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )

    user_service = UserService(db)
    user = user_service.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    gmail_service = GmailService()

    try:
        # Exchange code for tokens
        result = gmail_service.exchange_code_for_tokens(code, user_id)

        # Encrypt and store token data
        encrypted_token = encrypt_sensitive_data(json.dumps(result['token_data']))
        user.gmail_token = encrypted_token
        db.commit()

        # Return success response (in production, redirect to frontend)
        return {
            "message": "Gmail connected successfully",
            "user_email": result['user_info'].get('email'),
            "redirect_url": "http://localhost:3000/settings?gmail=connected"  # Frontend URL
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Gmail: {str(e)}"
        )


@router.post("/gmail/disconnect")
async def gmail_disconnect(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Gmail integration.
    """
    from app.services.gmail_service import GmailService

    if not current_user.gmail_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected"
        )

    gmail_service = GmailService()

    try:
        # Revoke access token
        gmail_service.revoke_gmail_access(current_user.gmail_token)

        # Clear stored token
        user_service = UserService(db)
        user_service.update(
            db_obj=current_user,
            obj_in={"gmail_token": None}
        )

        return {"message": "Gmail disconnected successfully"}

    except Exception as e:
        # Clear token even if revocation fails
        user_service = UserService(db)
        user_service.update(
            db_obj=current_user,
            obj_in={"gmail_token": None}
        )

        return {"message": "Gmail disconnected (revocation may have failed)"}


@router.get("/gmail/status")
async def gmail_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Check Gmail connection status.
    """
    from app.services.gmail_service import GmailService

    if not current_user.gmail_token:
        return {"connected": False}

    gmail_service = GmailService()
    is_connected = gmail_service.test_gmail_connection(current_user.gmail_token)

    return {"connected": is_connected}
