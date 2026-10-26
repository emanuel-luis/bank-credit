from datetime import timedelta

from conftest import T0
from fastapi import status
from sqlalchemy import select

from bank_credit.app.domain import workflow
from bank_credit.app.domain.enums import Action, UserRole
from bank_credit.app.models import CreditRequest, Notification

HOUR = timedelta(hours=1)


def body(**overrides):
    return {
        "amount": "125000.00",
        "purpose": "Working capital",
        "term_days": 90,
        "deliver_date": (T0 + timedelta(days=30)).date().isoformat(),
        **overrides,
    }


def create(test_app, auth, user, **overrides):
    response = test_app.post("/requests", json=body(**overrides), headers=auth(user))
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def act(test_app, auth, user, request_id, action, seq, **extra):
    return test_app.post(
        f"/requests/{request_id}/transitions",
        json={"action": action, "expected_seq": seq, **extra},
        headers=auth(user),
    )


# --- Submission and detail ---


def test_customer_submits_and_reads_the_detail(test_app, auth, customer):
    data = create(test_app, auth, customer)
    assert data["amount"] == "125000.00"  # money is a string in JSON
    assert data["status"] == "IN_REVIEW"
    assert data["stage"] == {"code": "document_check", "name": "Checagem", "position": 1}
    assert data["sector"]["code"] == "retail_center"
    assert data["is_overdue"] is False
    assert data["last_seq"] == 1
    assert data["allowed_actions"] == ["cancel"]
    assert data["client"]["cnpj"] == customer.client.cnpj
    assert data["sla_due_at"] == "2026-01-06T10:00:00Z"
    assert data["estimated_completion_at"] == "2026-01-13T10:00:00Z"  # + 24 + 72 + 48 + 24 h

    detail = test_app.get(f"/requests/{data['id']}", headers=auth(customer))
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json() == data


def test_only_customers_submit(test_app, auth, retail_staff):
    response = test_app.post("/requests", json=body(), headers=auth(retail_staff))
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["code"] == "customers_only"


def test_submit_validation(test_app, auth, customer):
    for bad in ({"amount": "0"}, {"amount": "10.123"}, {"term_days": 0}, {"extra": 1}):
        response = test_app.post("/requests", json=body(**bad), headers=auth(customer))
        assert response.status_code == 422, bad
        assert response.json()["code"] == "validation_error"
    past = (T0 - timedelta(days=1)).date().isoformat()
    response = test_app.post("/requests", json=body(deliver_date=past), headers=auth(customer))
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_deliver_date"


def test_requests_need_a_token(test_app):
    response = test_app.get("/requests")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated", "code": "http_401"}


def test_customer_cannot_see_another_customers_request(
    test_app, auth, customer, other_customer, admin
):
    data = create(test_app, auth, customer)
    for path in (f"/requests/{data['id']}", f"/requests/{data['id']}/history"):
        response = test_app.get(path, headers=auth(other_customer))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["code"] == "request_not_found"
        assert test_app.get(path, headers=auth(admin)).status_code == status.HTTP_200_OK


# --- Transitions: authorization and conflicts ---


def test_authorization_and_conflicts(test_app, auth, customer, retail_staff, make_employee):
    data = create(test_app, auth, customer)
    rid = data["id"]
    mid_staff = make_employee(UserRole.STAFF, "mid_large_center")

    response = act(test_app, auth, customer, rid, "approve", 1)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["code"] == "forbidden"
    assert act(test_app, auth, mid_staff, rid, "approve", 1).status_code == 403
    assert act(test_app, auth, retail_staff, rid, "resubmit", 1).status_code == 403

    stale = act(test_app, auth, retail_staff, rid, "approve", 7)
    assert stale.status_code == status.HTTP_409_CONFLICT
    assert stale.json()["code"] == "stale_seq"

    wrong_state = act(test_app, auth, customer, rid, "resubmit", 1)
    assert wrong_state.status_code == 409
    assert wrong_state.json()["code"] == "invalid_transition"

    no_reason = act(test_app, auth, retail_staff, rid, "reject", 1)
    assert no_reason.status_code == 422
    assert no_reason.json()["code"] == "reason_required"

    ok = act(test_app, auth, retail_staff, rid, "approve", 1)
    assert ok.status_code == status.HTTP_200_OK
    assert ok.json()["stage"]["code"] == "screening"
    assert ok.json()["last_seq"] == 2
    # the same staff member no longer sees the request in their queue, but the call is stale
    assert act(test_app, auth, retail_staff, rid, "approve", 1).status_code == 409


