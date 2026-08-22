import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_account import SocialAccount
from app.models.user import User
from app.services.social import (
    MockSocialProvider,
    SocialAccountManager,
    generate_oauth_state,
    validate_oauth_state,
)


# Helper to register test user and retrieve auth headers
async def create_user_and_headers(async_client: AsyncClient, email: str = "social_tester@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Social OAuth Tester",
            "company_name": "Social Media Lab Inc",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. State Security & CSRF Validation Tests
# ---------------------------------------------------------------------------

def test_oauth_state_generation_and_validation():
    """Verify cryptographically signed state token roundtrip and platform checks."""
    user_id = "test-user-uuid-12345"
    platform = "X"

    # Valid state
    state = generate_oauth_state(user_id=user_id, platform=platform)
    recovered_user_id = validate_oauth_state(state=state, expected_platform="X")
    assert recovered_user_id == user_id

    # Platform mismatch fails
    with pytest.raises(ValueError, match="platform mismatch"):
        validate_oauth_state(state=state, expected_platform="FACEBOOK")

    # Corrupted / tampered state fails
    with pytest.raises(ValueError, match="Invalid or tampered"):
        validate_oauth_state(state=state + "tampered", expected_platform="X")


# ---------------------------------------------------------------------------
# 2. Provider Abstraction Tests (All 5 Platforms)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_provider_all_platforms():
    """Verify MockSocialProvider handles Facebook, Instagram, X, LinkedIn, and TikTok."""
    platforms = ["FACEBOOK", "INSTAGRAM", "X", "LINKEDIN", "TIKTOK"]

    for plat in platforms:
        provider = MockSocialProvider(plat)
        auth_url = provider.get_authorization_url(state="mock_state_abc", redirect_uri="http://localhost/cb")
        assert "state=mock_state_abc" in auth_url

        # Exchange code
        tokens = await provider.exchange_code("mock_code", "http://localhost/cb")
        assert tokens.access_token.startswith("mock_access_token_")
        assert len(tokens.scopes) > 0

        # Profile info
        profile = await provider.get_account_info(tokens.access_token)
        assert profile.account_identifier is not None
        assert profile.account_name is not None


# ---------------------------------------------------------------------------
# 3. Credential Encryption at Rest & Lifecycle Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_social_account_manager_flow(db_session: AsyncSession):
    """Verify OAuth callback saves encrypted credentials and disconnect clears them."""
    user = User(
        email="oauth_manager_test@example.com",
        hashed_password="hashed_dummy_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    manager = SocialAccountManager()

    # 1. Initiate Connect
    init_res = manager.initiate_connect(user_id=user.id, platform="LINKEDIN")
    assert init_res.platform == "LINKEDIN"
    assert init_res.state is not None

    # 2. Handle Callback
    account = await manager.handle_oauth_callback(
        db=db_session,
        platform="LINKEDIN",
        code="mock_code_123",
        state=init_res.state,
    )
    assert account.connection_status == "CONNECTED"
    assert account.platform == "LINKEDIN"
    assert account.user_id == user.id

    # Verify credentials property decrypts accurately
    creds = account.credentials
    assert creds is not None
    assert "access_token" in creds
    assert creds["access_token"].startswith("mock_access_token_")

    # Verify raw ciphertext in database is NOT plaintext
    assert "mock_access_token_" not in account.encrypted_credentials

    # 3. Verify Scope Compliance
    assert manager.verify_scope_compliance(account, "openid") is True
    assert manager.verify_scope_compliance(account, "unauthorized_admin_scope") is False

    # 4. Refresh Token
    refreshed = await manager.refresh_account_token(db_session, user, account.id)
    assert refreshed.connection_status == "CONNECTED"

    # 5. Disconnect
    disconnected = await manager.disconnect_account(db_session, user, account.id)
    assert disconnected.connection_status == "DISCONNECTED"
    assert disconnected.encrypted_credentials is None
    assert disconnected.credentials is None


# ---------------------------------------------------------------------------
# 4. Authenticated REST API Endpoints Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_social_api_endpoints(async_client: AsyncClient):
    """Test REST API endpoints for connect, callback, listing, refresh, and disconnect."""
    token, headers = await create_user_and_headers(async_client, "social_api_user@example.com")

    # 1. Initially 0 connected accounts
    list_resp = await async_client.get("/api/v1/social/accounts", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 0

    # 2. Initiate Connect for X (Twitter)
    init_resp = await async_client.get("/api/v1/social/connect/x", headers=headers)
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    assert init_data["platform"] == "X"
    state = init_data["state"]

    # 3. Complete Callback via Programmatic POST endpoint
    cb_resp = await async_client.post(
        "/api/v1/social/callback/x",
        json={"code": "valid_oauth_code_x", "state": state},
        headers=headers,
    )
    assert cb_resp.status_code == 200
    connected_account = cb_resp.json()
    account_id = connected_account["id"]
    assert connected_account["platform"] == "X"
    assert connected_account["connection_status"] == "CONNECTED"
    # Ensure sensitive access tokens are never returned
    assert "access_token" not in connected_account
    assert "encrypted_credentials" not in connected_account

    # 4. List accounts now shows 1 account
    list_resp2 = await async_client.get("/api/v1/social/accounts", headers=headers)
    assert list_resp2.status_code == 200
    assert len(list_resp2.json()) == 1

    # 5. Get Account Details
    get_resp = await async_client.get(
        f"/api/v1/social/accounts/{account_id}", headers=headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == account_id

    # 6. Refresh Token
    refresh_resp = await async_client.post(
        f"/api/v1/social/accounts/{account_id}/refresh", headers=headers
    )
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["connection_status"] == "CONNECTED"

    # 7. Disconnect Account
    disc_resp = await async_client.post(
        f"/api/v1/social/accounts/{account_id}/disconnect", headers=headers
    )
    assert disc_resp.status_code == 200
    assert disc_resp.json()["status"] == "success"

    # 8. List accounts now shows DISCONNECTED status
    list_resp3 = await async_client.get("/api/v1/social/accounts", headers=headers)
    assert list_resp3.json()[0]["connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_social_user_data_isolation(async_client: AsyncClient):
    """Verify User A cannot access or disconnect User B's social accounts."""
    _, headers_a = await create_user_and_headers(async_client, "user_a_social@example.com")
    _, headers_b = await create_user_and_headers(async_client, "user_b_social@example.com")

    # User B connects an account
    init_b = (await async_client.get("/api/v1/social/connect/instagram", headers=headers_b)).json()
    account_b = (
        await async_client.post(
            "/api/v1/social/callback/instagram",
            json={"code": "ig_code", "state": init_b["state"]},
            headers=headers_b,
        )
    ).json()
    account_b_id = account_b["id"]

    # User A tries to view User B's account -> 404
    get_resp = await async_client.get(
        f"/api/v1/social/accounts/{account_b_id}", headers=headers_a
    )
    assert get_resp.status_code == 404

    # User A tries to disconnect User B's account -> 404
    disc_resp = await async_client.post(
        f"/api/v1/social/accounts/{account_b_id}/disconnect", headers=headers_a
    )
    assert disc_resp.status_code == 404
