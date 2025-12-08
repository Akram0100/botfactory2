# ============================================
# BotFactory AI - Auth API Tests
# ============================================

import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient, test_user_data: dict):
        """Test user registration."""
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"].lower()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # First registration
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Second registration with same email
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "allaqachon" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful login."""
        # Register first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: dict):
        """Test login with wrong password."""
        # Register first
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with wrong password
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "wrongpassword",
        })
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test accessing profile without token."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authorized(self, client: AsyncClient, test_user_data: dict):
        """Test accessing profile with token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        })
        token = login_response.json()["access_token"]
        
        # Get profile
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
