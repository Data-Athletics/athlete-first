WITH daily_diffs AS (
    SELECT
        date_trunc('day', timestamp) AS day,
        rr_ms - LAG(rr_ms) OVER (
            PARTITION BY date_trunc('day', timestamp)
            ORDER BY timestamp
        ) AS diff
    FROM af_rrinterval
    WHERE user_id = :user_id
        AND rr_ms > 0
        AND timestamp >= CAST(:start_time AS TIMESTAMPTZ)
        AND timestamp <= CAST(:end_time AS TIMESTAMPTZ)
),
daily_hrv AS (
    SELECT
        day,
        SQRT(AVG(diff ^ 2)) AS hrv
    FROM daily_diffs
    WHERE diff IS NOT NULL
    GROUP BY day
),
mean_hrv AS (
    SELECT AVG(hrv) AS mean_hrv
    FROM daily_hrv
),
latest_hrv AS (
    SELECT hrv
    FROM daily_hrv
    ORDER BY day DESC
    LIMIT 1
)
SELECT latest_hrv.hrv - mean_hrv.mean_hrv AS hrv
FROM mean_hrv
LEFT JOIN latest_hrv ON TRUE;
