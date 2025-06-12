"""
Test analytics endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


def test_get_spending_summary_default(client: TestClient, auth_headers):
    """Test getting spending summary with default parameters."""
    response = client.get("/api/v1/analytics/spending-summary", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "period" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "total_spent" in data
    assert "total_income" in data
    assert "transaction_count" in data
    assert "top_categories" in data
    assert "daily_breakdown" in data


def test_get_spending_summary_daily(client: TestClient, auth_headers):
    """Test getting daily spending summary."""
    response = client.get("/api/v1/analytics/spending-summary?period=daily", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["period"] == "daily"


def test_get_spending_summary_weekly(client: TestClient, auth_headers):
    """Test getting weekly spending summary."""
    response = client.get("/api/v1/analytics/spending-summary?period=weekly", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["period"] == "weekly"


def test_get_spending_summary_yearly(client: TestClient, auth_headers):
    """Test getting yearly spending summary."""
    response = client.get("/api/v1/analytics/spending-summary?period=yearly", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["period"] == "yearly"


def test_get_spending_summary_custom_dates(client: TestClient, auth_headers):
    """Test getting spending summary with custom date range."""
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T23:59:59"
    
    response = client.get(
        f"/api/v1/analytics/spending-summary?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["start_date"] == start_date
    assert data["end_date"] == end_date


def test_get_category_statistics(client: TestClient, auth_headers):
    """Test getting category statistics."""
    response = client.get("/api/v1/analytics/category-stats", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    # Check structure of category stats
    if data:
        stat = data[0]
        assert "category" in stat
        assert "transaction_count" in stat
        assert "total_amount" in stat
        assert "avg_amount" in stat
        assert "percentage_of_total" in stat


def test_get_category_statistics_with_date_range(client: TestClient, auth_headers):
    """Test getting category statistics with custom date range."""
    start_date = "2024-01-01T00:00:00"
    end_date = "2024-01-31T23:59:59"
    
    response = client.get(
        f"/api/v1/analytics/category-stats?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_category_statistics_with_limit(client: TestClient, auth_headers):
    """Test getting category statistics with limit."""
    response = client.get("/api/v1/analytics/category-stats?limit=5", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) <= 5


def test_get_monthly_trends(client: TestClient, auth_headers):
    """Test getting monthly spending trends."""
    response = client.get("/api/v1/analytics/monthly-trends", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "trends" in data
    assert "period" in data
    assert isinstance(data["trends"], list)
    
    # Check structure of trends
    if data["trends"]:
        trend = data["trends"][0]
        assert "year" in trend
        assert "month" in trend
        assert "total_spent" in trend
        assert "transaction_count" in trend
        assert "month_name" in trend


def test_get_monthly_trends_custom_months(client: TestClient, auth_headers):
    """Test getting monthly trends with custom month count."""
    response = client.get("/api/v1/analytics/monthly-trends?months=6", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "Last 6 months" in data["period"]


def test_get_receipt_statistics(client: TestClient, auth_headers):
    """Test getting receipt processing statistics."""
    response = client.get("/api/v1/analytics/receipt-stats", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "total_receipts" in data
    assert "processed_receipts" in data
    assert "pending_receipts" in data
    assert "failed_receipts" in data
    assert "verified_receipts" in data
    assert "processing_rate" in data
    assert "verification_rate" in data
    assert "avg_ocr_confidence" in data


def test_analytics_with_transactions(client: TestClient, auth_headers):
    """Test analytics endpoints after creating some transactions."""
    # Create a few test transactions
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
            "description": "Coffee",
            "transaction_date": "2024-01-16T08:00:00",
            "transaction_type": "debit",
            "merchant_name": "Starbucks"
        },
        {
            "amount": "1000.00",
            "currency": "USD",
            "description": "Salary",
            "transaction_date": "2024-01-01T00:00:00",
            "transaction_type": "credit"
        }
    ]
    
    for transaction in transactions:
        client.post("/api/v1/transactions/", json=transaction, headers=auth_headers)
    
    # Test spending summary
    response = client.get("/api/v1/analytics/spending-summary", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["transaction_count"] >= 3
    assert float(data["total_income"]) >= 1000.00
    assert float(data["total_spent"]) >= 75.00


def test_invalid_period_parameter(client: TestClient, auth_headers):
    """Test analytics with invalid period parameter."""
    response = client.get("/api/v1/analytics/spending-summary?period=invalid", headers=auth_headers)
    assert response.status_code == 422  # Validation error


def test_invalid_date_format(client: TestClient, auth_headers):
    """Test analytics with invalid date format."""
    response = client.get(
        "/api/v1/analytics/spending-summary?start_date=invalid-date",
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


def test_analytics_unauthorized(client: TestClient):
    """Test accessing analytics without authentication."""
    response = client.get("/api/v1/analytics/spending-summary")
    assert response.status_code == 401


def test_category_stats_limit_validation(client: TestClient, auth_headers):
    """Test category stats with invalid limit values."""
    # Test limit too high
    response = client.get("/api/v1/analytics/category-stats?limit=100", headers=auth_headers)
    assert response.status_code == 422
    
    # Test limit too low
    response = client.get("/api/v1/analytics/category-stats?limit=0", headers=auth_headers)
    assert response.status_code == 422


def test_monthly_trends_limit_validation(client: TestClient, auth_headers):
    """Test monthly trends with invalid month values."""
    # Test months too high
    response = client.get("/api/v1/analytics/monthly-trends?months=30", headers=auth_headers)
    assert response.status_code == 422
    
    # Test months too low
    response = client.get("/api/v1/analytics/monthly-trends?months=0", headers=auth_headers)
    assert response.status_code == 422
