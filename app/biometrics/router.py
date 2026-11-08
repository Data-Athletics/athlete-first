from datetime import datetime
from typing import Annotated

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.auth.dependencies import CurrentUserDep, get_current_user
from app.biometrics.decoder import decode_noop_csv
from app.biometrics.dtos.AggregationsDTOs import (
    BiometricsUploadResponseDTO,
    CaloriesResponseDTO,
    EffortStrainResponseDTO,
    GraphResponseDTO,
    HRVResponseDTO,
    RespiratoryRateResponseDTO,
    RHRResponseDTO,
    SkinTempDeltaResponseDTO,
)
from app.biometrics.dtos.MetricsDTOs import MetricsFilterDTO
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
from app.user.dependencies import UserByIdDep

biometrics_router = APIRouter(dependencies=[Depends(get_current_user)])


@biometrics_router.post(
    "/{user_id}", response_model=BiometricsUploadResponseDTO, status_code=201
)
async def create_biometrics_route(
    db: AsyncSessionDep, user: UserByIdDep, file: UploadFile = File(...)
):
    """Create many biometrics rows from a csv upload"""

    if file.filename and not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file.",
        )

    noop_data = decode_noop_csv(file.file)

    try:
        inserted, duplicates = await bulk_upload_noop_data(db, user.id, noop_data)

        return BiometricsUploadResponseDTO(
            detail="Noop data uploaded",
            code=201,
            inserted=inserted,
            duplicates=duplicates,
        )
    except sqlalchemy.exc.NoReferencedTableError as e:
        if "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User id does not exist to upload data to.",
            )


@biometrics_router.get("/{user_id}/hrv", response_model=HRVResponseDTO)
async def get_hrv_from_end_time(
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    user: UserByIdDep,
    end_time: Annotated[datetime, Query(default_factory=datetime.now)],
):
    """Get a user's HRV value over the previous two months."""

    hrv, start, end = await calculate_hrv(
        db, requestor=current_user, target_user=user, end_time=end_time
    )

    return HRVResponseDTO(hrv=hrv, start=start, end=end)


@biometrics_router.get("/{user_id}/rhr", response_model=RHRResponseDTO)
async def get_rhr_from_start_and_end_time(
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    user: UserByIdDep,
    filters: Annotated[MetricsFilterDTO, Query()],
):
    """Get a user's rhr value over an interval (10 minute bins)"""

    rhr, start, end = await rhr_over_interval(
        db,
        requestor=current_user,
        target_user=user,
        start_time=filters.start_time,
        end_time=filters.end_time,
    )

    return RHRResponseDTO(rhr=rhr, start=start, end=end)


@biometrics_router.get(
    "/{user_id}/skin-temp-delta", response_model=SkinTempDeltaResponseDTO
)
async def get_skin_temp_delta(
    db: AsyncSessionDep, current_user: CurrentUserDep, user: UserByIdDep
):
    """Get a user's skin temperature delta."""

    delta = await skin_temp_delta(db, requestor=current_user, target_user=user)

    return SkinTempDeltaResponseDTO(skin_temp_delta=delta)


@biometrics_router.get(
    "/{user_id}/respiratory-rate", response_model=RespiratoryRateResponseDTO
)
async def get_respiratory_rate(
    db: AsyncSessionDep, current_user: CurrentUserDep, user: UserByIdDep
) -> RespiratoryRateResponseDTO:
    """Get a user's respiratory rate value."""

    rate = await respiratory_rate(db, requestor=current_user, target_user=user)

    return RespiratoryRateResponseDTO(respiratory_rate=rate)


@biometrics_router.get("/{user_id}/effort", response_model=EffortStrainResponseDTO)
async def get_effort_strain(
    db: AsyncSessionDep, current_user: CurrentUserDep, user: UserByIdDep
) -> EffortStrainResponseDTO:
    """Get a user's effort/strain value."""

    effort = await calculate_effort_strain(db, requestor=current_user, target_user=user)

    return EffortStrainResponseDTO(effort=effort)


@biometrics_router.get("/{user_id}/calories", response_model=CaloriesResponseDTO)
async def get_calories(
    db: AsyncSessionDep, current_user: CurrentUserDep, user: UserByIdDep
) -> CaloriesResponseDTO:
    """Get a user's estimated calories."""

    calories = await calculate_calories(db, requestor=current_user, target_user=user)

    return CaloriesResponseDTO(calories=calories)


@biometrics_router.get("/{user_id}/bpm", response_model=GraphResponseDTO)
async def get_bpm_from_start_and_end_time(
    db: AsyncSessionDep,
    current_user: CurrentUserDep,
    user: UserByIdDep,
    filters: Annotated[MetricsFilterDTO, Query()],
):
    """Get a user's bpm data over an interval"""

    try:
        return await bulk_bpm_data(
            db,
            requestor=current_user,
            target_user=user,
            start_time=filters.start_time,
            end_time=filters.end_time,
        )
    except sqlalchemy.exc.NoReferencedTableError as e:
        if "user_id" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User id does not exist to upload data to.",
            )
