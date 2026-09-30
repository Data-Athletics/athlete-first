from datetime import datetime, timedelta

from sqlalchemy import and_, select, text

from app.biometrics.dtos.AggregationsDTOs import GraphResponseDTO
from app.biometrics.models import HeartRate
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
) -> tuple[float | None, datetime, datetime]:
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

    query = text(
        """
        SELECT
            percentile_cont(.1) WITHIN GROUP (ORDER BY median_bpm) AS rhr
        FROM (
            SELECT
                date_bin(
                    INTERVAL '10 minutes',
                    timestamp,
                    TIMESTAMPTZ '2000-01-01 00:00:00+00'
                ) as bins,
                percentile_cont(.5) WITHIN GROUP (ORDER BY bpm) AS median_bpm
            FROM af_heartrate
            WHERE timestamp <= CAST(:end_time AS TIMESTAMPTZ)
                AND timestamp >= CAST(:start_time AS TIMESTAMPTZ)
                AND bpm > 30
                AND bpm < 220
                AND user_id = :user_id
            GROUP BY bins
        ) AS medians;
        """
    )

    result = await db.execute(
        query, {"user_id": user_id, "start_time": start_time, "end_time": end_time}
    )

    return (result.scalar_one(), start_time, end_time)


async def skin_temp_delta(db: AsyncSessionDep, user_id: int) -> float:
    """Calculates skin temp delta for a user using today's median and the past 7 days values, not including today"""

    query = text(
        """
        WITH medians AS (
            SELECT
                date_bin(
                    INTERVAL '1 day',
                    timestamp,
                    TIMESTAMPTZ '2000-01-01 00:00:00+00'
                ) as bins,
                percentile_cont(.5) WITHIN GROUP (ORDER BY skin_temp_raw) AS median_str
            FROM af_skintemperatureraw
            WHERE user_id = :user_id
            GROUP BY bins
            ORDER BY bins DESC
            LIMIT 8
        ),
        today AS (
            SELECT median_str
            FROM medians
            LIMIT 1
        ),
        past_seven_result AS (
            SELECT
                percentile_cont(.5) WITHIN GROUP (ORDER BY median_str) AS median_str
            FROM (
                SELECT *
                FROM medians
                OFFSET 1
            ) week_data
        )
        SELECT
            (SELECT * FROM today)
            - (SELECT * FROM past_seven_result)
        AS std;
        """
    )

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def respiratory_rate(db: AsyncSessionDep, user_id: int) -> float | None:
    """
    Calculate respiratory rate from rr intervals

    Returns:
        float: beats/minute
    """

    query = text(
        """
        WITH cleaned AS (
            SELECT rr_ms, timestamp
            FROM af_rrinterval
            WHERE rr_ms > 0
                AND user_id = :user_id
                AND timestamp <= NOW()
        ),
        last_five AS (
            SELECT rr_ms, timestamp
            FROM cleaned
            WHERE timestamp >= (SELECT MAX(timestamp) FROM cleaned) - INTERVAL '5 minutes'
        ),
        cumulative AS (
            SELECT
                rr_ms,
                timestamp,
                (SUM(rr_ms) OVER (ORDER BY timestamp)) / 1000::float AS elapsed
            FROM last_five
        ),
        smoothed AS (
            SELECT
                rr_ms,
                elapsed,
                timestamp,
                AVG(rr_ms) OVER (
                    ORDER BY timestamp
                    ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
                ) AS averaged
            FROM cumulative
        ),
        possible_peaks AS (
            SELECT
                elapsed,
                timestamp,
                averaged,
                LAG(averaged, 1) OVER (ORDER BY timestamp) AS bef,
                LEAD(averaged, 1) OVER (ORDER BY timestamp) AS aft
            FROM smoothed
        ),
        peaks AS (
            SELECT elapsed, timestamp
            FROM possible_peaks
            WHERE averaged > bef
                AND averaged > aft
        ),
        intervals AS (
            SELECT
                timestamp,
                elapsed - LAG(elapsed, 1) OVER (ORDER BY timestamp) AS interval
            FROM peaks
        ),
        valid_intervals AS (
            SELECT timestamp, interval
            FROM intervals
            WHERE interval >= 2.5
                AND interval <= 10.0
        )

        SELECT 60.0 / percentile_cont(0.5) WITHIN GROUP (ORDER BY interval) AS respiratory_rate
        FROM valid_intervals
        """
    )

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def calculate_effort_strain(db: AsyncSessionDep, user_id: int) -> float | None:
    """Calculates strain/effort for a user over the most recent 24 hours with data."""

    query = text(
        """
        WITH clean AS (
            SELECT bpm, timestamp
            FROM af_heartrate
            WHERE timestamp <= NOW()
                AND user_id = :user_id
                AND bpm > 30
                AND bpm < 220
        ),
        max_time AS (
            SELECT MAX(timestamp)
            FROM clean
        ),
        rhr AS (
            SELECT
                percentile_cont(.1)
                WITHIN GROUP (ORDER BY median_bpm) AS rhr
            FROM (
                SELECT
                    date_bin(
                        INTERVAL '10 minutes',
                        timestamp,
                        TIMESTAMPTZ '2000-01-01 00:00:00+00'
                    ) AS bins,
                    percentile_cont(.5)
                    WITHIN GROUP (ORDER BY bpm) AS median_bpm
                FROM clean
                GROUP BY bins
            ) AS medians
        ),
        rates AS (
            SELECT
                clean.*,
                (SELECT * FROM rhr) AS rhr,
                (SELECT MAX(bpm) FROM clean) AS max_bpm
            FROM clean
            WHERE timestamp <= (SELECT * FROM max_time)
                AND timestamp >= (
                    SELECT * FROM max_time
                ) - INTERVAL '1 day'
        ),
        percent_hrr AS (
            SELECT
                rates.*,
                LEAST(
                    100,
                    GREATEST(
                        0,
                        (bpm - rhr) / (max_bpm - rhr) * 100
                    )
                ) AS hrr
            FROM rates
        ),
        weighted AS (
            SELECT
                percent_hrr.*,
                CASE
                    WHEN hrr < 50 THEN 0
                    WHEN hrr < 59.9 THEN 1
                    WHEN hrr < 69.9 THEN 2
                    WHEN hrr < 79.9 THEN 3
                    WHEN hrr < 89.9 THEN 4
                    ELSE 5
                END AS weight
            FROM percent_hrr
        ),
        gaps AS (
            SELECT
                weighted.*,
                EXTRACT(
                    EPOCH FROM (
                        LEAD(timestamp, 1) OVER (ORDER BY timestamp)
                        - timestamp
                    )
                ) / 60 AS gap
            FROM weighted
        )

        SELECT
            100 * (
                LN(SUM(weight * gap) + 1)
                / LN(7201)
            ) AS effort
        FROM gaps;
        """
    )

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()


