import pytest
from httpx import AsyncClient

from app.biometrics.dtos.HRVResponseDTO import HRVResponseDTO
from app.core.dtos import SimpleResponseDTO
from tests.mock.biometrics.metrics import EXPECTED_HRV

MOCK_USER_ID = 10
BASE_METRICS_ENDPOINT = f"/biometrics/{MOCK_USER_ID}"


async def test_metrics_calculation(client: AsyncClient):
    """Check that metrics are calculated as expected"""
    with open("tests/fixtures/noop_mock.csv", "rb") as file:
        creation_response = await client.post(
            f"/biometrics/{MOCK_USER_ID}",
            files={"file": ("noop_mock.csv", file, "text/csv")},
        )

        SimpleResponseDTO.model_validate(creation_response.json())
        assert creation_response.status_code == 201

    hrv_response = await client.get(
        BASE_METRICS_ENDPOINT + "/hrv" + "?end_time=" + "2025-04-27T14:46:47.336Z"
    )
    print(hrv_response.json())
    hrv = HRVResponseDTO.model_validate(hrv_response.json())
    assert hrv.hrv == pytest.approx(EXPECTED_HRV)
