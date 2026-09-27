import pytest
from httpx import AsyncClient

from app.biometrics.dtos.AggregationsDTOs import (
    EffortStrainResponseDTO,
    GraphResponseDTO,
    HRVResponseDTO,
    RespiratoryRateResponseDTO,
    RHRResponseDTO,
    SkinTempDeltaResponseDTO,
)
from app.user.models import User
from tests.mock.biometrics.metrics import (
    EXPECTED_EFFORT,
    EXPECTED_HRV,
    EXPECTED_RHR,
    EXPECTED_SKIN_TEMP_DELTA,
)


async def test_hrv_calculation(client: AsyncClient, noop_user: User):
    """Check that HRV is calculated as expected"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/hrv",
        params={
            "end_time": "2025-04-27T14:46:47.336Z",
        },
    )

    hrv = HRVResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert hrv.hrv == pytest.approx(EXPECTED_HRV)


async def test_rhr_calculation(client: AsyncClient, noop_user: User):
    """Check that RHR is calculated as expected"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/rhr",
        params={
            "start_time": "2025-04-27T14:46:47.000Z",
            "end_time": "2025-04-27T14:46:47.336Z",
        },
    )

    rhr = RHRResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert rhr.rhr == pytest.approx(EXPECTED_RHR)


async def test_skin_temp_delta_calculation(
    client: AsyncClient,
    noop_user: User,
):
    """Check that skin temp delta is calculated as expected"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/skin-temp-delta",
    )

    skin_temp = SkinTempDeltaResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert skin_temp.skin_temp_delta == pytest.approx(EXPECTED_SKIN_TEMP_DELTA)


async def test_bpm_list(client: AsyncClient, noop_user: User):
    """Check that BPM values are returned as expected"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/bpm",
        params={
            "start_time": "2025-04-27T14:46:47.000Z",
            "end_time": "2025-04-27T14:46:47.240Z",
        },
    )

    bpm = GraphResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert bpm.y == [52, 52, 53, 53, 54, 54]


async def test_respiratory_rate_calculation(
    client: AsyncClient,
    noop_user: User,
):
    """Check respiratory rate response with insufficient RR data"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/respiratory-rate",
    )

    respiratory_rate = RespiratoryRateResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert respiratory_rate.respiratory_rate is None


async def test_effort_calculation(
    client: AsyncClient,
    noop_user: User,
):
    """Check that effort is calculated as expected"""

    metrics_endpoint = f"/biometrics/{noop_user.id}"

    response = await client.get(
        metrics_endpoint + "/effort",
    )

    effort = EffortStrainResponseDTO.model_validate(response.json())

    assert response.status_code == 200
    assert effort.effort == pytest.approx(EXPECTED_EFFORT)
