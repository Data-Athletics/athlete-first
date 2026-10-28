from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from statistics import fmean
from typing import Any, cast

from sqlalchemy import and_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult

from app.biometrics.dtos.AggregationsDTOs import GraphResponseDTO
from app.biometrics.models import HeartRate
from app.biometrics.types import NoopData
from app.core.dependencies import AsyncSessionDep
from app.core.sql_loader import load_sql

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


async def calculate_hrv(
    db: AsyncSessionDep, user_id: int, end_time: datetime
) -> tuple[float | None, datetime, datetime]:
    """
    Computes and returns hrv value for a user from an end_time to six months in the past.

    Returns:
        tuple[float, datetime, datetime]: (hrv_value, start_time, end_time)
    """

    query = text(load_sql(SQL_DIRECTORY, "calculate_hrv.sql"))

    result = await db.execute(query, {"user_id": user_id, "end_time": end_time})

    return (result.scalar_one(), end_time - timedelta(days=61), end_time)


async def bulk_bpm_data(
    db: AsyncSessionDep, user_id: int, start_time: datetime, end_time: datetime
) -> GraphResponseDTO:
    """Returns a user's bpm data from a start to and end time"""

    stmt = (
        select(HeartRate.timestamp, HeartRate.bpm)
        .where(
            and_(
                HeartRate.user_id == user_id,
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
    db: AsyncSessionDep, user_id: int, start_time: datetime, end_time: datetime
) -> tuple[float | None, datetime, datetime]:
    """
    Computes and returns rhr value for a user from an end_time to some past start time (uses 10 minute buckets)

    Returns:
        tuple[float, datetime, datetime]: (rhr_value, start_time, end_time)
    """

    query = text(load_sql(SQL_DIRECTORY, "resting_heart_rate.sql"))

    result = await db.execute(
        query, {"user_id": user_id, "start_time": start_time, "end_time": end_time}
    )

    return (result.scalar_one(), start_time, end_time)


async def skin_temp_delta(db: AsyncSessionDep, user_id: int) -> float:
    """Calculates skin temp delta for a user using today's median and the past 7 days values, not including today"""

    query = text(load_sql(SQL_DIRECTORY, "skin_temperature_delta.sql"))

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def respiratory_rate(db: AsyncSessionDep, user_id: int) -> float | None:
    """
    Calculate respiratory rate from rr intervals

    Returns:
        float: beats/minute
    """

    query = text(load_sql(SQL_DIRECTORY, "respiratory_rate.sql"))

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def calculate_effort_strain(db: AsyncSessionDep, user_id: int) -> float | None:
    """Calculates strain/effort for a user over the most recent 24 hours with data."""

    query = text(load_sql(SQL_DIRECTORY, "effort_strain.sql"))

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def calculate_calories(db: AsyncSessionDep, user_id: int) -> float | None:
    """Calculate estimated calories for a user over their most recent day of HR data."""

    query = text(load_sql(SQL_DIRECTORY, "calories.sql"))

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()