async def calculate_calories(db: AsyncSessionDep, user_id: int) -> float | None:
    """Calculate estimated calories for a user over their most recent day of HR data."""

    query = text(
        """
        WITH max_time AS (
            SELECT MAX(timestamp)
            FROM af_heartrate
            WHERE timestamp <= NOW()
                AND user_id = :user_id
        ),
        clean AS (
            SELECT bpm, timestamp
            FROM af_heartrate
            WHERE (SELECT * FROM max_time) >= timestamp
                AND timestamp >= (SELECT * FROM max_time) - INTERVAL '1 day'
                AND user_id = :user_id
                AND bpm > 30
                AND bpm < 220
        ),
        rhr AS (
            SELECT
                percentile_cont(.1)
                WITHIN GROUP (ORDER BY median_bpm) AS rhr
            FROM (
                SELECT
                    date_bin(
                        INTERVAL '10 minutes',
                        timestamp,
                        TIMESTAMPTZ '2000-01-01 00:00:00+00'
                    ) AS bins,
                    percentile_cont(.5)
                    WITHIN GROUP (ORDER BY bpm) AS median_bpm
                FROM clean
                GROUP BY bins
            ) AS medians
        ),
        max_bpm AS (
            SELECT MAX(bpm) AS max_bpm
            FROM clean
        ),
        active_threshold AS (
            SELECT
                rhr.rhr + .5 * (max_bpm.max_bpm - rhr.rhr)
                AS active_threshold
            FROM max_bpm
            CROSS JOIN rhr
        ),
        vo2_max AS (
            SELECT
                15.3 * (max_bpm.max_bpm / rhr.rhr) AS vo2
            FROM max_bpm
            CROSS JOIN rhr
        ),
        user_info AS (
            SELECT weight, height, age, sex
            FROM af_user
            WHERE id = :user_id
        ),
        bmr AS (
            SELECT
                CASE
                    WHEN sex = 'Male'
                        THEN 88.362
                            + 13.397 * weight
                            + 4.799 * height
                            - 5.677 * age
                    WHEN sex = 'Female'
                        THEN 447.593
                            + 9.247 * weight
                            + 3.098 * height
                            - 4.330 * age
                END AS bmr
            FROM user_info
        ),
        gross_rates AS (
            SELECT
                (
                    CASE
                        WHEN sex = 'Male'
                            THEN -95.7735
                                + 0.634 * bpm
                                + 0.404 * vo2
                                + 0.394 * weight
                                + 0.271 * age
                        WHEN sex = 'Female'
                            THEN -59.3954
                                + 0.450 * bpm
                                + 0.380 * vo2
                                + 0.103 * weight
                                + 0.274 * age
                    END
                ) / 251.04 AS gross_rate,
                EXTRACT(
                    EPOCH FROM (
                        LEAD(timestamp) OVER (ORDER BY timestamp)
                        - timestamp
                    )
                ) AS interval,
                bpm
            FROM user_info
            CROSS JOIN vo2_max
            CROSS JOIN clean
        ),
        active_rates AS (
            SELECT
                CASE
                    WHEN bpm >= active_threshold THEN
                        GREATEST(
                            0,
                            gross_rate - (bmr / 86400.0)
                        )
                    ELSE 0
                END AS active_rate,
                interval
            FROM gross_rates
            CROSS JOIN bmr
            CROSS JOIN active_threshold
        ),
        active_calories AS (
            SELECT
                SUM(interval * active_rate) AS active_cal
            FROM active_rates
        )

        SELECT
            active_cal + bmr AS calories
        FROM active_calories
        CROSS JOIN bmr;
        """
    )

    result = await db.execute(query, {"user_id": user_id})

    return result.scalar_one()
