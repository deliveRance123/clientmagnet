from app.core.config import Settings


def test_db_url_asyncpg_enrichment():
    """Verify that traditional postgres URLs are transformed to use the asyncpg driver."""
    # Test standard postgresql prefix
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
    )
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"

    # Test old postgres prefix
    settings_old = Settings(
        DATABASE_URL="postgres://user:pass@localhost:5432/dbname"
    )
    assert settings_old.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"

    # Test that pre-formatted asyncpg strings are not modified
    settings_async = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
    )
    assert settings_async.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"
