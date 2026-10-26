-- v_time_in_stage_weekly (v1)
--
-- Meaning: how long finished stage intervals took, per stage, sector and week.
-- Grain:   one row per (stage_code, sector_code, week_start). week_start is the Monday (UTC) of the
--          week in which the interval ended. Percentiles cannot be summed across weeks, so
--          consumers must not re-aggregate rows.
-- n: finished intervals. avg_h, p50_h, p90_h: hours, numeric rounded to 2 decimals
--   (percentile_cont, linear interpolation). Open intervals are not counted.
-- Source: v_request_stage_intervals.

CREATE VIEW v_time_in_stage_weekly AS
SELECT w.stage_code,
       w.sector_code,
       w.week_start,
       count(*) AS n,
       round(CAST(avg(w.duration_s) / 3600 AS numeric), 2) AS avg_h,
       round(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY w.duration_h) AS numeric), 2) AS p50_h,
       round(CAST(percentile_cont(0.9) WITHIN GROUP (ORDER BY w.duration_h) AS numeric), 2) AS p90_h
FROM (
    SELECT i.stage_code,
           i.sector_code,
           CAST(date_trunc('week', i.exited_at AT TIME ZONE 'UTC') AS date) AS week_start,
           i.duration_s,
           CAST(i.duration_s AS double precision) / 3600 AS duration_h
    FROM v_request_stage_intervals i
    WHERE i.exited_at IS NOT NULL
) w
GROUP BY w.stage_code, w.sector_code, w.week_start;
