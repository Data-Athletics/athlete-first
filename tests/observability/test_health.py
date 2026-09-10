from httpx import AsyncClient

from app.constants import APP_PREFIX
from app.observability.dtos import HealthDTO
from app.observability.types import HealthStatus


async def test_health(client: AsyncClient):
    response = await client.get(APP_PREFIX + "/observability/health")
    health = HealthDTO.model_validate(response.json())

    assert response.status_code == 200
    assert health.status == HealthStatus.HEALTHY.value
