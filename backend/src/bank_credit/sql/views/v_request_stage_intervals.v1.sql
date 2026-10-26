-- v_request_stage_intervals (v1)
--
-- Meaning: how long a request sat in a stage, and whether the stage SLA was missed.
-- Grain:   one row per entry into a review stage (events whose to_status is IN_REVIEW:
--          SUBMITTED, STAGE_APPROVED into the next stage, RESUBMITTED). Primary key (request_id, entry_seq).
-- Source:  request_events only, so the view is a pure function of the append-only log.
--
-- exited_at / exit_event: the next event that is not SLA_BREACHED. SLA_BREACHED never moves the
--   request, so it is not an interval boundary. NULL while the request is still in the stage.
-- sla_breached: exited_at > sla_due_at (NULL while open). A request that was returned, rejected,
--   cancelled or expired after its deadline counts as breached.
-- Times are timestamptz; duration_s is numeric seconds.

CREATE VIEW v_request_stage_intervals AS
WITH ordered AS (
    SELECT ev.request_id,
           ev.seq,
           ev.to_status,
           ev.stage_id,
           ev.sector_id,
           ev.sla_due_at,
           ev.occurred_at,
           LEAD(ev.occurred_at) OVER w AS next_at,
           LEAD(ev.event_type) OVER w AS next_event
    FROM request_events ev
    WHERE ev.event_type <> 'SLA_BREACHED'
    WINDOW w AS (PARTITION BY ev.request_id ORDER BY ev.seq)
)
SELECT o.request_id,
       o.seq AS entry_seq,
       st.code AS stage_code,
       st.position AS stage_position,
       sc.code AS sector_code,
       o.occurred_at AS entered_at,
       o.next_at AS exited_at,
       o.next_event AS exit_event,
       o.sla_due_at,
       EXTRACT(EPOCH FROM (o.next_at - o.occurred_at)) AS duration_s,
       CASE WHEN o.next_at IS NULL THEN NULL ELSE o.next_at > o.sla_due_at END AS sla_breached
FROM ordered o
JOIN stages st ON st.id = o.stage_id
JOIN sectors sc ON sc.id = o.sector_id
WHERE o.to_status = 'IN_REVIEW';
