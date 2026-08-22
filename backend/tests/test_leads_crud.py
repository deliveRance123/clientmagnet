import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_leads_full_crud_and_validation(async_client: AsyncClient):
    # 1. Register test user
    email = "leads_tester@example.com"
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Leads Tester"},
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a service for matching
    svc_resp = await async_client.post(
        "/api/v1/services/",
        json={"name": "Full Stack Web Development", "pricing": "$5,000"},
        headers=headers,
    )
    svc_id = svc_resp.json()["id"]

    # 3. Create a lead with all fields
    lead_payload = {
        "name": "Sarah Connor",
        "company": "Cyberdyne Systems",
        "email": "sarah@cyberdyne.com",
        "phone": "+1 555 0199",
        "website": "https://cyberdyne.com",
        "platform": "LinkedIn",
        "profile_url": "https://linkedin.com/in/sarahconnor",
        "location": "Los Angeles, CA",
        "source": "LINKEDIN",
        "source_url": "https://linkedin.com/posts/cyberdyne_update",
        "description": "Looking for modern web redesign",
        "detected_need": "Complete UI overhaul and client portal",
        "matched_service_id": svc_id,
        "intent_score": 85.5,
        "status": "NEW",
        "notes": "Met at tech meetup, very interested in Q3 kickoff",
    }
    create_resp = await async_client.post("/api/v1/leads/", json=lead_payload, headers=headers)
    assert create_resp.status_code == 201
    lead = create_resp.json()
    lead_id = lead["id"]
    assert lead["name"] == "Sarah Connor"
    assert lead["company"] == "Cyberdyne Systems"
    assert lead["matched_service_id"] == svc_id
    assert lead["matched_service"]["name"] == "Full Stack Web Development"
    assert lead["intent_score"] == 85.5
    assert lead["status"] == "NEW"
    assert lead["source"] == "LINKEDIN"

    # 4. Intent Score Validation (0 to 100 valid, < 0 or > 100 invalid)
    bad_score_low = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Bad Score Lead", "intent_score": -5.0},
        headers=headers,
    )
    assert bad_score_low.status_code == 422

    bad_score_high = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Bad Score Lead", "intent_score": 105.0},
        headers=headers,
    )
    assert bad_score_high.status_code == 422

    # 5. Lead Status Validation (invalid status rejected)
    bad_status = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Bad Status Lead", "status": "INVALID_STATUS_VALUE"},
        headers=headers,
    )
    assert bad_status.status_code == 422

    # 6. Update Lead (PATCH status, score, notes)
    patch_resp = await async_client.patch(
        f"/api/v1/leads/{lead_id}",
        json={"status": "QUALIFIED", "intent_score": 95.0, "notes": "Sent discovery questionnaire"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated_lead = patch_resp.json()
    assert updated_lead["status"] == "QUALIFIED"
    assert updated_lead["intent_score"] == 95.0
    assert updated_lead["notes"] == "Sent discovery questionnaire"

    # 7. Get Lead by ID
    get_resp = await async_client.get(f"/api/v1/leads/{lead_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == lead_id

    # 8. Delete Lead
    del_resp = await async_client.delete(f"/api/v1/leads/{lead_id}", headers=headers)
    assert del_resp.status_code == 204
    assert (await async_client.get(f"/api/v1/leads/{lead_id}", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_leads_search_filter_sort_and_stats(async_client: AsyncClient):
    email = "leads_query@example.com"
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Query Tester"},
    )
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 leads
    l1 = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Alice Alpha", "company": "Alpha Corp", "status": "NEW", "source": "WEBSITE", "intent_score": 20.0},
        headers=headers,
    )
    l2 = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Bob Beta", "company": "Beta Tech", "status": "QUALIFIED", "source": "LINKEDIN", "intent_score": 80.0},
        headers=headers,
    )
    l3 = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Charlie Gamma", "company": "Gamma LLC", "status": "INTERESTED", "source": "X", "intent_score": 50.0},
        headers=headers,
    )
    assert l1.status_code == 201
    assert l2.status_code == 201
    assert l3.status_code == 201

    # 1. Search by name/company
    search_res = await async_client.get("/api/v1/leads/?search=Beta", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert search_res.json()[0]["name"] == "Bob Beta"

    # 2. Filter by status
    status_res = await async_client.get("/api/v1/leads/?status=QUALIFIED", headers=headers)
    assert status_res.status_code == 200
    assert len(status_res.json()) == 1
    assert status_res.json()[0]["status"] == "QUALIFIED"

    # 3. Filter by source
    source_res = await async_client.get("/api/v1/leads/?source=WEBSITE", headers=headers)
    assert source_res.status_code == 200
    assert len(source_res.json()) == 1
    assert source_res.json()[0]["name"] == "Alice Alpha"

    # 4. Sort by intent_score desc
    sort_score_desc = await async_client.get("/api/v1/leads/?sort_by=intent_score&sort_dir=desc", headers=headers)
    scores = [l["intent_score"] for l in sort_score_desc.json()]
    assert scores == [80.0, 50.0, 20.0]

    # 5. Sort by intent_score asc
    sort_score_asc = await async_client.get("/api/v1/leads/?sort_by=intent_score&sort_dir=asc", headers=headers)
    scores_asc = [l["intent_score"] for l in sort_score_asc.json()]
    assert scores_asc == [20.0, 50.0, 80.0]

    # 6. Dashboard Stats Summary
    stats_res = await async_client.get("/api/v1/leads/stats/summary", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_leads"] == 3
    assert stats["new_leads"] == 1
    assert stats["qualified_leads"] == 1
    assert stats["interested_leads"] == 1


@pytest.mark.asyncio
async def test_leads_foreign_service_matching_rejected(async_client: AsyncClient):
    # User A
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "u_a_match@example.com", "password": "Password123!", "full_name": "User A"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "u_b_match@example.com", "password": "Password123!", "full_name": "User B"},
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a service
    svc_a_res = await async_client.post(
        "/api/v1/services/",
        json={"name": "User A Exclusive Service"},
        headers=headers_a,
    )
    svc_a_id = svc_a_res.json()["id"]

    # User B attempts to link a lead to User A's service (must fail with 400)
    bad_match_res = await async_client.post(
        "/api/v1/leads/",
        json={"name": "User B Sneaky Lead", "matched_service_id": svc_a_id},
        headers=headers_b,
    )
    assert bad_match_res.status_code == 400

    # User B creates a lead without service, then attempts to PATCH it with User A's service (must fail with 400)
    good_lead_res = await async_client.post(
        "/api/v1/leads/",
        json={"name": "User B Regular Lead"},
        headers=headers_b,
    )
    lead_b_id = good_lead_res.json()["id"]

    bad_patch_res = await async_client.patch(
        f"/api/v1/leads/{lead_b_id}",
        json={"matched_service_id": svc_a_id},
        headers=headers_b,
    )
    assert bad_patch_res.status_code == 400
