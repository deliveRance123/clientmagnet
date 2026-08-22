from app.core.config import Settings


def test_settings_load():
    """Verify that settings validate and load correctly with default values."""
    settings = Settings(
        PROJECT_NAME="Test Magnet",
        ENVIRONMENT="test",
        BACKEND_CORS_ORIGINS=["http://testorigin.com"]
    )
    assert settings.PROJECT_NAME == "Test Magnet"
    assert settings.ENVIRONMENT == "test"
    assert settings.BACKEND_CORS_ORIGINS == ["http://testorigin.com"]


def test_cors_origins_validation():
    """Test that comma-separated strings are parsed into lists of origins."""
    settings = Settings(
        BACKEND_CORS_ORIGINS="http://localhost:3000, http://localhost:8080"
    )
    assert settings.BACKEND_CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8080"]


def test_cors_origins_json_validation():
    """Test that JSON lists are parsed correctly."""
    settings = Settings(
        BACKEND_CORS_ORIGINS='["http://localhost:3000", "http://localhost:8000"]'
    )
    assert settings.BACKEND_CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8000"]
