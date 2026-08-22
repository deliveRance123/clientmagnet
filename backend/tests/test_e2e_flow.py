import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_full_saas_lifecycle_e2e(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    End-to-end lifecycle verification:
    1. Register user
    2. Login and get token
    3. Create Service
    4. Discover & import lead
    5. Move stage to WON
    6. Convert to Client
    7. Verify in CRM Dashboard & Analytics
    """
    # 1. Register User
    reg_payload = {
        "email": "e2e_founder@agency.io",
        "password": "SecurePassword123!",
        "full_name": "E2E Founder",
        "company_name": "Magnet Growth Agency",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text

    # 2. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "e2e_founder@agency.io", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Service
    svc_res = await async_client.post(
        "/api/v1/services/",
        headers=headers,
        json={
            "name": "Full-Stack Web App Development",
            "pricing": "$5,000",
            "target_clients": "Tech Startups",
        },
    )
    assert svc_res.status_code == 201
    service_id = svc_res.json()["id"]

    # 4. Import Lead
    lead_res = await async_client.post(
        "/api/v1/discovery/import",
        headers=headers,
        json={
            "name": "Marcus Aurelius",
            "company": "Roman Ventures",
            "email": "marcus@meditations.com",
            "phone": "+1999888777",
            "description": "Looking for high performance web application developer for global expansion.",
            "source": "MANUAL",
            "analyze_with_ai": False,
        },
    )
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    # 5. Move stage to WON
    stage_res = await async_client.patch(
        f"/api/v1/crm/leads/{lead_id}/stage",
        headers=headers,
        json={"stage": "WON", "notes": "Contract signed and deposit received."},
    )
    assert stage_res.status_code == 200
    assert stage_res.json()["status"] == "WON"

    # 6. Convert to Client
    convert_res = await async_client.post(
        f"/api/v1/crm/leads/{lead_id}/convert-to-client",
        headers=headers,
        json={
            "service_id": service_id,
            "service_purchased": "Full-Stack Web App Development",
            "status": "ACTIVE",
            "notes": "Onboarding underway.",
        },
    )
    assert convert_res.status_code == 201
    assert convert_res.json()["name"] == "Marcus Aurelius"

    # 7. Check Dashboard & Analytics
    dash_res = await async_client.get("/api/v1/crm/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_leads"] >= 1
    assert dash_data["won_deals"] >= 1
    assert dash_data["active_clients"] >= 1

    ana_res = await async_client.get("/api/v1/crm/analytics", headers=headers)
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert ana_data["won_leads"] >= 1
