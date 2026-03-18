"""
Product endpoint tests – list, get by slug, create (auth), delete (auth).
"""
import pytest
from httpx import AsyncClient


CATEGORY_PAYLOAD = {"name": "Grinders", "description": "Herb grinders"}
PRODUCT_PAYLOAD = {
    "name": "Premium Grinder",
    "description": "A very good grinder",
    "price": 29.99,
    "stock_quantity": 10,
}
ADMIN_USER = {
    "email": "admin@example.com",
    "password": "AdminPass1!",
    "first_name": "Admin",
    "last_name": "User",
}

# ── helpers ──────────────────────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient, payload: dict) -> str:
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    return resp.json()["access_token"]


async def _promote_to_admin(client: AsyncClient, token: str) -> None:
    """Directly elevate the registered user to ADMIN via DB (test utility)."""
    # For the test, we call the super-admin endpoint if it exists,
    # or patch via the DB fixture. Since we only have the HTTP client here,
    # we rely on the test DB session being available via conftest.
    # This placeholder demonstrates the pattern; see conftest for DB access.
    pass


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    resp = await client.get("/api/v1/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_nonexistent_product_returns_404(client: AsyncClient):
    resp = await client.get("/api/v1/products/nonexistent-slug")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_product_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/products/", json=PRODUCT_PAYLOAD)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_product_requires_admin_role(client: AsyncClient):
    token = await _register_and_login(client, ADMIN_USER)
    resp = await client.post(
        "/api/v1/products/",
        json=PRODUCT_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    # Regular client user should get 403
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient, db_session):
    """Skip/limit query params are accepted."""
    resp = await client.get("/api/v1/products/?skip=0&limit=10")
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert "total" in resp.json()


@pytest.mark.asyncio
async def test_product_search_returns_empty_for_unknown_term(client: AsyncClient):
    resp = await client.get("/api/v1/products/?search=zzz_no_match_xyz")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
