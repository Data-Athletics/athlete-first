WITH cleaned AS (
    SELECT
        rr_ms,
        timestamp,
        date_trunc('day', timestamp) AS day
    FROM af_rrinterval
    WHERE rr_ms > 0
        AND user_id = :user_id
        AND timestamp >= CAST(:start_time AS TIMESTAMPTZ)
        AND timestamp <= CAST(:end_time AS TIMESTAMPTZ)
),
cumulative_data AS (
    SELECT
        rr_ms,
        timestamp,
        day,
        SUM(rr_ms) OVER (
            PARTITION BY day
            ORDER BY timestamp
        ) / 1000::float AS elapsed
    FROM cleaned
),
smoothed AS (
    SELECT
        rr_ms,
        elapsed,
        timestamp,
        day,
        AVG(rr_ms) OVER (
            PARTITION BY day
            ORDER BY timestamp
            ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
        ) AS averaged
    FROM cumulative_data
),
possible_peaks AS (
    SELECT
        elapsed,
        timestamp,
        averaged,
        day,
        LAG(averaged) OVER (PARTITION BY day ORDER BY timestamp) AS bef,
        LEAD(averaged) OVER (PARTITION BY day ORDER BY timestamp) AS aft
    FROM smoothed
),
peaks AS (
    SELECT elapsed, timestamp, day
    FROM possible_peaks
    WHERE averaged > bef
        AND averaged > aft
),
intervals AS (
    SELECT
        timestamp,
        day,
        elapsed - LAG(elapsed) OVER (PARTITION BY day ORDER BY timestamp) AS interval
    FROM peaks
),
valid_intervals AS (
    SELECT day, interval
    FROM intervals
    WHERE interval >= 2.5
        AND interval <= 10.0
),
daily_rates AS (
    SELECT
        day,
        60.0 / percentile_cont(.5) WITHIN GROUP (ORDER BY interval) AS respiratory_rate
    FROM valid_intervals
    GROUP BY day
),
mean_rate AS (
    SELECT AVG(respiratory_rate) AS mean_rate
    FROM daily_rates
),
latest_rate AS (
    SELECT respiratory_rate
    FROM daily_rates
    ORDER BY day DESC
    LIMIT 1
)
SELECT latest_rate.respiratory_rate - mean_rate.mean_rate AS respiratory_rate
FROM mean_rate
LEFT JOIN latest_rate ON TRUE;