def test_submit_action_is_not_a_transition(test_app, auth, customer):
    rid = create(test_app, auth, customer)["id"]
    response = act(test_app, auth, customer, rid, "submit", 1)
    assert response.status_code == 409
    assert response.json()["code"] == "invalid_transition"


def test_return_and_resubmit_over_the_api(test_app, auth, clock, customer, retail_staff):
    rid = create(test_app, auth, customer)["id"]
    clock.now = T0 + HOUR
    returned = act(test_app, auth, retail_staff, rid, "return", 1, reason="Missing statement")
    assert returned.json()["status"] == "RETURNED"
    assert returned.json()["allowed_actions"] == []  # staff cannot act on a returned request
    mine = test_app.get(f"/requests/{rid}", headers=auth(customer)).json()
    assert mine["allowed_actions"] == ["resubmit", "cancel"]
    assert act(test_app, auth, customer, rid, "resubmit", 2).json()["status"] == "IN_REVIEW"

    history = test_app.get(f"/requests/{rid}/history", headers=auth(customer)).json()
    assert [h["event_type"] for h in history] == ["SUBMITTED", "RETURNED", "RESUBMITTED"]
    assert [h["seq"] for h in history] == [1, 2, 3]
    assert history[1]["reason"] == "Missing statement"
    assert history[1]["actor"] == {
        "id": retail_staff.id,
        "full_name": retail_staff.full_name,
        "role": "staff",
    }
    assert history[0]["actor"]["role"] == "customer"


def test_lazy_expiry_over_the_api_keeps_the_event(test_app, auth, db, clock, customer, admin):
    rid = create(test_app, auth, customer)["id"]
    clock.now = T0 + timedelta(days=46)
    response = act(test_app, auth, admin, rid, "approve", 1)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "request_expired"
    detail = test_app.get(f"/requests/{rid}", headers=auth(customer)).json()
    assert detail["status"] == "EXPIRED"
    assert detail["allowed_actions"] == []
    assert db.scalar(select(Notification.subject).where(Notification.request_id == rid)) == (
        "Solicitação de crédito expirada"
    )


def test_customer_is_notified_of_the_outcome(test_app, auth, customer, retail_staff):
    rid = create(test_app, auth, customer)["id"]
    act(test_app, auth, retail_staff, rid, "reject", 1, reason="Outside policy")
    notes = test_app.get("/notifications/", headers=auth(customer)).json()
    assert [n["subject"] for n in notes] == ["Solicitação de crédito rejeitada"]
    assert "Outside policy" in notes[0]["message"]


# --- Listing and scopes ---


def test_scopes_by_role(
    test_app, auth, db, customer, other_customer, retail_staff, admin, make_employee
):
    mine = create(test_app, auth, customer)["id"]
    theirs = create(test_app, auth, other_customer, amount="5000000.00")["id"]

    as_customer = test_app.get("/requests", headers=auth(customer)).json()
    assert [r["id"] for r in as_customer["items"]] == [mine]
    assert as_customer["total"] == 1

    as_staff = test_app.get("/requests", headers=auth(retail_staff)).json()
    assert [r["id"] for r in as_staff["items"]] == [mine]  # retail queue only

    mid_staff = make_employee(UserRole.MANAGER, "mid_large_center")
    assert [
        r["id"] for r in test_app.get("/requests", headers=auth(mid_staff)).json()["items"]
    ] == [theirs]

    as_admin = test_app.get("/requests?scope=all", headers=auth(admin)).json()
    assert {r["id"] for r in as_admin["items"]} == {mine, theirs}
    assert as_admin["total"] == 2


