from httpx import AsyncClient

from app.observability.dtos import HealthDTO
from app.observability.types import HealthStatus


async def test_health(client: AsyncClient):
    """Should return 200 ok"""

    response = await client.get("/observability/health")
    health = HealthDTO.model_validate(response.json())

    assert response.status_code == 200
    assert health.status == HealthStatus.HEALTHY.value
