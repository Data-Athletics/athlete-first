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
