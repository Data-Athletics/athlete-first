from datetime import datetime

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_user
from app.biometrics.decoder import decode_noop_csv
from app.biometrics.dtos.AggregationsDTOs import (
    CaloriesResponseDTO,
    EffortStrainResponseDTO,
    GraphResponseDTO,
    HRVResponseDTO,
    RespiratoryRateResponseDTO,
    RHRResponseDTO,
    SkinTempDeltaResponseDTO,
)
from app.biometrics.services import (
    bulk_bpm_data,
    bulk_upload_noop_data,
    calculate_calories,
    calculate_effort_strain,
    calculate_hrv,
    respiratory_rate,
    rhr_over_interval,
    skin_temp_delta,
)
from app.core.dependencies import AsyncSessionDep
from app.core.dtos import SimpleResponseDTO
from app.user.dependencies import UserByIdDep

biometrics_router = APIRouter(dependencies=[Depends(get_current_user)])


@biometrics_router.post("/{user_id}", response_model=SimpleResponseDTO, status_code=201)
async def create_biometrics_route(
    db: AsyncSessionDep, user_id: int, file: UploadFile = File(...)
):
    """Create many biometrics rows from a csv upload"""

    if file.filename and not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file.",
        )

    noop_data = decode_noop_csv(file.file)

    try:
        await bulk_upload_noop_data(db, user_id, noop_data)
    except sqlalchemy.exc.NoReferencedTableError as e:
        if "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User id does not exist to upload data to.",
            )

    return SimpleResponseDTO(detail="Noop data uploaded", code=201)


@biometrics_router.get("/{user_id}/hrv", response_model=HRVResponseDTO)
async def get_hrv_from_end_time(db: AsyncSessionDep, user_id: int, end_time: datetime):
    """Get a user's hrv value from the end_time to some past start time (current default 3 weeks)"""

    hrv, start, end = await calculate_hrv(db, user_id, end_time)

    return HRVResponseDTO(hrv=hrv, start=start, end=end)


@biometrics_router.get("/{user_id}/rhr", response_model=RHRResponseDTO)
async def get_rhr_from_start_and_end_time(
    db: AsyncSessionDep, user_id: int, start_time: datetime, end_time: datetime
):
    """Get a user's rhr value over an interval (10 minute bins)"""

    rhr, start, end = await rhr_over_interval(db, user_id, start_time, end_time)

    return RHRResponseDTO(rhr=rhr, start=start, end=end)


@biometrics_router.get(
    "/{user_id}/skin-temp-delta", response_model=SkinTempDeltaResponseDTO
)
async def get_skin_temp_delta(db: AsyncSessionDep, user_id: int):
    """Get a user's skin temperature delta."""

    delta = await skin_temp_delta(db, user_id)

    return SkinTempDeltaResponseDTO(skin_temp_delta=delta)


@biometrics_router.get(
    "/{user_id}/respiratory-rate", response_model=RespiratoryRateResponseDTO
)
async def get_respiratory_rate(
    user_id: int, db: AsyncSessionDep
) -> RespiratoryRateResponseDTO:
    """Get a user's respiratory rate value."""

    rate = await respiratory_rate(db, user_id)

    return RespiratoryRateResponseDTO(respiratory_rate=rate)


@biometrics_router.get("/{user_id}/effort", response_model=EffortStrainResponseDTO)
async def get_effort_strain(
    user_id: int, db: AsyncSessionDep
) -> EffortStrainResponseDTO:
    """Get a user's effort/strain value."""

    effort = await calculate_effort_strain(db, user_id)

    return EffortStrainResponseDTO(effort=effort)


@biometrics_router.get("/{user_id}/calories", response_model=CaloriesResponseDTO)
async def get_calories(
    user_id: int, user: UserByIdDep, db: AsyncSessionDep
) -> CaloriesResponseDTO:
    """Get a user's estimated calories."""

    if (
        user.height is None
        or user.weight is None
        or user.sex is None
        or user.age is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have all of height, weight, sex, and age to calculate calories.",
        )

    calories = await calculate_calories(db, user_id)

    return CaloriesResponseDTO(calories=calories)


@biometrics_router.get("/{user_id}/bpm", response_model=GraphResponseDTO)
async def get_bpm_from_start_and_end_time(
    db: AsyncSessionDep, user_id: int, start_time: datetime, end_time: datetime
):
    """Get a user's bpm data over an interval"""

    if start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data start time must be less than end time.",
        )

    try:
        return await bulk_bpm_data(db, user_id, start_time, end_time)
    except sqlalchemy.exc.NoReferencedTableError as e:
        if "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User id does not exist to upload data to.",
            )
