"""
Test receipt endpoints.
"""
import pytest
import io
from fastapi.testclient import TestClient


def test_get_receipts_empty(client: TestClient, auth_headers):
    """Test getting receipts when none exist."""
    response = client.get("/api/v1/receipts/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_upload_receipt_image(client: TestClient, auth_headers):
    """Test uploading a receipt image."""
    # Create a fake image file
    image_content = b"fake image content"
    files = {
        "file": ("receipt.jpg", io.BytesIO(image_content), "image/jpeg")
    }
    
    response = client.post("/api/v1/receipts/upload", files=files, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "receipt_id" in data
    assert "upload_id" in data
    assert data["processing_status"] == "pending"


def test_upload_receipt_with_data(client: TestClient, auth_headers):
    """Test uploading receipt with additional data."""
    image_content = b"fake image content"
    files = {
        "file": ("receipt.jpg", io.BytesIO(image_content), "image/jpeg")
    }
    data = {
        "merchant_name": "Test Store",
        "amount": "25.99",
        "notes": "Test receipt"
    }
    
    response = client.post("/api/v1/receipts/upload", files=files, data=data, headers=auth_headers)
    assert response.status_code == 200


def test_upload_invalid_file_type(client: TestClient, auth_headers):
    """Test uploading invalid file type."""
    file_content = b"not an image"
    files = {
        "file": ("document.txt", io.BytesIO(file_content), "text/plain")
    }
    
    response = client.post("/api/v1/receipts/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "File type not allowed" in response.json()["detail"]


def test_get_receipt_not_found(client: TestClient, auth_headers):
    """Test getting non-existent receipt."""
    response = client.get("/api/v1/receipts/999", headers=auth_headers)
    assert response.status_code == 404


def test_update_receipt(client: TestClient, auth_headers):
    """Test updating a receipt."""
    # First upload a receipt
    image_content = b"fake image content"
    files = {
        "file": ("receipt.jpg", io.BytesIO(image_content), "image/jpeg")
    }
    
    upload_response = client.post("/api/v1/receipts/upload", files=files, headers=auth_headers)
    receipt_id = upload_response.json()["receipt_id"]
    
    # Update the receipt
    update_data = {
        "merchant_name": "Updated Store",
        "amount": "30.99",
        "notes": "Updated notes"
    }
    
    response = client.put(f"/api/v1/receipts/{receipt_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["merchant_name"] == "Updated Store"


def test_delete_receipt(client: TestClient, auth_headers):
    """Test deleting a receipt."""
    # First upload a receipt
    image_content = b"fake image content"
    files = {
        "file": ("receipt.jpg", io.BytesIO(image_content), "image/jpeg")
    }
    
    upload_response = client.post("/api/v1/receipts/upload", files=files, headers=auth_headers)
    receipt_id = upload_response.json()["receipt_id"]
    
    # Delete the receipt
    response = client.delete(f"/api/v1/receipts/{receipt_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/receipts/{receipt_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_receipts_pagination(client: TestClient, auth_headers):
    """Test receipt pagination."""
    # Upload multiple receipts
    for i in range(5):
        image_content = f"fake image content {i}".encode()
        files = {
            "file": (f"receipt_{i}.jpg", io.BytesIO(image_content), "image/jpeg")
        }
        client.post("/api/v1/receipts/upload", files=files, headers=auth_headers)
    
    # Test pagination
    response = client.get("/api/v1/receipts/?page=1&size=3", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["size"] == 3
    assert data["has_next"] == True
