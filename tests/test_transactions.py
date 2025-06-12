"""
Test transaction endpoints.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from fastapi.testclient import TestClient


def test_get_transactions_empty(client: TestClient, auth_headers):
    """Test getting transactions when none exist."""
    response = client.get("/api/v1/transactions/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_transaction(client: TestClient, auth_headers):
    """Test creating a new transaction."""
    transaction_data = {
        "amount": "25.99",
        "currency": "USD",
        "description": "Test transaction",
        "transaction_date": "2024-01-15T10:30:00",
        "transaction_type": "debit",
        "merchant_name": "Test Store"
    }
    
    response = client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["amount"] == "25.99"
    assert data["description"] == "Test transaction"
    assert data["merchant_name"] == "Test Store"


def test_get_transaction_by_id(client: TestClient, auth_headers):
    """Test getting a specific transaction."""
    # First create a transaction
    transaction_data = {
        "amount": "15.50",
        "currency": "USD",
        "description": "Coffee",
        "transaction_date": "2024-01-15T08:00:00",
        "transaction_type": "debit"
    }
    
    create_response = client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    transaction_id = create_response.json()["id"]
    
    # Get the transaction
    response = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == transaction_id
    assert data["amount"] == "15.50"


def test_update_transaction(client: TestClient, auth_headers):
    """Test updating a transaction."""
    # Create transaction
    transaction_data = {
        "amount": "20.00",
        "currency": "USD",
        "description": "Original description",
        "transaction_date": "2024-01-15T12:00:00",
        "transaction_type": "debit"
    }
    
    create_response = client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    transaction_id = create_response.json()["id"]
    
    # Update transaction
    update_data = {
        "description": "Updated description",
        "notes": "Added some notes"
    }
    
    response = client.put(f"/api/v1/transactions/{transaction_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["notes"] == "Added some notes"


def test_delete_transaction(client: TestClient, auth_headers):
    """Test deleting a transaction."""
    # Create transaction
    transaction_data = {
        "amount": "10.00",
        "currency": "USD",
        "description": "To be deleted",
        "transaction_date": "2024-01-15T14:00:00",
        "transaction_type": "debit"
    }
    
    create_response = client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    transaction_id = create_response.json()["id"]
    
    # Delete transaction
    response = client.delete(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/transactions/{transaction_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_transaction_filtering(client: TestClient, auth_headers):
    """Test transaction filtering."""
    # Create multiple transactions
    transactions = [
        {
            "amount": "50.00",
            "currency": "USD",
            "description": "Grocery shopping",
            "transaction_date": "2024-01-15T10:00:00",
            "transaction_type": "debit",
            "merchant_name": "Supermarket"
        },
        {
            "amount": "25.00",
            "currency": "USD",
            "description": "Gas station",
            "transaction_date": "2024-01-16T15:00:00",
            "transaction_type": "debit",
            "merchant_name": "Shell"
        }
    ]
    
    for transaction in transactions:
        client.post("/api/v1/transactions/", json=transaction, headers=auth_headers)
    
    # Test merchant name filter
    response = client.get("/api/v1/transactions/?merchant_name=Shell", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["merchant_name"] == "Shell"


def test_transaction_pagination(client: TestClient, auth_headers):
    """Test transaction pagination."""
    # Create multiple transactions
    for i in range(5):
        transaction_data = {
            "amount": f"{10 + i}.00",
            "currency": "USD",
            "description": f"Transaction {i}",
            "transaction_date": f"2024-01-{15 + i:02d}T10:00:00",
            "transaction_type": "debit"
        }
        client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    
    # Test pagination
    response = client.get("/api/v1/transactions/?page=1&size=3", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["size"] == 3
    assert data["has_next"] == True


def test_get_current_month_summary(client: TestClient, auth_headers):
    """Test getting current month transaction summary."""
    # Create some transactions
    transaction_data = {
        "amount": "100.00",
        "currency": "USD",
        "description": "Test expense",
        "transaction_date": datetime.now().isoformat(),
        "transaction_type": "debit"
    }
    
    client.post("/api/v1/transactions/", json=transaction_data, headers=auth_headers)
    
    response = client.get("/api/v1/transactions/summary/current-month", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_amount" in data
    assert "transaction_count" in data


def test_get_spending_summary(client: TestClient, auth_headers):
    """Test getting spending summary."""
    response = client.get("/api/v1/transactions/summary/spending?period=monthly", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["period"] == "monthly"
    assert "start_date" in data
    assert "end_date" in data
    assert "total_spent" in data
    assert "top_categories" in data
    assert "daily_breakdown" in data


def test_transaction_not_found(client: TestClient, auth_headers):
    """Test getting non-existent transaction."""
    response = client.get("/api/v1/transactions/999", headers=auth_headers)
    assert response.status_code == 404


def test_unauthorized_access(client: TestClient):
    """Test accessing transactions without authentication."""
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 401
