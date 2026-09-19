from datetime import datetime, timedelta

from sqlalchemy import text

from app.biometrics.types import NoopData
from app.core.dependencies import AsyncSessionDep


async def bulk_upload_noop_data(
    db: AsyncSessionDep, user_id: int, noop_data: NoopData
) -> None:
    """Bulk uploads noop data model to the database"""

    models = noop_data.to_models(user_id)
    db.add_all(models.to_list())
    await db.flush()


async def calculate_hrv(
    db: AsyncSessionDep, user_id: int, end_time: datetime
) -> tuple[float, datetime, datetime]:
    """
    Computes and returns hrv value for a user from an end_time to some past start time (currently defaults 3 weeks in the past)

    Returns:
        tuple[float, datetime, datetime]: (hrv_value, start_time, end_time)
    """

    query = text(
        """
        WITH user_rr AS (
            SELECT rr_ms, timestamp, id
            FROM af_rrinterval
            WHERE user_id = :user_id
                AND timestamp >= CAST(:end_time AS TIMESTAMPTZ) - INTERVAL '3 week'
                AND timestamp <= CAST(:end_time AS TIMESTAMPTZ)
        )

        SELECT SQRT(AVG(diff ^ 2)) AS hrv
        FROM (
            SELECT
                rr_ms - LAG(rr_ms, 1) OVER (ORDER BY timestamp) AS diff
            FROM user_rr
        ) AS diffs;
        """
    )

    result = await db.execute(query, {"user_id": user_id, "end_time": end_time})
    return (result.scalar_one(), end_time - timedelta(weeks=3), end_time)
