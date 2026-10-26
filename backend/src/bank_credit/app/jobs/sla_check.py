"""sla-check: write the SLA_BREACHED and EXPIRED events that came due. Safe to re-run."""

import logging
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import TERMINAL_STATUSES
from bank_credit.app.domain.workflow import apply_due_system_events
from bank_credit.app.jobs.runs import job_run
from bank_credit.app.models import CreditRequest

logger = logging.getLogger("bank_credit.jobs.sla_check")


def sla_check(db: Session, now: datetime | None = None) -> int:
    """Return the events written. One transaction per request; timestamps are the deadlines."""
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    with job_run(db, "sla-check", {"now": now.isoformat()}) as run:
        due_ids = list(
            db.scalars(
                select(CreditRequest.id)
                .where(
                    CreditRequest.status.not_in(TERMINAL_STATUSES),
                    or_(CreditRequest.sla_due_at <= now, CreditRequest.expires_at <= now),
                )
                .order_by(CreditRequest.id)
            )
        )
        run.rows_read = len(due_ids)
        written = 0
        for request_id in due_ids:
            request = db.get(CreditRequest, request_id)
            assert request is not None
            db.refresh(request, with_for_update=True)
            written += len(apply_due_system_events(db, request, now, job_run_id=run.run_id))
            db.commit()
        run.rows_written = written
    logger.info("sla-check checked %d requests and wrote %d events", len(due_ids), written)
    return written
