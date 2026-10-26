-- v_throughput_daily (v1)
--
-- Meaning: work flowing through each sector per UTC day.
-- Grain:   one row per (sector_code, day). day is the UTC calendar date.
-- entered: stage intervals that started that day in the sector (new, approved-in and resubmitted).
-- approved, returned, rejected, cancelled, expired: stage intervals that ended that day in the
--   sector with that exit event. approved counts every stage approval (STAGE_APPROVED), including
--   the last stage; the sector is the one that held the request, not the next one.
-- Days without activity have no row. Source: v_request_stage_intervals.

CREATE VIEW v_throughput_daily AS
WITH moves AS (
    SELECT i.sector_code,
           CAST(i.entered_at AT TIME ZONE 'UTC' AS date) AS day,
           'ENTERED' AS kind
    FROM v_request_stage_intervals i
    UNION ALL
    SELECT i.sector_code,
           CAST(i.exited_at AT TIME ZONE 'UTC' AS date),
           i.exit_event
    FROM v_request_stage_intervals i
    WHERE i.exited_at IS NOT NULL
)
SELECT m.sector_code,
       m.day,
       count(*) FILTER (WHERE m.kind = 'ENTERED') AS entered,
       count(*) FILTER (WHERE m.kind = 'STAGE_APPROVED') AS approved,
       count(*) FILTER (WHERE m.kind = 'RETURNED') AS returned,
       count(*) FILTER (WHERE m.kind = 'REJECTED') AS rejected,
       count(*) FILTER (WHERE m.kind = 'CANCELLED') AS cancelled,
       count(*) FILTER (WHERE m.kind = 'EXPIRED') AS expired
FROM moves m
GROUP BY m.sector_code, m.day;
