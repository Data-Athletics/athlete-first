SELECT
    percentile_cont(.1) WITHIN GROUP (ORDER BY median_bpm) AS rhr
FROM (
    SELECT
        date_bin(
            INTERVAL '10 minutes',
            timestamp,
            TIMESTAMPTZ '2000-01-01 00:00:00+00'
        ) as bins,
        percentile_cont(.5) WITHIN GROUP (ORDER BY bpm) AS median_bpm
    FROM af_heartrate
    WHERE timestamp <= CAST(:end_time AS TIMESTAMPTZ)
        AND timestamp >= CAST(:start_time AS TIMESTAMPTZ)
        AND bpm > 30
        AND bpm < 220
        AND user_id = :user_id
    GROUP BY bins
) AS medians;