def test_scope_not_allowed_for_the_role(test_app, auth, customer, retail_staff, admin):
    for user, scope in (
        (customer, "all"),
        (customer, "queue"),
        (retail_staff, "all"),
        (retail_staff, "mine"),
        (admin, "mine"),
    ):
        response = test_app.get(f"/requests?scope={scope}", headers=auth(user))
        assert response.status_code == status.HTTP_403_FORBIDDEN, (user.role, scope)
        assert response.json()["code"] == "scope_not_allowed"
    assert test_app.get("/requests?scope=mine", headers=auth(customer)).status_code == 200
    assert test_app.get("/requests?scope=queue", headers=auth(retail_staff)).status_code == 200


def test_filters_and_pagination(test_app, auth, clock, customer, admin):
    ids = [create(test_app, auth, customer)["id"] for _ in range(3)]
    clock.now = T0 + HOUR
    act(test_app, auth, admin, ids[0], "approve", 1)  # -> screening
    act(test_app, auth, admin, ids[1], "reject", 1, reason="no")

    def listing(query):
        return test_app.get(f"/requests?scope=all&{query}", headers=auth(admin)).json()

    assert {r["id"] for r in listing("status=REJECTED")["items"]} == {ids[1]}
    assert {r["id"] for r in listing("stage=screening")["items"]} == {ids[0]}
    assert {r["id"] for r in listing("stage=document_check&status=IN_REVIEW")["items"]} == {ids[2]}

    page = listing("limit=2&offset=0")
    assert page["total"] == 3 and len(page["items"]) == 2
    assert len(listing("limit=2&offset=2")["items"]) == 1
    assert test_app.get("/requests?limit=0", headers=auth(admin)).status_code == 422

    assert listing("overdue=true")["total"] == 0
    clock.now = T0 + 30 * HOUR  # ids[2] was due at +24 h, ids[0] (in screening since +1 h) at +25 h
    overdue = listing("overdue=true")
    assert {r["id"] for r in overdue["items"]} == {ids[2], ids[0]}
    assert all(r["is_overdue"] for r in overdue["items"])
    assert listing("overdue=false")["total"] == 3 - overdue["total"]


def test_queue_defaults_to_open_work_and_orders_by_deadline(
    test_app, auth, clock, customer, retail_staff
):
    first = create(test_app, auth, customer)["id"]
    clock.now = T0 + HOUR
    second = create(test_app, auth, customer)["id"]
    act(test_app, auth, retail_staff, second, "return", 1, reason="docs")
    queue = test_app.get("/requests", headers=auth(retail_staff)).json()
    assert [r["id"] for r in queue["items"]] == [first]  # the returned one waits on the customer
    returned = test_app.get("/requests?status=RETURNED", headers=auth(retail_staff)).json()
    assert [r["id"] for r in returned["items"]] == [second]


# --- Workflow map ---


def test_workflow_endpoint(test_app, auth, customer):
    data = test_app.get("/workflow", headers=auth(customer)).json()
    assert [s["code"] for s in data["stages"]] == [
        "document_check",
        "screening",
        "analysis",
        "instrument_drafting",
        "disbursement",
    ]
    analysis = data["stages"][2]
    assert analysis["name"] == "Análise"
    assert [
        (r["sector"]["code"], r["min_amount"], r["max_amount"], r["sla_hours"])
        for r in analysis["routes"]
    ] == [
        ("retail_center", "0.00", "4800000.00", 72),
        ("mid_large_center", "4800000.00", None, 120),
    ]
    assert len(data["stages"][4]["routes"]) == 1
    assert test_app.get("/workflow").status_code == 401


def test_domain_and_api_agree_on_allowed_actions(test_app, auth, db, customer, retail_staff):
    rid = create(test_app, auth, customer)["id"]
    request = db.get(CreditRequest, rid)
    for user in (customer, retail_staff):
        api = test_app.get(f"/requests/{rid}", headers=auth(user)).json()["allowed_actions"]
        assert api == [a.value for a in workflow.allowed_actions(request, user, T0)]
    assert workflow.allowed_actions(request, retail_staff, T0) == [
        Action.APPROVE,
        Action.RETURN,
        Action.REJECT,
    ]
