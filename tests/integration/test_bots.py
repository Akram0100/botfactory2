# ============================================
# BotFactory AI - Bot API Tests
# ============================================

import pytest
from httpx import AsyncClient


class TestBotAPI:
    """Tests for bot endpoints."""

    async def _get_auth_headers(self, client: AsyncClient, user_data: dict) -> dict:
        """Helper to register and get auth headers."""
        await client.post("/api/v1/auth/register", json=user_data)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_create_bot(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_bot_data: dict,
    ):
        """Test creating a new bot."""
        headers = await self._get_auth_headers(client, test_user_data)
        
        response = await client.post(
            "/api/v1/bots",
            json=test_bot_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_bot_data["name"]
        assert data["platform"] == test_bot_data["platform"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_bots(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_bot_data: dict,
    ):
        """Test listing user's bots."""
        headers = await self._get_auth_headers(client, test_user_data)
        
        # Create a bot
        await client.post("/api/v1/bots", json=test_bot_data, headers=headers)
        
        # List bots
        response = await client.get("/api/v1/bots", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_bot(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_bot_data: dict,
    ):
        """Test getting a specific bot."""
        headers = await self._get_auth_headers(client, test_user_data)
        
        # Create a bot
        create_response = await client.post(
            "/api/v1/bots",
            json=test_bot_data,
            headers=headers,
        )
        bot_id = create_response.json()["id"]
        
        # Get bot
        response = await client.get(f"/api/v1/bots/{bot_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bot_id

    @pytest.mark.asyncio
    async def test_update_bot(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_bot_data: dict,
    ):
        """Test updating a bot."""
        headers = await self._get_auth_headers(client, test_user_data)
        
        # Create a bot
        create_response = await client.post(
            "/api/v1/bots",
            json=test_bot_data,
            headers=headers,
        )
        bot_id = create_response.json()["id"]
        
        # Update bot
        response = await client.patch(
            f"/api/v1/bots/{bot_id}",
            json={"name": "Updated Bot Name"},
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Bot Name"

    @pytest.mark.asyncio
    async def test_delete_bot(
        self,
        client: AsyncClient,
        test_user_data: dict,
        test_bot_data: dict,
    ):
        """Test deleting a bot."""
        headers = await self._get_auth_headers(client, test_user_data)
        
        # Create a bot
        create_response = await client.post(
            "/api/v1/bots",
            json=test_bot_data,
            headers=headers,
        )
        bot_id = create_response.json()["id"]
        
        # Delete bot
        response = await client.delete(f"/api/v1/bots/{bot_id}", headers=headers)
        
        assert response.status_code == 200
        
        # Verify deleted
        get_response = await client.get(f"/api/v1/bots/{bot_id}", headers=headers)
        assert get_response.status_code == 404
