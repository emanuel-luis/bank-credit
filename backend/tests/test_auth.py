import pytest
from fastapi import status
from bank_credit.app.models import Client


def test_register_user(client, db):
    response = client.post("/auth/register", json={"username": "new_user", "email": "new_user@example.com", "password": "new_password"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "new_user"
    assert data["email"] == "new_user@example.com"
    assert "hashed_password" not in data

    # Verificar se o usuário foi realmente criado no banco
    db_user = db.query(Client).filter(Client.username == "new_user").first()
    assert db_user is not None
    assert db_user.username == "new_user"
    assert db_user.email == "new_user@example.com"


def test_register_existing_username(client, test_user):
    response = client.post("/auth/register", json={"username": "test_user", "email": "another@example.com", "password": "another_password"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Username já cadastrado"


def test_register_existing_email(client, test_user):
    response = client.post(
        "/auth/register", json={"username": "another_user", "email": "test_user@example.com", "password": "another_password"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email já cadastrado"


def test_login_success(client, test_user):
    response = client.post("/auth/token", data={"username": "test_user", "password": "test_password"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post("/auth/token", data={"username": "test_user", "password": "wrong_password"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Usuário ou senha incorretos"


def test_login_nonexistent_user(client):
    response = client.post("/auth/token", data={"username": "nonexistent", "password": "password"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Usuário ou senha incorretos"


def test_protected_route_with_token(authorized_client):
    response = authorized_client.get("/auth/me")
    assert response.status_code == status.HTTP_200_OK


def test_protected_route_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
