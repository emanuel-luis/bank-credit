"""Job run bookkeeping: every job writes a job_runs row that its events point back to."""

import logging
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import JobStatus
from bank_credit.app.models import JobRun

logger = logging.getLogger("bank_credit.jobs")


@contextmanager
def job_run(db: Session, name: str, params: dict[str, Any]) -> Iterator[JobRun]:
    """Record a run: running when entered, succeeded or failed when left.

    The row is committed on entry so events written in later transactions can reference it.
    The job sets rows_read and rows_written on the yielded row and owns its own commits; on an
    exception the open transaction is rolled back, the run is marked failed and the error re-raised.
    """
    run = JobRun(
        run_id=uuid.uuid4(),
        job_name=name,
        status=JobStatus.RUNNING,
        params=params,
        started_at=datetime.now(UTC),
        rows_read=0,
        rows_written=0,
    )
    run_id = run.run_id
    db.add(run)
    db.commit()
    logger.info("job %s started: run_id=%s at %s", name, run_id, run.started_at.isoformat())
    try:
        yield run
    except BaseException as exc:
        counts = (run.rows_read, run.rows_written)
        db.rollback()
        failed = db.get(JobRun, run_id)
        assert failed is not None
        failed.status = JobStatus.FAILED
        failed.finished_at = datetime.now(UTC)
        failed.rows_read, failed.rows_written = counts
        failed.error = f"{type(exc).__name__}: {exc}"
        db.commit()
        logger.error(
            "job %s failed: run_id=%s finished=%s rows_read=%s rows_written=%s error=%s",
            name,
            run_id,
            failed.finished_at.isoformat(),
            counts[0],
            counts[1],
            failed.error,
        )
        raise
    run.status = JobStatus.SUCCEEDED
    run.finished_at = datetime.now(UTC)
    db.commit()
    logger.info(
        "job %s succeeded: run_id=%s started=%s finished=%s rows_read=%s rows_written=%s",
        name,
        run_id,
        run.started_at.isoformat(),
        run.finished_at.isoformat(),
        run.rows_read,
        run.rows_written,
    )
