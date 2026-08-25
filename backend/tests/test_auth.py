import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import login_rate_limiter
from app.models.token import RefreshToken
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiter state before each test."""
    login_rate_limiter._failures.clear()
    yield
    login_rate_limiter._failures.clear()


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration and verify response structure."""
    payload = {
        "email": "sarah.connor@example.com",
        "password": "Password123!",
        "full_name": "Sarah Connor",
        "company_name": "Cyberdyne Defense",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Verify tokens returned
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0

    # Verify user profile data
    user = data["user"]
    assert user["email"] == "sarah.connor@example.com"
    assert user["full_name"] == "Sarah Connor"
    assert user["company_name"] == "Cyberdyne Defense"
    assert user["is_active"] is True
    assert "id" in user
    # Ensure sensitive fields are NEVER returned in response
    assert "password" not in user
    assert "hashed_password" not in user

    # Verify user in database
    db_user_res = await db_session.execute(
        select(User).where(User.email == "sarah.connor@example.com")
    )
    db_user = db_user_res.scalar_one_or_none()
    assert db_user is not None
    assert db_user.hashed_password.startswith("$argon2")


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Test that duplicate email registration is rejected with 400."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "User One",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email (even with different casing)
    payload2 = {
        "email": "DUPLICATE@example.com",
        "password": "Password123!",
        "full_name": "User Two",
    }
    res2 = await async_client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_passwords(async_client: AsyncClient):
    """Test validation errors for weak or invalid passwords."""
    # Too short (< 8 chars)
    res_short = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "Pass1"},
    )
    assert res_short.status_code in (400, 422)

    # Missing uppercase
    res_no_upper = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "noupper@example.com", "password": "password123"},
    )
    assert res_no_upper.status_code in (400, 422)

    # Missing number
    res_no_num = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "nonum@example.com", "password": "PasswordNoNum"},
    )
    assert res_no_num.status_code in (400, 422)


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test valid user login flow."""
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login.test@example.com",
            "password": "SecurePassword1!",
            "full_name": "Login User",
        },
    )

    # Login
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "login.test@example.com", "password": "SecurePassword1!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login.test@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials_unified_error(async_client: AsyncClient):
    """Test that login failures do not leak whether an email exists."""
    # 1. Non-existent email
    res1 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password123!"},
    )
    assert res1.status_code == 401
    assert res1.json()["detail"] == "Invalid email or password."

    # 2. Existing user with incorrect password
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "realuser@example.com", "password": "CorrectPassword1!"},
    )
    res2 = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "realuser@example.com", "password": "WrongPassword1!"},
    )
    assert res2.status_code == 401
    # Error message must be identical to avoid account enumeration
    assert res2.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_rate_limiting(async_client: AsyncClient):
    """Test brute force protection after repeated failed logins."""
    target_email = "bruteforce@example.com"

    for i in range(5):
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": f"WrongAttempt{i}!"},
        )
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter
    res_blocked = await async_client.post(
        "/api/v1/auth/login",
        json={"email": target_email, "password": "WrongAttempt6!"},
    )
    assert res_blocked.status_code == 429
    assert "Too many failed login attempts" in res_blocked.json()["detail"]
    assert "Retry-After" in res_blocked.headers


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient):
    """Test /api/v1/auth/me with valid Bearer token."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "me.test@example.com",
            "password": "Password123!",
            "full_name": "Me Tester",
            "company_name": "Test Co",
        },
    )
    token = reg_res.json()["access_token"]

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "me.test@example.com"
    assert user["full_name"] == "Me Tester"
    assert user["company_name"] == "Test Co"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    """Test /api/v1/auth/me rejects requests without token."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(async_client: AsyncClient):
    """Test /api/v1/auth/me rejects invalid or tampered tokens."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.signature"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_me_profile(async_client: AsyncClient):
    """Test PATCH /api/v1/auth/me updates basic account details."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "update.me@example.com",
            "password": "Password123!",
            "full_name": "Original Name",
        },
    )
    token = reg_res.json()["access_token"]

    update_res = await async_client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name",
            "company_name": "New Ventures LLC",
        },
    )
    assert update_res.status_code == 200
    updated_user = update_res.json()
    assert updated_user["full_name"] == "Updated Name"
    assert updated_user["company_name"] == "New Ventures LLC"


@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient):
    """Test token refresh endpoint rotation."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh.flow@example.com",
            "password": "Password123!",
        },
    )
    refresh_token = reg_res.json()["refresh_token"]

    # Request new access token using refresh token
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # Use new access token to access protected endpoint
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_data['access_token']}"},
    )
    assert me_res.status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_token(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Test that logging out revokes the refresh token."""
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout.test@example.com",
            "password": "Password123!",
        },
    )
    refresh_token = reg_res.json()["refresh_token"]

    # Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Attempting to refresh with the revoked token should fail
    failed_refresh = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert failed_refresh.status_code == 401


@pytest.mark.asyncio
async def test_google_auth_url(async_client: AsyncClient):
    """Test getting Google OAuth authorization URL."""
    response = await async_client.get("/api/v1/auth/google/url")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "state" in data
    assert len(data["authorization_url"]) > 0


@pytest.mark.asyncio
async def test_google_auth_new_user_registration(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Test automatic new user registration via Google OAuth."""
    payload = {
        "code": "mock_google_auth_code_999",
        "email": "google.newuser@example.com",
        "name": "New Google User",
    }
    response = await async_client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "google.newuser@example.com"
    assert data["user"]["full_name"] == "New Google User"
    assert data["user"]["is_active"] is True
    assert data["user"]["is_verified"] is True

    # Verify user saved in DB
    db_res = await db_session.execute(
        select(User).where(User.email == "google.newuser@example.com")
    )
    db_user = db_res.scalar_one_or_none()
    assert db_user is not None
    assert db_user.is_verified is True


@pytest.mark.asyncio
async def test_google_auth_existing_user_login(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Test signing in an existing user with Google OAuth."""
    # Create existing user
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing.google@example.com",
            "password": "Password123!",
            "full_name": "Original Name",
        },
    )

    # Sign in with Google with same email
    payload = {
        "code": "mock_google_auth_code_888",
        "email": "existing.google@example.com",
        "name": "Original Name",
    }
    response = await async_client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "existing.google@example.com"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_send_and_verify_otp(async_client: AsyncClient):
    """Test OTP code dispatch and verification."""
    # 1. Send OTP
    send_res = await async_client.post(
        "/api/v1/auth/otp/send",
        json={"email": "otp.tester@example.com", "purpose": "registration"},
    )
    assert send_res.status_code == 200
    assert send_res.json()["success"] is True

    # 2. Verify with invalid OTP code
    bad_verify = await async_client.post(
        "/api/v1/auth/otp/verify",
        json={"email": "otp.tester@example.com", "otp": "000000", "purpose": "registration"},
    )
    assert bad_verify.status_code == 400

    # 3. Verify with valid dev OTP code (999999)
    good_verify = await async_client.post(
        "/api/v1/auth/otp/verify",
        json={"email": "otp.tester@example.com", "otp": "999999", "purpose": "registration"},
    )
    assert good_verify.status_code == 200
    assert good_verify.json()["success"] is True


@pytest.mark.asyncio
async def test_login_with_otp_flow(async_client: AsyncClient):
    """Test passwordless authentication via OTP."""
    email = "otp.login.user@example.com"
    await async_client.post(
        "/api/v1/auth/otp/send",
        json={"email": email, "purpose": "login"},
    )

    login_res = await async_client.post(
        "/api/v1/auth/otp/login",
        json={"email": email, "otp": "999999"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["is_verified"] is True


@pytest.mark.asyncio
async def test_forgot_and_reset_password_otp(async_client: AsyncClient):
    """Test forgot password and reset password using OTP."""
    email = "reset.user@example.com"
    # Create user first
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OriginalPassword123!"},
    )

    # Request forgot password OTP
    forgot_res = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    assert forgot_res.status_code == 200

    # Reset password with OTP
    reset_res = await async_client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": email,
            "otp": "999999",
            "new_password": "NewSecretPassword123!",
        },
    )
    assert reset_res.status_code == 200

    # Login with new password
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "NewSecretPassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
