WITH clean AS (
    SELECT
        bpm,
        timestamp,
        date_trunc('day', timestamp) AS day
    FROM af_heartrate
    WHERE timestamp >= CAST(:start_time AS TIMESTAMPTZ)
        AND timestamp <= CAST(:end_time AS TIMESTAMPTZ)
        AND user_id = :user_id
        AND bpm > 30
        AND bpm < 220
),
medians AS (
    SELECT
        day,
        date_bin(
            INTERVAL '10 minutes',
            timestamp,
            TIMESTAMPTZ '2000-01-01 00:00:00+00'
        ) AS bins,
        percentile_cont(.5) WITHIN GROUP (ORDER BY bpm) AS median_bpm
    FROM clean
    GROUP BY day, bins
),
daily_rhr AS (
    SELECT
        day,
        percentile_cont(.1) WITHIN GROUP (ORDER BY median_bpm) AS rhr
    FROM medians
    GROUP BY day
),
daily_max AS (
    SELECT day, MAX(bpm) AS max_bpm
    FROM clean
    GROUP BY day
),
rates AS (
    SELECT
        clean.*,
        daily_rhr.rhr,
        daily_max.max_bpm
    FROM clean
    JOIN daily_rhr ON daily_rhr.day = clean.day
    JOIN daily_max ON daily_max.day = clean.day
),
percent_hrr AS (
    SELECT
        rates.*,
        LEAST(
            100,
            GREATEST(
                0,
                (bpm - rhr) / NULLIF(max_bpm - rhr, 0) * 100
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
                LEAD(timestamp) OVER (PARTITION BY day ORDER BY timestamp)
                - timestamp
            )
        ) / 60 AS gap
    FROM weighted
),
daily_effort AS (
    SELECT
        day,
        100 * (
            LN(SUM(weight * gap) + 1)
            / LN(7201)
        ) AS effort
    FROM gaps
    GROUP BY day
)
SELECT day, effort AS value
FROM daily_effort
ORDER BY day;
