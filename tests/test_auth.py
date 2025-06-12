"""
Test authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data


def test_register_duplicate_email(client: TestClient, test_user):
    """Test registration with duplicate email."""
    user_data = {
        "email": test_user.email,
        "password": "password123",
        "full_name": "Duplicate User"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client: TestClient, test_user):
    """Test successful login."""
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user):
    """Test login with invalid credentials."""
    login_data = {
        "email": test_user.email,
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_refresh_token(client: TestClient, test_user):
    """Test token refresh."""
    # First login to get tokens
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    
    login_response = client.post("/api/v1/auth/login", json=login_data)
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new access token
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/v1/auth/refresh", json=refresh_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(client: TestClient, auth_headers):
    """Test user logout."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "logged out" in response.json()["message"]


def test_change_password(client: TestClient, auth_headers):
    """Test password change."""
    password_data = {
        "current_password": "testpassword123",
        "new_password": "newtestpassword123"
    }
    
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
    assert response.status_code == 200
    assert "updated successfully" in response.json()["message"]


def test_change_password_wrong_current(client: TestClient, auth_headers):
    """Test password change with wrong current password."""
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newtestpassword123"
    }
    
    response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
    assert response.status_code == 400
    assert "Incorrect current password" in response.json()["detail"]
