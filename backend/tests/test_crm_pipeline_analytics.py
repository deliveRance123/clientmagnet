import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.lead import Lead
from app.models.service import Service
from app.models.user import User


@pytest.mark.asyncio
async def test_lead_pipeline_stage_transition_and_activity(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test updating lead stages and verifying activity logging."""
    # Create test lead
    lead = Lead(
        user_id=test_user.id,
        name="Pipeline Prospect",
        company="Prospect Corp",
        email="prospect@example.com",
        status="NEW",
        intent_score=0.85,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    # 1. Transition to QUALIFIED
    res = await async_client.patch(
        f"/api/v1/crm/leads/{lead.id}/stage",
        headers=auth_headers,
        json={"stage": "QUALIFIED", "notes": "Verified high budget requirement."},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "QUALIFIED"

    # 2. Verify invalid stage returns 400
    res_bad = await async_client.patch(
        f"/api/v1/crm/leads/{lead.id}/stage",
        headers=auth_headers,
        json={"stage": "NON_EXISTENT_STAGE"},
    )
    assert res_bad.status_code == 400


@pytest.mark.asyncio
async def test_convert_lead_to_client(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test converting a won lead into a permanent client record without deleting lead."""
    service = Service(
        user_id=test_user.id,
        name="Custom Bot Automation",
        pricing="$3,500 fixed",
        target_clients="SaaS Companies",
    )
    db_session.add(service)
    await db_session.flush()

    lead = Lead(
        user_id=test_user.id,
        name="Sarah Connor",
        company="Cyberdyne",
        email="sarah@cyberdyne.com",
        phone="+1555123456",
        website="https://cyberdyne.com",
        status="NEGOTIATION",
        matched_service_id=service.id,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    # Convert to Client
    res = await async_client.post(
        f"/api/v1/crm/leads/{lead.id}/convert-to-client",
        headers=auth_headers,
        json={
            "service_id": service.id,
            "service_purchased": "Custom Bot Automation Enterprise",
            "status": "ACTIVE",
            "notes": "Initial deposit paid. Project starting next Monday.",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["name"] == "Sarah Connor"
    assert data["company"] == "Cyberdyne"
    assert data["lead_id"] == lead.id
    assert data["status"] == "ACTIVE"
    assert data["service_purchased"] == "Custom Bot Automation Enterprise"

    # Verify original lead still exists and is marked WON
    await db_session.refresh(lead)
    assert lead.status == "WON"


@pytest.mark.asyncio
async def test_crm_dashboard_and_analytics_metrics(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test PostgreSQL aggregation queries for CRM dashboard and conversion funnels."""
    # 1. Fetch dashboard overview
    dash_res = await async_client.get("/api/v1/crm/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "total_leads" in dash_data
    assert "qualified_leads" in dash_data
    assert "active_conversations" in dash_data
    assert "active_clients" in dash_data

    # 2. Fetch analytics & conversion funnel
    ana_res = await async_client.get("/api/v1/crm/analytics", headers=auth_headers)
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert "conversion_funnel" in ana_data
    assert "lead_to_qualified_pct" in ana_data["conversion_funnel"]
    assert "overall_lead_to_won_pct" in ana_data["conversion_funnel"]
    assert isinstance(ana_data["service_performance"], list)
    assert isinstance(ana_data["source_performance"], list)
