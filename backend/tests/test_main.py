from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test that the health endpoint is reachable and returns the expected schema."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "environment" in data
    assert "project" in data
    
    # Status can be OK (if DB running) or DEGRADED (if DB not running)
    assert data["status"] in ("OK", "DEGRADED")
    assert data["database"] in ("connected", "disconnected")
