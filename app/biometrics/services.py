from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from statistics import fmean
from typing import Any, cast

from fastapi import HTTPException, status
from sqlalchemy import and_, exists, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.biometrics.dtos.AggregationsDTOs import GraphResponseDTO
from app.biometrics.dtos.MetricsDTOs import BoolMetricType
from app.biometrics.models import HeartRate
from app.biometrics.types import NoopData
from app.core.dependencies import AsyncSessionDep
from app.core.dtos import PermissionDeniedReason
from app.core.exceptions import PermissionException
from app.core.sql_loader import load_sql
from app.team.models import TeamMembership, TeamMembershipStatusType, TeamRoleType
from app.team.services import get_effective_membership_dsp
from app.user.models import User

SQL_DIRECTORY = Path(__file__).parent / "sql"
# asyncpg limits one statement to 32,767 bind parameters. Four thousand rows
# stays below that limit for the widest biometric model.
UPLOAD_BATCH_SIZE = 4_000
MAX_GRAPH_POINTS = 1_000


async def bulk_upload_noop_data(
    db: AsyncSessionDep, user_id: int, noop_data: NoopData
) -> tuple[int, int]:
    """Bulk uploads noop data model to the database"""

    models = noop_data.to_models(user_id)
    inserted = 0
    duplicates = 0

    for model_rows in (
        models.heart_rate,
        models.rr_interval,
        models.gravity,
        models.optical_raw,
        models.skin_temperature_raw,
        models.respiration_raw,
    ):
        if not model_rows:
            continue

        model = type(model_rows[0])
        for batch_start in range(0, len(model_rows), UPLOAD_BATCH_SIZE):
            batch = model_rows[batch_start : batch_start + UPLOAD_BATCH_SIZE]
            values = [
                {
                    key: value
                    for key, value in row.__dict__.items()
                    if not key.startswith("_")
                }
                for row in batch
            ]
            statement = (
                insert(model)
                .values(values)
                .on_conflict_do_nothing(index_elements=["user_id", "timestamp"])
            )
            result = cast(CursorResult[Any], await db.execute(statement))
            rowcount = result.rowcount or 0
            inserted += rowcount
            duplicates += len(batch) - rowcount

    return inserted, duplicates


async def _can_access_metric(
    db: AsyncSession,
    requestor: User | None,
    target_user_id: int,
    metric: BoolMetricType,
) -> None:
    """Check if requestor user can access target user"""

    check_policy = f"{metric}_shared"

    # Calls from trusted internal tools can skip request authorization explicitly.
    if requestor is None or requestor.is_admin:
        return

    if requestor.id == target_user_id:
        query = select(TeamMembership).where(
            TeamMembership.user_id == requestor.id,
            TeamMembership.role == TeamRoleType.ATHLETE,
            TeamMembership.status == TeamMembershipStatusType.APPROVE,
        )
        rows = await db.execute(query)
        memberships = list(rows.scalars())

        # Only approved athlete memberships require an accepted sharing policy.
        need_dsps = [m for m in memberships if m.dsp is None]

        if need_dsps:
            raise PermissionException(
                reason=PermissionDeniedReason.NULL_POLICY,
                detail=(
                    f"There are still {len(need_dsps)} data sharing "
                    f"{'policy' if len(need_dsps) == 1 else 'policies'} "
                    "that need confirmation"
                ),
            )

        # Get list of memberships with dsps and dsrs set
        invalid_memberships: list[str] = []
        for membership in memberships:
            effective_mem = get_effective_membership_dsp(membership)
            if len(effective_mem.invalid_fields) > 0:
                invalid_memberships.append(str(membership.id))

        if invalid_memberships:
            raise PermissionException(
                reason=PermissionDeniedReason.INVALID_POLICY,
                detail=(
                    f"The policies for memberships [{','.join(invalid_memberships)}] need to be reviewed"
                ),
            )

        return

    coach_membership = aliased(TeamMembership)
    query = select(TeamMembership).where(
        TeamMembership.user_id == target_user_id,
        TeamMembership.role == TeamRoleType.ATHLETE,
        TeamMembership.status == TeamMembershipStatusType.APPROVE,
        exists(
            select(coach_membership.id).where(
                coach_membership.team_id == TeamMembership.team_id,
                coach_membership.user_id == requestor.id,
                coach_membership.role == TeamRoleType.COACH,
                coach_membership.status == TeamMembershipStatusType.APPROVE,
            )
        ),
    )
    rows = await db.execute(query)
    matched_memberships = list(rows.scalars())

    for membership in matched_memberships:
        if membership.dsp is None:
            continue

        effective_policy = get_effective_membership_dsp(membership)
        if check_policy in effective_policy.invalid_fields:
            continue
        if getattr(effective_policy, check_policy, False) is True:
            return

    raise PermissionException(
        reason=PermissionDeniedReason.POLICY_RESTRICTION,
        detail=(
            f"No access policy allows user with id '{requestor.id}' "
            f"to access {metric} of user with id '{target_user_id}'"
        ),
    )


