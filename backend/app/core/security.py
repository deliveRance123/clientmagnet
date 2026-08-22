import hashlib
import hmac
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple, Union

import jwt
import bcrypt

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ph = PasswordHasher(
        time_cost=1,
        memory_cost=19456,  # 19 MB (RFC 9106 recommended)
        parallelism=1,
        hash_len=32,
    )
except ImportError:
    _ph = None

from app.core.config import settings


def hash_password(password: str) -> str:
    """Securely hash a password using modern Argon2id or Bcrypt fallback."""
    if _ph is not None:
        return _ph.hash(password)
    # Bcrypt fallback
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash (supporting Argon2id & bcrypt)."""
    if not hashed_password or not plain_password:
        return False
    try:
        if hashed_password.startswith("$argon2"):
            if _ph is not None:
                return _ph.verify(hashed_password, plain_password)
            return False
        elif hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            # Support standard bcrypt hashes
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        else:
            return False
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    return True, ""


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    if custom_claims:
        payload.update(custom_claims)

    encoded_jwt = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str, datetime]:
    """
    Generate a signed JWT refresh token.
    Returns: (raw_jwt_token, token_hash_for_db, expires_at_datetime)
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Generate unique entropy for refresh token
    random_entropy = hashlib.sha256(f"{subject}-{now.timestamp()}-{time.time_ns()}".encode()).hexdigest()[:16]

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "jti": random_entropy,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }

    raw_token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    token_db_hash = hash_token(raw_token)
    return raw_token, token_db_hash, expire


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT signature and expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None


class LoginRateLimiter:
    """In-memory sliding window rate limiter to protect against repeated failed logins."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # Mapping: identifier -> list of failure timestamps
        self._failures: Dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, identifier: str, current_time: float):
        cutoff = current_time - self.window_seconds
        self._failures[identifier] = [
            ts for ts in self._failures[identifier] if ts > cutoff
        ]
        if not self._failures[identifier]:
            self._failures.pop(identifier, None)

    def is_rate_limited(self, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is rate limited. Returns (is_limited, retry_after_seconds)."""
        now = time.time()
        self._cleanup(identifier, now)
        attempts = self._failures.get(identifier, [])
        if len(attempts) >= self.max_attempts:
            oldest_relevant = attempts[0]
            retry_after = int(self.window_seconds - (now - oldest_relevant)) + 1
            return True, max(retry_after, 1)
        return False, 0

    def record_failure(self, identifier: str):
        """Record a failed login attempt."""
        now = time.time()
        self._failures[identifier].append(now)
        self._cleanup(identifier, now)

    def reset(self, identifier: str):
        """Reset failed attempts upon successful login."""
        self._failures.pop(identifier, None)


login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
)
