import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_data_isolation(async_client: AsyncClient):
    """
    Test strict multi-tenant user isolation:
    User A can access User A's data.
    User B can access User B's data.
    User A cannot access User B's data.
    User B cannot access User A's data.
    """
    # 1. Register User A
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.a@example.com",
            "password": "Password123!",
            "full_name": "User A",
        },
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "user.b@example.com",
            "password": "Password123!",
            "full_name": "User B",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates 2 leads
    lead_a1_res = await async_client.post(
        "/api/v1/leads/",
        headers=headers_a,
        json={
            "name": "Acme Corp (User A Lead 1)",
            "source": "LINKEDIN",
            "status": "NEW",
        },
    )
    assert lead_a1_res.status_code == 201
    lead_a1_id = lead_a1_res.json()["id"]

    lead_a2_res = await async_client.post(
        "/api/v1/leads/",
        headers=headers_a,
        json={
            "name": "Beta LLC (User A Lead 2)",
            "source": "OTHER",
            "status": "CONTACTED",
        },
    )
    assert lead_a2_res.status_code == 201

    # 4. User B creates 1 lead
    lead_b1_res = await async_client.post(
        "/api/v1/leads/",
        headers=headers_b,
        json={
            "name": "Gamma Inc (User B Lead 1)",
            "source": "X",
            "status": "QUALIFIED",
        },
    )
    assert lead_b1_res.status_code == 201
    lead_b1_id = lead_b1_res.json()["id"]

    # 5. Verify User A only sees User A's leads
    user_a_leads = await async_client.get("/api/v1/leads/", headers=headers_a)
    assert user_a_leads.status_code == 200
    a_leads_list = user_a_leads.json()
    assert len(a_leads_list) == 2
    a_lead_ids = [l["id"] for l in a_leads_list]
    assert lead_a1_id in a_lead_ids
    assert lead_b1_id not in a_lead_ids

    # 6. Verify User B only sees User B's leads
    user_b_leads = await async_client.get("/api/v1/leads/", headers=headers_b)
    assert user_b_leads.status_code == 200
    b_leads_list = user_b_leads.json()
    assert len(b_leads_list) == 1
    assert b_leads_list[0]["id"] == lead_b1_id

    # 7. Verify User B CANNOT access User A's lead directly by ID (must return 404)
    cross_access_b_to_a = await async_client.get(
        f"/api/v1/leads/{lead_a1_id}", headers=headers_b
    )
    assert cross_access_b_to_a.status_code == 404

    # 8. Verify User A CANNOT access User B's lead directly by ID (must return 404)
    cross_access_a_to_b = await async_client.get(
        f"/api/v1/leads/{lead_b1_id}", headers=headers_a
    )
    assert cross_access_a_to_b.status_code == 404

    # 9. Verify User A CAN access their own lead directly by ID
    own_access_a = await async_client.get(
        f"/api/v1/leads/{lead_a1_id}", headers=headers_a
    )
    assert own_access_a.status_code == 200
    assert own_access_a.json()["id"] == lead_a1_id

    # 10. Verify truly unauthenticated access (cookies cleared, no headers) is rejected with 401
    async_client.cookies.clear()
    unauth_access = await async_client.get(f"/api/v1/leads/{lead_a1_id}")
    assert unauth_access.status_code == 401


@pytest.mark.asyncio
async def test_services_and_clients_user_isolation(async_client: AsyncClient):
    # Register and authenticate User A
    email_a = "user.a.svc@example.com"
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "User A"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register and authenticate User B
    email_b = "user.b.svc@example.com"
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "User B"},
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A creates a service
    svc_a_res = await async_client.post(
        "/api/v1/services/",
        headers=headers_a,
        json={"name": "User A Service", "description": "Desc A", "pricing": "Free", "is_active": True},
    )
    assert svc_a_res.status_code == 201
    svc_a_id = svc_a_res.json()["id"]

    # 2. User B creates a service
    svc_b_res = await async_client.post(
        "/api/v1/services/",
        headers=headers_b,
        json={"name": "User B Service", "description": "Desc B", "pricing": "Paid", "is_active": True},
    )
    assert svc_b_res.status_code == 201
    svc_b_id = svc_b_res.json()["id"]

    # 3. User A lists services (should only see User A's service)
    list_a_res = await async_client.get("/api/v1/services/", headers=headers_a)
    assert list_a_res.status_code == 200
    assert len(list_a_res.json()) == 1
    assert list_a_res.json()[0]["id"] == svc_a_id

    # 4. User B lists services (should only see User B's service)
    list_b_res = await async_client.get("/api/v1/services/", headers=headers_b)
    assert len(list_b_res.json()) == 1
    assert list_b_res.json()[0]["id"] == svc_b_id

    # 5. User A creates a client
    client_a_res = await async_client.post(
        "/api/v1/clients/",
        headers=headers_a,
        json={"name": "Client A", "company": "Corp A", "email": "client.a@example.com"},
    )
    assert client_a_res.status_code == 201
    client_a_id = client_a_res.json()["id"]

    # 6. User B creates a client
    client_b_res = await async_client.post(
        "/api/v1/clients/",
        headers=headers_b,
        json={"name": "Client B", "company": "Corp B", "email": "client.b@example.com"},
    )
    assert client_b_res.status_code == 201
    client_b_id = client_b_res.json()["id"]

    # 7. User A lists clients (should only see User A's client)
    clients_a_list = await async_client.get("/api/v1/clients/", headers=headers_a)
    assert len(clients_a_list.json()) == 1
    assert clients_a_list.json()[0]["id"] == client_a_id

    # 8. User B lists clients (should only see User B's client)
    clients_b_list = await async_client.get("/api/v1/clients/", headers=headers_b)
    assert len(clients_b_list.json()) == 1
    assert clients_b_list.json()[0]["id"] == client_b_id

    # 9. Verify User B CANNOT link their client to User A's lead
    # Create Lead for User A
    lead_a_res = await async_client.post(
        "/api/v1/leads/",
        headers=headers_a,
        json={"name": "Lead A"},
    )
    lead_a_id = lead_a_res.json()["id"]
    
    # User B tries to link client to User A's lead_id
    bad_client_res = await async_client.post(
        "/api/v1/clients/",
        headers=headers_b,
        json={"name": "Client Bad", "lead_id": lead_a_id},
    )
    assert bad_client_res.status_code == 400

