import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoints(async_client: AsyncClient):
    """Test public health check endpoint for production load balancers."""
    res_root = await async_client.get("/health")
    assert res_root.status_code == 200
    root_data = res_root.json()
    assert "status" in root_data
    assert "database" in root_data

    res_v1 = await async_client.get("/api/v1/health")
    assert res_v1.status_code == 200
    v1_data = res_v1.json()
    assert "status" in v1_data


@pytest.mark.asyncio
async def test_unauthorized_access_protection(async_client: AsyncClient):
    """Verify protected endpoints reject requests lacking authentication."""
    res = await async_client.get("/api/v1/crm/dashboard")
    assert res.status_code == 401

    res_clients = await async_client.get("/api/v1/clients/")
    assert res_clients.status_code == 401
