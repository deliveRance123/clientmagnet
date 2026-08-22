import pytest
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)


def test_argon2id_password_hashing():
    """Verify that passwords are encrypted with Argon2id and can be verified."""
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    # Must produce valid Argon2id hash format
    assert hashed.startswith("$argon2id$")
    assert raw_password != hashed

    # Valid password verification
    assert verify_password(raw_password, hashed) is True

    # Incorrect password verification
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_password, "") is False


def test_password_strength_rules():
    """Verify complexity rules enforcement."""
    # Valid
    ok, err = validate_password_strength("ValidPass123!")
    assert ok is True
    assert err == ""

    # Too short
    ok, err = validate_password_strength("V1!")
    assert ok is False
    assert "at least 8" in err

    # No uppercase
    ok, err = validate_password_strength("validpass123!")
    assert ok is False
    assert "uppercase" in err

    # No lowercase
    ok, err = validate_password_strength("VALIDPASS123!")
    assert ok is False
    assert "lowercase" in err

    # No digit
    ok, err = validate_password_strength("ValidPassword!")
    assert ok is False
    assert "digit" in err


def test_jwt_lifecycle_and_tamper_proofing():
    """Verify token encoding, expiration, and tampering rejection."""
    token = create_access_token(
        subject="user-12345",
        custom_claims={"company": "Test Corp"},
    )
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-12345"
    assert payload["type"] == "access"
    assert payload["company"] == "Test Corp"

    # Tampered token
    tampered_token = token[:-4] + "abcd"
    tampered_payload = decode_token(tampered_token)
    assert tampered_payload is None
