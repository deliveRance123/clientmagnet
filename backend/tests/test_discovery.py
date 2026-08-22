import io
import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery import LeadDiscoveryRun, LeadDiscoverySource
from app.models.lead import Lead
from app.models.lead_source import LeadSource
from app.models.user import User
from app.schemas.discovery import (
    DiscoverySourceCreate,
    ManualLeadImportRequest,
    NormalizedOpportunity,
    RawOpportunity,
)
from app.services.ai import AIService, MockProvider
from app.services.discovery import (
    DeduplicationService,
    DiscoveryEngine,
    LeadNormalizer,
    MockDiscoveryProvider,
)


# Helper to register user and get auth headers
async def create_user_and_headers(async_client: AsyncClient, email: str = "discoverer@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Lead Scout Tester",
            "company_name": "Discovery Automation Lab",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Provider & Normalizer Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_discovery_provider():
    """Verify MockDiscoveryProvider returns structured raw opportunities."""
    provider = MockDiscoveryProvider()
    opps = await provider.fetch_opportunities({"name": "Test Feed"})
    assert len(opps) >= 3
    assert all(isinstance(o, RawOpportunity) for o in opps)
    assert any("website redesign" in o.title.lower() for o in opps)
    assert any("whatsapp" in o.title.lower() or "bot" in o.title.lower() for o in opps)


def test_lead_normalizer_html_stripping_and_field_mapping():
    """Verify LeadNormalizer removes HTML markup and normalizes fields."""
    raw = RawOpportunity(
        external_id="ext-999",
        title="Acme Global: Senior Frontend React Developer",
        description="<p>We are looking for a <strong>Next.js</strong> expert with <em>5+ years</em> experience.</p>",
        url="https://jobs.example.com/acme-999",
        location="Remote",
        platform="WEB",
        source="Custom Job Feed",
        email="jobs@acmeglobal.com",
        website="https://acmeglobal.com",
    )
    norm = LeadNormalizer.normalize(raw)
    assert isinstance(norm, NormalizedOpportunity)
    assert norm.name == "Acme Global: Senior Frontend React Developer"
    assert norm.company == "Acme Global"
    assert "<p>" not in norm.description
    assert "<strong>" not in norm.description
    assert "Next.js expert with 5+ years experience." in norm.description
    assert norm.source_url == "https://jobs.example.com/acme-999"


# ---------------------------------------------------------------------------
# 2. Deduplication Service Tests (5 Signals)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplication_all_signals(db_session: AsyncSession):
    """Test deduplication across source_url, email, website, and name+company."""
    user = User(
        email="dedup_tester@example.com",
        hashed_password="hashed_dummy_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Insert an existing baseline lead
    existing_lead = Lead(
        user_id=user.id,
        name="Existing Prospect",
        company="Omega Ventures",
        email="omega@example.com",
        website="https://omegaventures.io",
        source="Job Board",
        source_url="https://jobs.example.com/omega-1",
        description="Omega looking for bot development",
        intent_score=80.0,
    )
    db_session.add(existing_lead)
    await db_session.commit()

    # 1. Matching source_url
    dup_url = NormalizedOpportunity(
        name="Different Title",
        description="Some desc",
        platform="WEB",
        source="Any",
        source_url="https://jobs.example.com/omega-1",
    )
    is_dup, reason = await DeduplicationService.is_duplicate(db_session, user.id, dup_url)
    assert is_dup is True
    assert "source URL" in reason

    # 2. Matching email
    dup_email = NormalizedOpportunity(
        name="Different Title",
        email="omega@example.com",
        description="Some desc",
        platform="WEB",
        source="Any",
    )
    is_dup, reason = await DeduplicationService.is_duplicate(db_session, user.id, dup_email)
    assert is_dup is True
    assert "email" in reason

    # 3. Matching website
    dup_web = NormalizedOpportunity(
        name="Different Title",
        website="https://omegaventures.io/",
        description="Some desc",
        platform="WEB",
        source="Any",
    )
    is_dup, reason = await DeduplicationService.is_duplicate(db_session, user.id, dup_web)
    assert is_dup is True
    assert "website" in reason

    # 4. Matching Name + Company
    dup_name_comp = NormalizedOpportunity(
        name="Existing Prospect",
        company="Omega Ventures",
        description="Some desc",
        platform="WEB",
        source="Any",
    )
    is_dup, reason = await DeduplicationService.is_duplicate(db_session, user.id, dup_name_comp)
    assert is_dup is True
    assert "name & company" in reason

    # 5. Non-duplicate lead
    clean_opp = NormalizedOpportunity(
        name="Brand New Prospect",
        company="Starlight Studio",
        email="star@starlight.io",
        website="https://starlight.io",
        description="Looking for website redesign",
        platform="WEB",
        source="Any",
        source_url="https://jobs.example.com/starlight-new",
    )
    is_dup, _ = await DeduplicationService.is_duplicate(db_session, user.id, clean_opp)
    assert is_dup is False


# ---------------------------------------------------------------------------
# 3. Discovery Engine Service Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discovery_engine_run_source_and_duplicate_handling(db_session: AsyncSession):
    """Verify discovery engine processes opportunities, enriches with AI, and skips duplicates on rerun."""
    user = User(
        email="engine_tester@example.com",
        hashed_password="hashed_dummy_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Configure a mock discovery source
    source = LeadDiscoverySource(
        user_id=user.id,
        name="Dev Mock Opportunities",
        source_type="MOCK",
        is_active=True,
        frequency="DAILY",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    ai_service = AIService(MockProvider())
    engine = DiscoveryEngine(ai_service=ai_service)

    # Run 1: First scout run
    run1 = await engine.run_source(db=db_session, user=user, source=source, analyze_with_ai=True)
    assert run1.status == "SUCCESS"
    assert run1.total_discovered >= 3
    assert run1.accepted_count >= 3
    assert run1.duplicate_count == 0

    # Verify leads were inserted in DB
    query = select(Lead).where(Lead.user_id == user.id)
    leads = (await db_session.execute(query)).scalars().all()
    assert len(leads) >= 3
    assert all(l.detected_need is not None for l in leads)
    assert all(0 <= l.intent_score <= 100 for l in leads)

    # Run 2: Second scout run on same source -> all should be detected as duplicates
    run2 = await engine.run_source(db=db_session, user=user, source=source, analyze_with_ai=True)
    assert run2.status == "SUCCESS"
    assert run2.total_discovered >= 3
    assert run2.accepted_count == 0
    assert run2.duplicate_count >= 3


@pytest.mark.asyncio
async def test_discovery_engine_csv_import(db_session: AsyncSession):
    """Verify CSV parser imports valid rows, skips duplicates, and flags malformed rows."""
    user = User(
        email="csv_tester@example.com",
        hashed_password="hashed_dummy_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    engine = DiscoveryEngine(ai_service=AIService(MockProvider()))

    csv_data = """name,company,email,website,description,source
Alice Wonderland,Wonderland Tea,alice@wonderland.com,https://wonderland.com,Looking for brand graphics package,LinkedIn
Bob Builder,Bob Construction,bob@builder.com,,Need automated client SMS appointment system,Twitter
,No Name Corp,bad@company.com,,Missing name row,Manual
Charlie Chocolate,Wonka Factory,invalid-email-format,,Need eCommerce store overhaul,Referral
Alice Wonderland,Wonderland Tea,alice@wonderland.com,https://wonderland.com,Duplicate row,LinkedIn
"""
    result = await engine.import_csv_leads(
        db=db_session, user=user, csv_content=csv_data, analyze_with_ai=False
    )
    assert result.total_rows == 5
    assert result.imported_count == 2  # Alice and Bob
    assert result.duplicate_count == 1  # Second Alice
    assert result.rejected_count == 2  # Missing name and invalid email
    assert len(result.errors) == 2


# ---------------------------------------------------------------------------
# 4. Authenticated REST API Endpoints Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_discovery_sources_crud(async_client: AsyncClient):
    """Test full CRUD endpoints for discovery sources."""
    token, headers = await create_user_and_headers(async_client, "sources_crud@example.com")

    # 1. Create Source
    create_resp = await async_client.post(
        "/api/v1/discovery/sources",
        json={
            "name": "RemoteOK Web Dev",
            "source_type": "JOB_BOARD",
            "feed_url": "https://remoteok.com/api",
            "frequency": "HOURLY",
            "is_active": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    source = create_resp.json()
    source_id = source["id"]
    assert source["name"] == "RemoteOK Web Dev"
    assert source["source_type"] == "JOB_BOARD"

    # 2. List Sources
    list_resp = await async_client.get("/api/v1/discovery/sources", headers=headers)
    assert list_resp.status_code == 200
    sources_list = list_resp.json()
    assert len(sources_list) >= 1
    assert sources_list[0]["id"] == source_id

    # 3. Update Source
    patch_resp = await async_client.patch(
        f"/api/v1/discovery/sources/{source_id}",
        json={"name": "RemoteOK Global Tech", "is_active": False},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "RemoteOK Global Tech"
    assert patch_resp.json()["is_active"] is False

    # 4. Delete Source
    del_resp = await async_client.delete(
        f"/api/v1/discovery/sources/{source_id}", headers=headers
    )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_authenticated_discovery_run_and_runs_history(async_client: AsyncClient):
    """Test triggering discovery run and querying run logs."""
    token, headers = await create_user_and_headers(async_client, "run_tester@example.com")

    # Create a mock source
    src_resp = await async_client.post(
        "/api/v1/discovery/sources",
        json={"name": "API Mock Source", "source_type": "MOCK", "is_active": True},
        headers=headers,
    )
    source_id = src_resp.json()["id"]

    # Trigger discovery run
    run_resp = await async_client.post(
        "/api/v1/discovery/run",
        json={"source_id": source_id, "analyze_with_ai": True},
        headers=headers,
    )
    assert run_resp.status_code == 200
    runs = run_resp.json()
    assert len(runs) == 1
    assert runs[0]["status"] == "SUCCESS"
    assert runs[0]["accepted_count"] >= 3

    # Query discovery runs history
    history_resp = await async_client.get("/api/v1/discovery/runs", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["source_id"] == source_id


@pytest.mark.asyncio
async def test_authenticated_manual_lead_import_endpoint(async_client: AsyncClient):
    """Test manual lead import endpoint with AI analysis."""
    token, headers = await create_user_and_headers(async_client, "manual_importer@example.com")

    resp = await async_client.post(
        "/api/v1/discovery/import",
        json={
            "name": "David Miller",
            "company": "Miller Law Group",
            "email": "david@millerlaw.com",
            "description": "Looking for custom client onboarding portal and website redesign.",
            "source": "MANUAL",
            "analyze_with_ai": True,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    lead = resp.json()
    assert lead["name"] == "David Miller"
    assert lead["company"] == "Miller Law Group"
    assert lead["detected_need"] is not None
    assert 0 <= lead["intent_score"] <= 100

    # Duplicate manual import should return 400 Bad Request
    dup_resp = await async_client.post(
        "/api/v1/discovery/import",
        json={
            "name": "David Miller",
            "company": "Miller Law Group",
            "email": "david@millerlaw.com",
            "description": "Duplicate attempt",
        },
        headers=headers,
    )
    assert dup_resp.status_code == 400
    assert "Duplicate" in dup_resp.json()["detail"]


@pytest.mark.asyncio
async def test_authenticated_csv_upload_endpoint(async_client: AsyncClient):
    """Test CSV file upload endpoint."""
    token, headers = await create_user_and_headers(async_client, "csv_endpoint_tester@example.com")

    csv_file_bytes = (
        b"name,company,email,description\n"
        b"TechCorp Inc,TechCorp,contact@techcorp.io,Need automated bot for Discord and Slack support\n"
        b"DesignStudio,DesignStudio,hello@designstudio.art,Need brand redesign and landing page\n"
    )

    files = {"file": ("test_leads.csv", io.BytesIO(csv_file_bytes), "text/csv")}
    resp = await async_client.post(
        "/api/v1/discovery/import/csv",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["total_rows"] == 2
    assert result["imported_count"] == 2
    assert result["rejected_count"] == 0


@pytest.mark.asyncio
async def test_discovery_user_isolation(async_client: AsyncClient):
    """Verify User A cannot access or mutate User B's discovery sources."""
    _, headers_a = await create_user_and_headers(async_client, "user_a_discovery@example.com")
    _, headers_b = await create_user_and_headers(async_client, "user_b_discovery@example.com")

    # User B creates a discovery source
    b_source_resp = await async_client.post(
        "/api/v1/discovery/sources",
        json={"name": "User B Secret Source", "source_type": "MOCK"},
        headers=headers_b,
    )
    b_source_id = b_source_resp.json()["id"]

    # User A tries to view User B's source -> 404 Not Found
    get_resp = await async_client.get(
        f"/api/v1/discovery/sources/{b_source_id}", headers=headers_a
    )
    assert get_resp.status_code == 404

    # User A tries to delete User B's source -> 404 Not Found
    del_resp = await async_client.delete(
        f"/api/v1/discovery/sources/{b_source_id}", headers=headers_a
    )
    assert del_resp.status_code == 404
