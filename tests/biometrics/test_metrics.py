import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.biometrics.dtos.AggregationsDTOs import (
    CaloriesResponseDTO,
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
from utilities.urls import create_biometrics_url


async def test_hrv_calculation(admin_client: AsyncClient, noop_user: User):
    """Check that HRV is calculated as expected"""

    response = await admin_client.get(
        create_biometrics_url(noop_user) + "/hrv",
        params={"end_time": "2025-04-27T14:46:47.336Z"},
    )

    assert response.status_code == 200

    hrv = HRVResponseDTO.model_validate(response.json())
    assert hrv.hrv == pytest.approx(EXPECTED_HRV)


async def test_rhr_calculation(admin_client: AsyncClient, noop_user: User):
    """Check that RHR is calculated as expected"""

    response = await admin_client.get(
        create_biometrics_url(noop_user) + "/rhr",
        params={
            "start_time": "2025-04-27T14:46:47.000Z",
            "end_time": "2025-04-27T14:46:47.336Z",
        },
    )

    assert response.status_code == 200

    rhr = RHRResponseDTO.model_validate(response.json())
    assert rhr.rhr == pytest.approx(EXPECTED_RHR)


async def test_skin_temp_delta_calculation(admin_client: AsyncClient, noop_user: User):
    """Check that skin temp delta is calculated as expected"""

    response = await admin_client.get(
        create_biometrics_url(noop_user) + "/skin-temp-delta"
    )

    assert response.status_code == 200

    skin_temp = SkinTempDeltaResponseDTO.model_validate(response.json())
    assert skin_temp.skin_temp_delta == pytest.approx(EXPECTED_SKIN_TEMP_DELTA)


async def test_bpm_list(admin_client: AsyncClient, noop_user: User):
    """Check that BPM values are returned as expected"""

    response = await admin_client.get(
        create_biometrics_url(noop_user) + "/bpm",
        params={
            "start_time": "2025-04-27T14:46:47.000Z",
            "end_time": "2025-04-27T14:46:47.240Z",
        },
    )

    assert response.status_code == 200

    bpm = GraphResponseDTO.model_validate(response.json())
    assert bpm.y == [52, 52, 53, 53, 54, 54]


async def test_respiratory_rate_calculation(admin_client: AsyncClient, noop_user: User):
    """Check respiratory rate response with insufficient RR data"""

    response = await admin_client.get(
        create_biometrics_url(noop_user) + "/respiratory-rate"
    )

    assert response.status_code == 200

    respiratory_rate = RespiratoryRateResponseDTO.model_validate(response.json())
    assert respiratory_rate.respiratory_rate is None


async def test_effort_calculation(admin_client: AsyncClient, noop_user: User):
    """Check that effort is calculated as expected"""

    response = await admin_client.get(create_biometrics_url(noop_user) + "/effort")

    assert response.status_code == 200

    effort = EffortStrainResponseDTO.model_validate(response.json())
    assert effort.effort == pytest.approx(EXPECTED_EFFORT)


async def test_calorie_calculation(admin_client: AsyncClient, noop_user: User):
    """Check that calories are calculated successfully"""

    response = await admin_client.get(create_biometrics_url(noop_user) + "/calories")

    assert response.status_code == 200

    calories = CaloriesResponseDTO.model_validate(response.json())

    assert calories.calories is not None
    assert isinstance(calories.calories, float)


async def test_calorie_calculation_missing_user_data(
    admin_client: AsyncClient, noop_user: User, db: AsyncSession
):
    """Check that calories fail when required user data is missing"""

    noop_user.height = None
    await db.commit()
    await db.refresh(noop_user)

    response = await admin_client.get(create_biometrics_url(noop_user) + "/calories")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "User must have all of height, weight, sex, and age to calculate calories."
    )
