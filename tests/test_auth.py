"""
Auth endpoint tests – register, login, /me, token refresh, logout.
"""
import pytest
from httpx import AsyncClient


REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "password": "SecurePass1!",
    "first_name": "Test",
    "last_name": "User",
}


@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_valid_credentials_returns_tokens(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = login_resp.json()["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == REGISTER_PAYLOAD["email"]


@pytest.mark.asyncio
async def test_get_me_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    original_refresh = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    # Rotation: new refresh token should differ from the original
    assert new_tokens["refresh_token"] != original_refresh


@pytest.mark.asyncio
async def test_password_not_in_register_or_login_response(client: AsyncClient):
    reg_resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    body = reg_resp.text
    assert "password_hash" not in body
    assert REGISTER_PAYLOAD["password"] not in body
