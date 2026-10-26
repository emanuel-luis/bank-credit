import pytest
from conftest import PASSWORD, T0
from fastapi import status
from sqlalchemy import select

from bank_credit.app.domain.enums import UserRole
from bank_credit.app.models import Client, User


def test_register_client(test_app, db, client_payload):
    payload = client_payload()
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == payload["user"]["email"]
    assert data["user"]["role"] == "customer"
    assert data["cnpj"] == payload["cnpj"]
    assert "hashed_password" not in data["user"]
    user = db.scalar(select(User).where(User.email == payload["user"]["email"]))
    assert user is not None and user.role is UserRole.CUSTOMER
    assert db.scalar(select(Client).where(Client.cnpj == payload["cnpj"])).user_id == user.id


def test_register_normalizes_a_formatted_cnpj(test_app, client_payload):
    payload = client_payload()
    cnpj = payload["cnpj"]
    payload["cnpj"] = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == 200
    assert response.json()["cnpj"] == cnpj


def test_register_rejects_an_invalid_cnpj(test_app, client_payload):
    payload = client_payload()
    payload["cnpj"] = payload["cnpj"][:-1] + ("0" if payload["cnpj"][-1] != "0" else "1")
    assert test_app.post("/auth/register/client", json=payload).status_code == 422


def test_register_existing_email_and_cnpj(test_app, customer, client_payload):
    payload = client_payload()
    payload["user"]["email"] = customer.email
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Email already registered", "code": "email_taken"}

    payload = client_payload()
    payload["cnpj"] = customer.client.cnpj
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == 400
    assert response.json()["code"] == "cnpj_taken"


def test_register_employee_is_gone(test_app):
    assert test_app.post("/auth/register/employee", json={}).status_code == 404


@pytest.mark.parametrize(
    "extra",
    [{"role": "admin"}, {"is_superuser": True}, {"groups": ["x"]}, {"role": "customer"}],
)
def test_register_client_rejects_privilege_fields(test_app, client_payload, extra):
    payload = client_payload()
    payload["user"].update(extra)
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "validation_error"


def test_register_client_rejects_role_at_the_top_level(test_app, client_payload):
    payload = client_payload()
    payload["role"] = "admin"
    assert test_app.post("/auth/register/client", json=payload).status_code == 422


def test_login_sets_last_login(test_app, db, customer):
    assert customer.last_login_at is None
    response = test_app.post("/auth/token", data={"username": customer.email, "password": PASSWORD})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["token_type"] == "bearer"
    db.refresh(customer)
    assert customer.last_login_at == T0


def test_login_wrong_password(test_app, customer):
    response = test_app.post(
        "/auth/token", data={"username": customer.email, "password": "wrong_password"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect email or password", "code": "invalid_login"}


def test_login_nonexistent_user(test_app):
    response = test_app.post(
        "/auth/token", data={"username": "nobody@bank-demo.org", "password": "password"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_inactive_user(test_app, db, customer):
    customer.is_active = False
    db.commit()
    response = test_app.post("/auth/token", data={"username": customer.email, "password": PASSWORD})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me(test_app, auth, customer, retail_staff):
    me = test_app.get("/auth/me", headers=auth(customer))
    assert me.status_code == status.HTTP_200_OK
    assert me.json()["role"] == "customer"
    assert me.json()["client"]["cnpj"] == customer.client.cnpj
    assert me.json()["employee"] is None
    staff = test_app.get("/auth/me", headers=auth(retail_staff)).json()
    assert staff["role"] == "staff"
    assert staff["employee"]["sector"]["code"] == "retail_center"
    assert "hashed_password" not in staff


def test_protected_route_without_token(test_app):
    assert test_app.get("/auth/me").status_code == status.HTTP_401_UNAUTHORIZED
