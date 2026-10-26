-- v_sla_breach_rate_weekly (v1)
--
-- Meaning: share of finished stage intervals that missed their SLA, per sector and week.
-- Grain:   one row per (sector_code, week_start). week_start is the Monday (UTC) of the week in
--          which the interval ended, because the SLA outcome is only known at exit.
-- closed:  intervals that ended in the week. breached: those that ended after sla_due_at.
-- breach_rate: breached / closed, numeric rounded to 4 decimals, between 0 and 1.
-- Open intervals are not counted. Source: v_request_stage_intervals.

CREATE VIEW v_sla_breach_rate_weekly AS
SELECT w.sector_code,
       w.week_start,
       count(*) AS closed,
       count(*) FILTER (WHERE w.sla_breached) AS breached,
       round(CAST(count(*) FILTER (WHERE w.sla_breached) AS numeric) / count(*), 4) AS breach_rate
FROM (
    SELECT i.sector_code,
           CAST(date_trunc('week', i.exited_at AT TIME ZONE 'UTC') AS date) AS week_start,
           i.sla_breached
    FROM v_request_stage_intervals i
    WHERE i.exited_at IS NOT NULL AND i.sla_due_at IS NOT NULL
) w
GROUP BY w.sector_code, w.week_start;
