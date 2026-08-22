import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.lead import Lead
from app.models.user import User


@pytest.mark.asyncio
async def test_global_search_and_activity_timelines(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test global cross-entity search and activity timeline fetching."""
    # 1. Create searchable lead and client
    lead = Lead(
        user_id=test_user.id,
        name="Alexander Hamilton",
        company="Treasury Consulting",
        email="alex@treasury.gov",
        status="NEW",
        detected_need="Needs high-speed banking automation bot",
    )
    db_session.add(lead)
    await db_session.flush()

    client = Client(
        user_id=test_user.id,
        name="Thomas Jefferson",
        company="Monticello Design Studio",
        email="thomas@monticello.org",
        status="ACTIVE",
        service_purchased="Custom Web Platform",
    )
    db_session.add(client)
    await db_session.commit()

    # 2. Perform global search for "banking"
    search_res = await async_client.get(
        "/api/v1/search/?q=banking",
        headers=auth_headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_results"] >= 1
    assert any(r["title"] == "Alexander Hamilton" for r in search_data["results"])

    # 3. Perform global search for "Monticello"
    client_search_res = await async_client.get(
        "/api/v1/search/?q=Monticello",
        headers=auth_headers,
    )
    assert client_search_res.status_code == 200
    client_data = client_search_res.json()
    assert any(r["title"] == "Thomas Jefferson" for r in client_data["results"])

    # 4. Fetch activity timeline for lead
    timeline_res = await async_client.get(
        f"/api/v1/activities/lead/{lead.id}",
        headers=auth_headers,
    )
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()
    assert timeline_data["entity_id"] == lead.id
    assert isinstance(timeline_data["activities"], list)
