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
