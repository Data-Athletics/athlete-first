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
user_info AS (
    SELECT weight, height, age, lower(sex) AS sex
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
        END AS bmr,
        sex,
        weight,
        age
    FROM user_info
),
daily_params AS (
    SELECT
        daily_max.day,
        daily_rhr.rhr,
        daily_max.max_bpm,
        daily_rhr.rhr + .5 * (daily_max.max_bpm - daily_rhr.rhr)
            AS active_threshold,
        15.3 * (daily_max.max_bpm / NULLIF(daily_rhr.rhr, 0)) AS vo2
    FROM daily_max
    JOIN daily_rhr ON daily_rhr.day = daily_max.day
),
gross_rates AS (
    SELECT
        clean.day,
        clean.bpm,
        EXTRACT(
            EPOCH FROM (
                LEAD(clean.timestamp) OVER (
                    PARTITION BY clean.day ORDER BY clean.timestamp
                ) - clean.timestamp
            )
        ) AS interval,
        daily_params.active_threshold,
        bmr.bmr,
        (
            CASE
                WHEN bmr.sex = 'male'
                    THEN -95.7735
                        + 0.634 * clean.bpm
                        + 0.404 * daily_params.vo2
                        + 0.394 * bmr.weight
                        + 0.271 * bmr.age
                WHEN bmr.sex = 'female'
                    THEN -59.3954
                        + 0.450 * clean.bpm
                        + 0.380 * daily_params.vo2
                        + 0.103 * bmr.weight
                        + 0.274 * bmr.age
            END
        ) / 251.04 AS gross_rate
    FROM clean
    JOIN daily_params ON daily_params.day = clean.day
    CROSS JOIN bmr
),
active_rates AS (
    SELECT
        day,
        bmr,
        CASE
            WHEN bpm >= active_threshold THEN
                GREATEST(0, gross_rate - (bmr / 86400.0))
            ELSE 0
        END AS active_rate,
        interval
    FROM gross_rates
),
daily_calories AS (
    SELECT
        day,
        MAX(bmr) + SUM(interval * active_rate) AS calories
    FROM active_rates
    GROUP BY day
)
SELECT day, calories AS value
FROM daily_calories
ORDER BY day;
