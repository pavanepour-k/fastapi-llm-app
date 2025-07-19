"""
Authentication tests
"""

import pytest
from httpx import AsyncClient


class TestAuthentication:
    """
    Test suite for authentication functionality.
    
    Single Responsibility: Authentication testing
    """
    
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
    
    async def test_register_duplicate_user(self, client: AsyncClient):
        """Test registration with duplicate username."""
        # Create first user
        await client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "email": "first@example.com",
            "full_name": "First User",
            "password": "password123"
        })
        
        # Try to create duplicate
        response = await client.post("/api/v1/auth/register", json={
            "username": "duplicate",
            "email": "second@example.com",
            "full_name": "Second User",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user first
        await client.post("/api/v1/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "password123"
        })
        
        # Login
        response = await client.post("/api/v1/auth/token", data={
            "username": "loginuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post("/api/v1/auth/token", data={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_get_current_user(self, authenticated_client: AsyncClient):
        """Test getting current user information."""
        response = await authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
