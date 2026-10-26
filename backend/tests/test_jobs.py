import pytest
from sqlalchemy import func, select

from bank_credit.app.cli import main
from bank_credit.app.domain.documents import is_valid_cnpj, is_valid_cpf
from bank_credit.app.domain.enums import JobStatus, UserRole
from bank_credit.app.jobs.runs import job_run
from bank_credit.app.jobs.seed import seed
from bank_credit.app.models import Client, Employee, JobRun, Sector, User
from bank_credit.app.security import verify_password


def test_job_run_records_success(db):
    with job_run(db, "demo", {"k": 1}) as run:
        assert db.get(JobRun, run.run_id).status is JobStatus.RUNNING
        run.rows_read, run.rows_written = 3, 2
    row = db.get(JobRun, run.run_id)
    assert (row.job_name, row.params, row.status) == ("demo", {"k": 1}, JobStatus.SUCCEEDED)
    assert (row.rows_read, row.rows_written, row.error) == (3, 2, None)
    assert row.finished_at >= row.started_at


def test_job_run_records_failure_and_rolls_back_the_job(db):
    with pytest.raises(ValueError, match="boom"), job_run(db, "demo", {}) as run:
        db.add(Sector(code="temp", name="Temp"))
        db.flush()
        run.rows_written = 1
        raise ValueError("boom")
    row = db.get(JobRun, run.run_id)
    assert row.status is JobStatus.FAILED
    assert row.error == "ValueError: boom"
    assert row.rows_written == 1
    assert row.finished_at is not None
    assert db.scalar(select(Sector).where(Sector.code == "temp")) is None


def test_seed_is_idempotent(db):
    def counts():
        return [db.scalar(select(func.count()).select_from(m)) for m in (User, Employee, Client)]

    assert seed(db, "pw-one") == 13
    db.commit()
    assert counts() == [13, 10, 3]
    emails = set(db.scalars(select(User.email)))
    assert seed(db, "pw-two") == 0
    assert counts() == [13, 10, 3]
    assert set(db.scalars(select(User.email))) == emails


def test_seed_creates_demo_users(db):
    seed(db, "pw-one")
    users = list(db.scalars(select(User)))
    assert all(u.email.endswith("@example.com") for u in users)
    assert all(verify_password("pw-one", u.hashed_password) for u in users)
    by_role = {role: [u for u in users if u.role is role] for role in UserRole}
    assert [len(by_role[r]) for r in UserRole] == [3, 6, 3, 1]
    for sector in db.scalars(select(Sector)):
        roles = [u.role for u in users if u.employee and u.employee.sector_id == sector.id]
        assert sorted(roles) == [UserRole.MANAGER, UserRole.STAFF, UserRole.STAFF]
    assert all(is_valid_cpf(e.cpf) for e in db.scalars(select(Employee)))
    assert all(is_valid_cnpj(c.cnpj) for c in db.scalars(select(Client)))


@pytest.mark.parametrize("command", ["serve", "seed", "simulate", "sla-check"])
def test_cli_help(command, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([command, "--help"])
    assert exit_info.value.code == 0
    assert f"bank-credit {command}" in capsys.readouterr().out


def test_cli_requires_a_command():
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == 2
