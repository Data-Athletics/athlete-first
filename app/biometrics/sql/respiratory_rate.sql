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
FROM valid_intervals;
