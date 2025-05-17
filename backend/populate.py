# populate.py

from datetime import datetime, timedelta
from passlib.context import CryptContext

from bank_credit.app.database import SessionLocal, engine, Base
from bank_credit.app.models import Sector, Process, Client, Notification

# Initialize DB schema (if not already)
Base.metadata.create_all(bind=engine)

# Password hashing context (same as in auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def populate():
    db = SessionLocal()
    try:
        # --- Sectors ---
        sectors = [
            Sector(name="Documentation", limit=1_000_000.0, sla_days=2, require_all=False),
            Sector(name="RiskAnalysis", limit=500_000.0, sla_days=5, require_all=False),
            Sector(name="CreditCommittee", limit=100_000.0, sla_days=3, require_all=True),
        ]
        db.add_all(sectors)
        db.commit()

        # Refresh to get IDs
        for s in sectors:
            db.refresh(s)

        # --- Processes ---
        # Chain: Checklist -> Risk -> Committee -> End
        p_check = Process(name="Checklist", next_process_id=None)
        p_risk = Process(name="RiskAnalysis", next_process_id=None)
        p_commit = Process(name="CreditCommittee", next_process_id=None)

        # link next_process_id (after creation of all)
        db.add_all([p_check, p_risk, p_commit])
        db.commit()
        db.refresh(p_check)
        db.refresh(p_risk)
        db.refresh(p_commit)

        # set next links
        p_check.next_process_id = p_risk.id
        p_risk.next_process_id = p_commit.id
        p_commit.next_process_id = None  # end of chain
        db.add_all([p_check, p_risk, p_commit])
        db.commit()

        # Associate sectors with processes
        # Documentation sector handles Checklist
        sectors_map = {s.name: s for s in sectors}
        p_check.sectors.append(sectors_map["Documentation"])
        # RiskAnalysis sector handles RiskAnalysis
        p_risk.sectors.append(sectors_map["RiskAnalysis"])
        # CreditCommittee requires all of CreditCommittee sector
        p_commit.sectors.append(sectors_map["CreditCommittee"])
        db.commit()

        # --- Default client user ---
        test_client = Client(
            username="testuser",
            hashed_password=get_password_hash("testpass"),
            is_active=True,
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        # --- Sample notifications ---
        notif1 = Notification(
            client_id=test_client.id,
            subject="Bem-vindo!",
            message="Conta criada com sucesso. Use /auth/token para obter seu JWT.",
            read=False,
            created_at=datetime.utcnow(),
        )
        db.add(notif1)
        db.commit()

        print("Database populated with initial sectors, processes, user, and notification.")
    finally:
        db.close()


if __name__ == "__main__":
    populate()
