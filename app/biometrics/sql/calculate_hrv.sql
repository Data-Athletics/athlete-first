WITH user_rr AS (
    SELECT rr_ms, timestamp, id
    FROM af_rrinterval
    WHERE user_id = :user_id
        AND timestamp >= CAST(:end_time AS TIMESTAMPTZ) - INTERVAL '2 months'
        AND timestamp <= CAST(:end_time AS TIMESTAMPTZ)
)

SELECT SQRT(AVG(diff ^ 2)) AS hrv
FROM (
    SELECT
        rr_ms - LAG(rr_ms, 1) OVER (ORDER BY timestamp) AS diff
    FROM user_rr
) AS diffs;
