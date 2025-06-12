"""
Test category endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_get_categories_empty(client: TestClient, auth_headers):
    """Test getting categories when none exist."""
    response = client.get("/api/v1/categories/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_create_category(client: TestClient, auth_headers):
    """Test creating a new category."""
    category_data = {
        "name": "Test Category",
        "description": "A test category",
        "color": "#FF5733",
        "icon": "shopping_cart",
        "is_income": False
    }
    
    response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Test Category"
    assert data["description"] == "A test category"
    assert data["color"] == "#FF5733"
    assert data["icon"] == "shopping_cart"
    assert data["is_income"] == False


def test_get_category_by_id(client: TestClient, auth_headers):
    """Test getting a specific category."""
    # First create a category
    category_data = {
        "name": "Food & Dining",
        "description": "Restaurant and food expenses",
        "color": "#4CAF50",
        "icon": "restaurant"
    }
    
    create_response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    category_id = create_response.json()["id"]
    
    # Get the category
    response = client.get(f"/api/v1/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "Food & Dining"


def test_update_category(client: TestClient, auth_headers):
    """Test updating a category."""
    # Create category
    category_data = {
        "name": "Original Name",
        "description": "Original description",
        "color": "#000000"
    }
    
    create_response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    category_id = create_response.json()["id"]
    
    # Update category
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "color": "#FFFFFF"
    }
    
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    assert data["color"] == "#FFFFFF"


def test_delete_category(client: TestClient, auth_headers):
    """Test deleting a category."""
    # Create category
    category_data = {
        "name": "To Be Deleted",
        "description": "This will be deleted"
    }
    
    create_response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    category_id = create_response.json()["id"]
    
    # Delete category
    response = client.delete(f"/api/v1/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_get_category_tree(client: TestClient, auth_headers):
    """Test getting category tree structure."""
    # Create parent category
    parent_data = {
        "name": "Parent Category",
        "description": "A parent category"
    }
    
    parent_response = client.post("/api/v1/categories/", json=parent_data, headers=auth_headers)
    parent_id = parent_response.json()["id"]
    
    # Create child category
    child_data = {
        "name": "Child Category",
        "description": "A child category",
        "parent_id": parent_id
    }
    
    client.post("/api/v1/categories/", json=child_data, headers=auth_headers)
    
    # Get category tree
    response = client.get("/api/v1/categories/tree", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_get_category_stats(client: TestClient, auth_headers):
    """Test getting category statistics."""
    # Create category
    category_data = {
        "name": "Test Stats Category",
        "description": "For testing stats"
    }
    
    create_response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    category_id = create_response.json()["id"]
    
    # Get category stats
    response = client.get(f"/api/v1/categories/{category_id}/stats", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "category" in data
    assert "transaction_count" in data
    assert "total_amount" in data
    assert "avg_amount" in data
    assert "percentage_of_total" in data


def test_create_category_with_parent(client: TestClient, auth_headers):
    """Test creating a category with a parent."""
    # Create parent category
    parent_data = {
        "name": "Parent",
        "description": "Parent category"
    }
    
    parent_response = client.post("/api/v1/categories/", json=parent_data, headers=auth_headers)
    parent_id = parent_response.json()["id"]
    
    # Create child category
    child_data = {
        "name": "Child",
        "description": "Child category",
        "parent_id": parent_id
    }
    
    response = client.post("/api/v1/categories/", json=child_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Child"
    assert data["parent_id"] == parent_id


def test_create_category_invalid_parent(client: TestClient, auth_headers):
    """Test creating a category with invalid parent."""
    category_data = {
        "name": "Invalid Parent Child",
        "parent_id": 999  # Non-existent parent
    }
    
    response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 400
    assert "Parent category not found" in response.json()["detail"]


def test_category_filtering(client: TestClient, auth_headers):
    """Test category filtering."""
    # Create active category
    active_data = {
        "name": "Active Category",
        "description": "This is active"
    }
    client.post("/api/v1/categories/", json=active_data, headers=auth_headers)
    
    # Test include_inactive filter
    response = client.get("/api/v1/categories/?include_inactive=false", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    # Should only return active categories
    for category in data:
        assert category.get("is_active", True) == True


def test_category_not_found(client: TestClient, auth_headers):
    """Test getting non-existent category."""
    response = client.get("/api/v1/categories/999", headers=auth_headers)
    assert response.status_code == 404


def test_unauthorized_category_access(client: TestClient):
    """Test accessing categories without authentication."""
    response = client.get("/api/v1/categories/")
    assert response.status_code == 401


def test_invalid_color_format(client: TestClient, auth_headers):
    """Test creating category with invalid color format."""
    category_data = {
        "name": "Invalid Color",
        "color": "invalid-color"  # Should be hex format
    }
    
    response = client.post("/api/v1/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error
