"""
Test user endpoints.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from app.services.receipt_service import ReceiptService
from app.services.transaction_service import TransactionService
from app.services.bank_account_service import BankAccountService
from app.schemas.receipt import ReceiptCreate
from app.schemas.transaction import TransactionCreate
from app.schemas.bank_account import BankAccountCreate


def test_get_current_user(client: TestClient, auth_headers):
    """Test getting current user information."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "full_name" in data
    assert "is_active" in data
    assert "is_verified" in data


def test_update_current_user(client: TestClient, auth_headers):
    """Test updating current user information."""
    update_data = {
        "full_name": "Updated Test User",
        "phone_number": "+1234567890",
        "timezone": "America/New_York",
        "currency": "EUR"
    }
    
    response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["full_name"] == "Updated Test User"
    assert data["phone_number"] == "+1234567890"
    assert data["timezone"] == "America/New_York"
    assert data["currency"] == "EUR"


def test_get_user_profile_empty(client: TestClient, auth_headers):
    """Test getting user profile with no data."""
    response = client.get("/api/v1/users/me/profile", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert data["total_receipts"] == 0
    assert data["total_transactions"] == 0
    assert data["total_spent_this_month"] == 0.0
    assert data["connected_accounts"] == 0


def test_get_user_profile_with_data(client: TestClient, auth_headers, test_user, db_session):
    """Test getting user profile with actual data."""
    # Create test data
    receipt_service = ReceiptService(db_session)
    transaction_service = TransactionService(db_session)
    bank_account_service = BankAccountService(db_session)

    # Create some receipts
    for i in range(3):
        receipt_service.create_from_upload(
            user_id=test_user.id,
            file_path=f"/test/path/{i}.jpg",
            original_filename=f"receipt_{i}.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            data_source_id=1
        )

    # Create some transactions (including current month expenses)
    now = datetime.utcnow()
    current_month_start = datetime(now.year, now.month, 1)

    # Current month transactions
    for i in range(2):
        from app.models.transaction import Transaction
        transaction = Transaction(
            user_id=test_user.id,
            amount=Decimal("-25.00"),  # Negative for expenses
            currency="USD",
            description=f"Current month expense {i}",
            transaction_date=current_month_start + timedelta(days=i),
            transaction_type="debit",
            data_source_id=1,
            processing_status="completed"
        )
        db_session.add(transaction)

    # Previous month transaction (should not count)
    prev_month = current_month_start - timedelta(days=1)
    prev_transaction = Transaction(
        user_id=test_user.id,
        amount=Decimal("-15.00"),
        currency="USD",
        description="Previous month expense",
        transaction_date=prev_month,
        transaction_type="debit",
        data_source_id=1,
        processing_status="completed"
    )
    db_session.add(prev_transaction)

    # Create a bank account
    from app.models.bank_account import BankAccount
    bank_account = BankAccount(
        user_id=test_user.id,
        account_name="Test Checking",
        account_type="checking",
        institution_name="Test Bank",
        current_balance=Decimal("1000.00"),
        currency="USD",
        is_active=True
    )
    db_session.add(bank_account)
    db_session.commit()

    # Get user profile
    response = client.get("/api/v1/users/me/profile", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_receipts"] == 3
    assert data["total_transactions"] == 3  # All transactions count
    assert data["total_spent_this_month"] == 50.0  # Only current month expenses
    assert data["connected_accounts"] == 1


def test_delete_current_user(client: TestClient, auth_headers):
    """Test deactivating current user account."""
    response = client.delete("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "deactivated successfully" in data["message"]


def test_get_user_profile_unauthorized(client: TestClient):
    """Test getting user profile without authentication."""
    response = client.get("/api/v1/users/me/profile")
    assert response.status_code == 401


def test_update_user_unauthorized(client: TestClient):
    """Test updating user without authentication."""
    update_data = {"full_name": "Unauthorized User"}
    response = client.put("/api/v1/users/me", json=update_data)
    assert response.status_code == 401
