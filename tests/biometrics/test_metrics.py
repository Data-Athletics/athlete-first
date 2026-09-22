import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.biometrics.dtos.HRVResponseDTO import HRVResponseDTO
from app.core.dtos import SimpleResponseDTO
from tests.mock.biometrics.metrics import EXPECTED_HRV
from tests.utils import create_test_user


async def test_metrics_calculation(client: AsyncClient, db: AsyncSession):
    """Check that metrics are calculated as expected"""

    test_user = await create_test_user(db)
    metrics_endpoint = f"/biometrics/{test_user.id}"

    with open("tests/fixtures/noop_mock.csv", "rb") as file:
        creation_response = await client.post(
            metrics_endpoint,
            files={"file": ("noop_mock.csv", file, "text/csv")},
        )

        SimpleResponseDTO.model_validate(creation_response.json())
        assert creation_response.status_code == 201

    hrv_response = await client.get(
        metrics_endpoint + "/hrv" + "?end_time=" + "2025-04-27T14:46:47.336Z"
    )
    print(hrv_response.json())
    hrv = HRVResponseDTO.model_validate(hrv_response.json())
    assert hrv.hrv == pytest.approx(EXPECTED_HRV)
