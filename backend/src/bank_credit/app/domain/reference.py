"""Reference data: stages, sectors and the routes (amount bands and SLAs) between them."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise

from sqlalchemy import select
from sqlalchemy.orm import Session

from bank_credit.app.models import Sector, Stage, StageRoute

# Codes are stable English identifiers; names are the pt-BR display data.
STAGES: tuple[tuple[str, str], ...] = (
    ("document_check", "Checagem"),
    ("screening", "Triagem"),
    ("analysis", "Análise"),
    ("instrument_drafting", "Criação de Instrumento"),
    ("disbursement", "Central de Desembolso"),
)
SECTORS: dict[str, str] = {
    "retail_center": "Central de Varejo",
    "mid_large_center": "Central de Médio e Grande",
    "disbursement_center": "Central de Desembolso",
}

BAND_LIMIT = Decimal("4800000.00")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class RouteSpec:
    stage: str
    sector: str
    min_amount: Decimal
    max_amount: Decimal | None  # exclusive; None means no upper bound
    sla_hours: int


def _banded(stage: str, retail_hours: int, mid_large_hours: int) -> tuple[RouteSpec, ...]:
    return (
        RouteSpec(stage, "retail_center", ZERO, BAND_LIMIT, retail_hours),
        RouteSpec(stage, "mid_large_center", BAND_LIMIT, None, mid_large_hours),
    )


ROUTES: tuple[RouteSpec, ...] = (
    *_banded("document_check", 24, 48),
    *_banded("screening", 24, 48),
    *_banded("analysis", 72, 120),
    *_banded("instrument_drafting", 48, 72),
    RouteSpec("disbursement", "disbursement_center", ZERO, None, 24),
)


def validate_routes(routes: tuple[RouteSpec, ...] | list[RouteSpec] = ROUTES) -> None:
    """Each stage's bands must cover [0, inf) with no gaps or overlaps."""
    stage_codes = {code for code, _ in STAGES}
    by_stage: dict[str, list[RouteSpec]] = defaultdict(list)
    for route in routes:
        if route.stage not in stage_codes:
            raise ValueError(f"unknown stage {route.stage!r}")
        if route.sector not in SECTORS:
            raise ValueError(f"unknown sector {route.sector!r}")
        if route.sla_hours <= 0:
            raise ValueError(f"{route.stage}: sla_hours must be positive")
        if route.max_amount is not None and route.max_amount <= route.min_amount:
            raise ValueError(f"{route.stage}: empty band starting at {route.min_amount}")
        by_stage[route.stage].append(route)
    for code in stage_codes:
        bands = sorted(by_stage[code], key=lambda r: r.min_amount)
        if not bands:
            raise ValueError(f"{code}: no routes")
        if bands[0].min_amount != 0:
            raise ValueError(f"{code}: bands must start at 0")
        for prev, nxt in pairwise(bands):
            if prev.max_amount != nxt.min_amount:
                raise ValueError(f"{code}: gap or overlap at {nxt.min_amount}")
        if bands[-1].max_amount is not None:
            raise ValueError(f"{code}: last band must be unbounded")


def ensure_reference_data(db: Session) -> None:
    """Idempotent get-or-create by code. Does not commit; existing rows are left as they are."""
    validate_routes()
    sectors = {s.code: s for s in db.scalars(select(Sector))}
    for code, name in SECTORS.items():
        if code not in sectors:
            sectors[code] = Sector(code=code, name=name)
            db.add(sectors[code])
    stages = {s.code: s for s in db.scalars(select(Stage))}
    for position, (code, name) in enumerate(STAGES, start=1):
        if code not in stages:
            stages[code] = Stage(code=code, name=name, position=position)
            db.add(stages[code])
    db.flush()
    existing = {(r.stage_id, r.min_amount) for r in db.scalars(select(StageRoute))}
    for spec in ROUTES:
        stage, sector = stages[spec.stage], sectors[spec.sector]
        if (stage.id, spec.min_amount) not in existing:
            db.add(
                StageRoute(
                    stage_id=stage.id,
                    sector_id=sector.id,
                    min_amount=spec.min_amount,
                    max_amount=spec.max_amount,
                    sla_hours=spec.sla_hours,
                )
            )
    db.flush()