async def calculate_hrv(
    db: AsyncSessionDep, requestor: User | None, target_user: User, end_time: datetime
) -> tuple[float | None, datetime, datetime]:
    """
    Computes and returns hrv value for a user from an end_time to six months in the past.

    Returns:
        tuple[float, datetime, datetime]: (hrv_value, start_time, end_time)
    """

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="hrv")

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "calculate_hrv.sql"))
    result = await db.execute(query, {"user_id": target_user.id, "end_time": end_time})

    return (result.scalar_one(), end_time - timedelta(days=61), end_time)


async def bulk_bpm_data(
    db: AsyncSessionDep,
    requestor: User | None,
    target_user: User,
    start_time: datetime,
    end_time: datetime,
) -> GraphResponseDTO:
    """Returns a user's bpm data from a start to and end time"""

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="bpm")

    # Then compute the metric
    stmt = (
        select(HeartRate.timestamp, HeartRate.bpm)
        .where(
            and_(
                HeartRate.user_id == target_user.id,
                HeartRate.timestamp >= start_time,
                HeartRate.timestamp <= end_time,
            )
        )
        .order_by(HeartRate.timestamp.asc())
    )

    result = await db.execute(stmt)
    rows = result.all()  # list[tuple[timestamp, bpm]]

    if len(rows) > MAX_GRAPH_POINTS:
        bucket_size = ceil(len(rows) / MAX_GRAPH_POINTS)
        rows = [
            (bucket[len(bucket) // 2][0], fmean(row[1] for row in bucket))
            for index in range(0, len(rows), bucket_size)
            if (bucket := rows[index : index + bucket_size])
        ]

    x = [row[0] for row in rows]
    y = [row[1] for row in rows]

    return GraphResponseDTO(start=start_time, end=end_time, x=x, y=y)


async def rhr_over_interval(
    db: AsyncSessionDep,
    requestor: User | None,
    target_user: User,
    start_time: datetime,
    end_time: datetime,
) -> tuple[float | None, datetime, datetime]:
    """
    Computes and returns rhr value for a user from an end_time to some past start time (uses 10 minute buckets)

    Returns:
        tuple[float, datetime, datetime]: (rhr_value, start_time, end_time)
    """

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="rhr")

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "resting_heart_rate.sql"))
    result = await db.execute(
        query,
        {"user_id": target_user.id, "start_time": start_time, "end_time": end_time},
    )

    return (result.scalar_one(), start_time, end_time)


async def skin_temp_delta(
    db: AsyncSessionDep, requestor: User | None, target_user: User
) -> float:
    """Calculates skin temp delta for a user using today's median and the past 7 days values, not including today"""

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="skin_temp_delta")

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "skin_temperature_delta.sql"))
    result = await db.execute(query, {"user_id": target_user.id})

    return result.scalar_one()


async def respiratory_rate(
    db: AsyncSessionDep, requestor: User | None, target_user: User
) -> float | None:
    """
    Calculate respiratory rate from rr intervals

    Returns:
        float: beats/minute
    """
    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="respiratory_rate")

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "respiratory_rate.sql"))
    result = await db.execute(query, {"user_id": target_user.id})

    return result.scalar_one()


async def calculate_effort_strain(
    db: AsyncSessionDep, requestor: User | None, target_user: User
) -> float | None:
    """Calculates strain/effort for a user over the most recent 24 hours with data."""

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="effort")

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "effort_strain.sql"))
    result = await db.execute(query, {"user_id": target_user.id})

    return result.scalar_one()


async def calculate_calories(
    db: AsyncSessionDep, requestor: User | None, target_user: User
) -> float | None:
    """Calculate estimated calories for a user over their most recent day of HR data."""

    # Check if the current user can see the metric
    await _can_access_metric(db, requestor, target_user.id, metric="calories")

    if (
        target_user.height is None
        or target_user.weight is None
        or target_user.sex is None
        or target_user.age is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have all of height, weight, sex, and age to calculate calories.",
        )

    # Then compute the metric
    query = text(load_sql(SQL_DIRECTORY, "calories.sql"))
    result = await db.execute(query, {"user_id": target_user.id})

    return result.scalar_one()
