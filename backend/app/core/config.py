import json
from typing import Any, List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Client Magnet"
    ENVIRONMENT: str = "development"  # "development", "staging", "production", "test"

    # CORS origins
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        raise ValueError(v)

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:localpassword@localhost:5432/client_magnet"
    ENCRYPTION_KEY: str = "y5lX0NnN2n_D9D0R_iS7xR7P3q1u3U9z8D_H_8q9J4k="  # Default dev key


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_db_url(cls, v: str) -> str:
        """Ensure that the database URL uses an async driver."""
        if not v:
            return v
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Security & Authentication Settings
    JWT_SECRET_KEY: str = "dev-secret-jwt-key-client-magnet-must-change-in-prod-xyz9876543210"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_COOKIE_NAME: str = "cm_refresh_token"
    
    # Rate Limiting for Login Protection
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300  # 5 minutes

    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    AI_MAX_OUTPUT_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.7
    AI_REQUEST_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 3
    AI_RATE_LIMIT_PER_MINUTE: int = 30

    # Enable mock AI provider for testing / keyless runtime
    USE_MOCK_AI: bool = True

    # Social Media OAuth Settings
    META_CLIENT_ID: str = ""
    META_CLIENT_SECRET: str = ""

    X_CLIENT_ID: str = ""
    X_CLIENT_SECRET: str = ""

    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""

    SOCIAL_OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000/api/v1/social/callback"
    FRONTEND_SOCIAL_REDIRECT_URL: str = "http://localhost:3000/settings/social"
    USE_MOCK_SOCIAL_OAUTH: bool = True

    # Google OAuth / User Authentication Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_AUTH_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/email/callback"
    FRONTEND_EMAIL_REDIRECT_URL: str = "http://localhost:3000/email"
    FRONTEND_URL: str = "http://localhost:3000"
    USE_MOCK_EMAIL: bool = True
    USE_MOCK_GOOGLE_AUTH: bool = True

    # WhatsApp Business Cloud API Settings
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v19.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "client_magnet_whatsapp_verify_token"
    WHATSAPP_APP_SECRET: str = ""
    USE_MOCK_WHATSAPP: bool = True


settings = Settings()
