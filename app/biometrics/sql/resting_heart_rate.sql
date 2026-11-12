WITH medians AS (
    SELECT
        date_trunc('day', timestamp) AS day,
        date_bin(
            INTERVAL '10 minutes',
            timestamp,
            TIMESTAMPTZ '2000-01-01 00:00:00+00'
        ) AS bins,
        percentile_cont(.5) WITHIN GROUP (ORDER BY bpm) AS median_bpm
    FROM af_heartrate
    WHERE timestamp <= CAST(:end_time AS TIMESTAMPTZ)
        AND timestamp >= CAST(:start_time AS TIMESTAMPTZ)
        AND bpm > 30
        AND bpm < 220
        AND user_id = :user_id
    GROUP BY day, bins
),
daily_rhr AS (
    SELECT
        day,
        percentile_cont(.1) WITHIN GROUP (ORDER BY median_bpm) AS rhr
    FROM medians
    GROUP BY day
),
mean_rhr AS (
    SELECT AVG(rhr) AS mean_rhr
    FROM daily_rhr
),
latest_rhr AS (
    SELECT rhr
    FROM daily_rhr
    ORDER BY day DESC
    LIMIT 1
)
SELECT latest_rhr.rhr - mean_rhr.mean_rhr AS rhr
FROM mean_rhr
LEFT JOIN latest_rhr ON TRUE;
