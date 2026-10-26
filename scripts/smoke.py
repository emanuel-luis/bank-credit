"""End-to-end smoke test against a running stack. Standard library only.

Registers a customer, submits a request and has the staff of each sector approve it through
every stage. Exits 1 with a message on the first failed check.

    BASE_URL      API root (default http://localhost:8080/api, the web container's proxy)
    DEMO_PASSWORD password of the seeded demo users (also --demo-password)
"""

import argparse
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta

STAGES = 5
REQUIRED_DOCUMENTS = [
    "company_registration",
    "financial_statements",
    "business_plan",
    "tax_clearance",
]
_WEIGHTS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


class SmokeError(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def cnpj_digit(chars: str) -> str:
    total = sum((ord(c) - 48) * w for c, w in zip(chars, _WEIGHTS[-len(chars) :], strict=True))
    rest = total % 11
    return "0" if rest < 2 else str(11 - rest)


def new_cnpj() -> str:
    base = "".join(secrets.choice("0123456789") for _ in range(8)) + "0001"
    base += cnpj_digit(base)
    return base + cnpj_digit(base)


class Api:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def call(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: object = None,
        form: dict | None = None,
    ) -> tuple[int, dict | list]:
        headers = {"Accept": "application/json"}
        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                return exc.code, json.loads(raw)
            except ValueError:
                return exc.code, {"detail": raw[:200]}
        except urllib.error.URLError as exc:
            raise SmokeError(f"cannot reach {request.full_url}: {exc.reason}") from exc

    def expect(self, status: int, method: str, path: str, **kwargs: object) -> dict | list:
        got, payload = self.call(method, path, **kwargs)  # type: ignore[arg-type]
        check(got == status, f"{method} {path}: expected {status}, got {got}: {payload}")
        return payload

    def login(self, email: str, password: str) -> str:
        payload = self.expect(
            200, "POST", "/auth/token", form={"username": email, "password": password}
        )
        return payload["access_token"]  # type: ignore[call-overload]


def run(base_url: str, demo_password: str) -> None:
    api = Api(base_url)
    suffix = secrets.token_hex(6)
    email, password = f"smoke-{suffix}@example.com", secrets.token_urlsafe(16)

    api.expect(
        200,
        "POST",
        "/auth/register/client",
        body={
            "cnpj": new_cnpj(),
            "trade_name": f"Smoke {suffix}",
            "legal_name": f"Smoke {suffix} Ltda",
            "cnae_primary": "6201-5/01",
            "cnae_primary_desc": "Custom software development",
            "legal_nature_code": "2062",
            "legal_nature_desc": "Sociedade Empresaria Limitada",
            "street": "Rua Exemplo",
            "number": "100",
            "postal_code": "01310100",
            "district": "Centro",
            "city": "Sao Paulo",
            "state": "SP",
            "user": {
                "full_name": "Smoke Customer",
                "phone": "11987654321",
                "email": email,
                "password": password,
            },
        },
    )
    print(f"registered {email}")
    customer_token = api.login(email, password)

    deliver = (datetime.now(UTC) + timedelta(days=30)).date().isoformat()
    request = api.expect(
        201,
        "POST",
        "/requests",
        token=customer_token,
        body={
            "amount": "125000.00",
            "purpose": "Smoke test",
            "term_days": 90,
            "deliver_date": deliver,
            "documents": REQUIRED_DOCUMENTS,
        },
    )
    request_id = request["id"]  # type: ignore[call-overload]
    print(f"submitted request {request_id}")
    docs = sorted(d["document_type"] for d in request["documents"])  # type: ignore[call-overload]
    check(docs == sorted(REQUIRED_DOCUMENTS), f"unexpected documents on the detail: {docs}")

    path = f"/requests/{request_id}/transitions"
    status, payload = api.call(
        "POST",
        path,
        token=customer_token,
        body={"action": "approve", "expected_seq": request["last_seq"]},  # type: ignore[call-overload]
    )
    check(status == 403, f"the customer approving should be 403, got {status}: {payload}")

    approvals = 0
    detail = request
    for _ in range(STAGES + 2):  # a few spare turns, so a stuck request fails instead of looping
        detail = api.expect(200, "GET", f"/requests/{request_id}", token=customer_token)  # type: ignore[assignment]
        if detail["status"] == "APPROVED":  # type: ignore[call-overload]
            break
        check(detail["status"] == "IN_REVIEW", f"unexpected status {detail['status']}")  # type: ignore[call-overload]
        sector, stage = detail["sector"]["code"], detail["stage"]["code"]  # type: ignore[call-overload]
        staff = api.login(f"staff1.{sector}@example.com", demo_password)
        detail = api.expect(  # type: ignore[assignment]
            200,
            "POST",
            path,
            token=staff,
            body={"action": "approve", "expected_seq": detail["last_seq"]},  # type: ignore[call-overload]
        )
        approvals += 1
        print(f"stage {stage} approved by staff1.{sector}")
    check(approvals == STAGES, f"expected {STAGES} stage approvals, got {approvals}")
    check(detail["status"] == "APPROVED", f"final status is {detail['status']}")  # type: ignore[call-overload]

    history = api.expect(200, "GET", f"/requests/{request_id}/history", token=customer_token)
    types = [e["event_type"] for e in history]  # type: ignore[union-attr]
    check(types == ["SUBMITTED"] + ["STAGE_APPROVED"] * STAGES, f"unexpected history: {types}")
    seqs = [e["seq"] for e in history]  # type: ignore[union-attr]
    check(seqs == list(range(1, STAGES + 2)), f"history seq is not 1..{STAGES + 1}: {seqs}")
    print(f"ok: request {request_id} approved through {STAGES} stages")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-url", default=os.environ.get("BASE_URL", "http://localhost:8080/api")
    )
    parser.add_argument("--demo-password", default=os.environ.get("DEMO_PASSWORD"))
    args = parser.parse_args()
    if not args.demo_password:
        print("smoke FAILED: set DEMO_PASSWORD (or --demo-password)", file=sys.stderr)
        return 1
    try:
        run(args.base_url, args.demo_password)
    except SmokeError as exc:
        print(f"smoke FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
