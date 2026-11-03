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
            WHEN sex = 'male'
                THEN 88.362
                    + 13.397 * weight
                    + 4.799 * height
                    - 5.677 * age
            WHEN sex = 'female'
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
