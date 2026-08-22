import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.lead import Lead


@pytest.mark.asyncio
async def test_services_api_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Register test user - token comes directly from register response
    email = "service_api@example.com"
    user_in = {"email": email, "password": "Password123!", "full_name": "API Service Tester"}
    reg_resp = await async_client.post("/api/v1/auth/register", json=user_in)
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get services (should be empty initially)
    get_resp = await async_client.get("/api/v1/services/", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 0

    # 3. Create a service
    svc_data = {
        "name": "SEO Optimization",
        "description": "Boost Google rankings",
        "pricing": "$150/hr",
        "is_active": True,
    }
    post_resp = await async_client.post("/api/v1/services/", json=svc_data, headers=headers)
    assert post_resp.status_code == 201
    created_svc = post_resp.json()
    assert created_svc["name"] == "SEO Optimization"
    assert created_svc["pricing"] == "$150/hr"

    # 4. Get services (should contain created service)
    get_resp = await async_client.get("/api/v1/services/", headers=headers)
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["name"] == "SEO Optimization"

    # 5. Unauthenticated request should be rejected (clear cookies from previous session first)
    async_client.cookies.clear()
    unauth_resp = await async_client.get("/api/v1/services/")
    assert unauth_resp.status_code == 401


@pytest.mark.asyncio
async def test_clients_api_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    email = "client_api@example.com"
    user_in = {"email": email, "password": "Password123!", "full_name": "API Client Tester"}
    reg_resp = await async_client.post("/api/v1/auth/register", json=user_in)
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user object to create Lead directly in DB
    user_query = select(User).where(User.email == email)
    user_res = await db_session.execute(user_query)
    user = user_res.scalar_one()

    # Create a Lead
    lead = Lead(user_id=user.id, name="Interested Lead")
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    # Get clients (empty initially)
    get_resp = await async_client.get("/api/v1/clients/", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 0

    # Create client WITHOUT lead link
    client_data = {
        "name": "Standalone Client",
        "company": "Big Corp",
        "email": "standalone@bigcorp.com",
        "status": "Active",
        "notes": "Direct client signup",
    }
    post_resp = await async_client.post("/api/v1/clients/", json=client_data, headers=headers)
    assert post_resp.status_code == 201
    created_client = post_resp.json()
    assert created_client["name"] == "Standalone Client"
    assert created_client["lead_id"] is None

    # Create client WITH lead link (lead belongs to same user)
    client_linked = {
        "name": "Promoted Client",
        "company": "Linked Corp",
        "email": "promoted@linkedcorp.com",
        "status": "Active",
        "lead_id": lead.id,
    }
    linked_resp = await async_client.post("/api/v1/clients/", json=client_linked, headers=headers)
    assert linked_resp.status_code == 201
    assert linked_resp.json()["lead_id"] == lead.id

    # Get clients (should contain 2 clients)
    get_resp = await async_client.get("/api/v1/clients/", headers=headers)
    assert len(get_resp.json()) == 2
