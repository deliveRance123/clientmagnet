import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_services_full_crud(async_client: AsyncClient):
    # 1. Register test user
    email = "services_crud@example.com"
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Services Tester"},
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Service
    create_payload = {
        "name": "Custom AI Chatbots",
        "description": "Enterprise customer support bots",
        "pricing": "$3,000 setup + $500/mo",
        "target_clients": "High volume e-commerce brands",
        "portfolio_links": "https://example.com/bot1, https://example.com/bot2",
        "is_active": True,
    }
    create_resp = await async_client.post("/api/v1/services/", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    svc = create_resp.json()
    svc_id = svc["id"]
    assert svc["name"] == "Custom AI Chatbots"
    assert svc["target_clients"] == "High volume e-commerce brands"
    assert svc["portfolio_links"] == "https://example.com/bot1, https://example.com/bot2"
    assert svc["is_active"] is True

    # 3. Get Service by ID
    get_resp = await async_client.get(f"/api/v1/services/{svc_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == svc_id

    # 4. Update Service (PATCH)
    patch_payload = {
        "name": "Custom AI Agents & Chatbots",
        "pricing": "$4,000 setup",
        "is_active": False,
    }
    patch_resp = await async_client.patch(f"/api/v1/services/{svc_id}", json=patch_payload, headers=headers)
    assert patch_resp.status_code == 200
    updated_svc = patch_resp.json()
    assert updated_svc["name"] == "Custom AI Agents & Chatbots"
    assert updated_svc["pricing"] == "$4,000 setup"
    assert updated_svc["is_active"] is False

    # 5. Toggle Service Active Status
    toggle_resp = await async_client.patch(f"/api/v1/services/{svc_id}/toggle", headers=headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is True

    # 6. Filter active services
    # Create an inactive service
    await async_client.post(
        "/api/v1/services/",
        json={"name": "Deprecated Service", "is_active": False},
        headers=headers,
    )
    all_svcs = await async_client.get("/api/v1/services/", headers=headers)
    assert len(all_svcs.json()) == 2

    active_svcs = await async_client.get("/api/v1/services/?active_only=true", headers=headers)
    assert len(active_svcs.json()) == 1
    assert active_svcs.json()[0]["name"] == "Custom AI Agents & Chatbots"

    # 7. Delete Service
    del_resp = await async_client.delete(f"/api/v1/services/{svc_id}", headers=headers)
    assert del_resp.status_code == 204

    # 8. Verify 404 after delete
    get_after_del = await async_client.get(f"/api/v1/services/{svc_id}", headers=headers)
    assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_services_isolation_and_auth(async_client: AsyncClient):
    # User 1
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "s_user1@example.com", "password": "Password123!", "full_name": "User 1"},
    )
    token1 = res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # User 2
    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "s_user2@example.com", "password": "Password123!", "full_name": "User 2"},
    )
    token2 = res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates service
    svc_res = await async_client.post(
        "/api/v1/services/",
        json={"name": "User 1 Service"},
        headers=headers1,
    )
    svc_id = svc_res.json()["id"]

    # User 2 cannot access, update, toggle or delete User 1's service (all return 404)
    assert (await async_client.get(f"/api/v1/services/{svc_id}", headers=headers2)).status_code == 404
    assert (await async_client.patch(f"/api/v1/services/{svc_id}", json={"name": "Hacked"}, headers=headers2)).status_code == 404
    assert (await async_client.patch(f"/api/v1/services/{svc_id}/toggle", headers=headers2)).status_code == 404
    assert (await async_client.delete(f"/api/v1/services/{svc_id}", headers=headers2)).status_code == 404

    # Unauthenticated access rejected with 401
    async_client.cookies.clear()
    assert (await async_client.get("/api/v1/services/")).status_code == 401
    assert (await async_client.post("/api/v1/services/", json={"name": "Unauthorized"})).status_code == 401
