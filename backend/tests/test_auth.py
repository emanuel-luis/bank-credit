from fastapi import status
from bank_credit.app.models import User, Client, Employee


def test_register_user(test_app, db, faker):
    email = faker.unique.email()
    payload = {
        "cnpj": faker.unique.cnpj(),
        "nome_fantasia": faker.company(),
        "razao_social": faker.company_suffix(),
        "cnae_principal": "6201-5/01",
        "cnae_principal_desc": "Desenvolvimento de programas de computador sob encomenda",
        "cnae_secundario": "6202-3/00",
        "cnae_secundario_desc": "Desenvolvimento de programas de computador customizáveis",
        "natureza_juridica": "2062",
        "natureza_juridica_desc": "Sociedade Empresária Limitada",
        "logradouro": faker.street_name(),
        "numero": faker.building_number(),
        "complemento": "",
        "cep": faker.postcode().replace("-", ""),
        "bairro": faker.bairro(),
        "municipio": faker.city(),
        "uf": faker.estado_sigla(),
        "user": {
            "full_name": faker.name(),
            "phone": faker.msisdn()[0:11],
            "email": email,
            "password": faker.password(),
            "groups": []
        }
    }
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == email
    assert "hashed_password" not in data["user"]
    db_user = db.query(User).filter(User.email == email).first()
    assert db_user is not None
    db_client = db.query(Client).filter(Client.cnpj == payload["cnpj"]).first()
    assert db_client is not None
    assert db_client.user_id == db_user.id


def test_register_existing_email(test_app, db, client, faker):
    payload = {
        "cnpj": faker.unique.cnpj(),
        "nome_fantasia": faker.company(),
        "razao_social": faker.company_suffix(),
        "cnae_principal": "6201-5/01",
        "cnae_principal_desc": "Desenvolvimento de programas de computador sob encomenda",
        "cnae_secundario": "6202-3/00",
        "cnae_secundario_desc": "Desenvolvimento de programas de computador customizáveis",
        "natureza_juridica": "2062",
        "natureza_juridica_desc": "Sociedade Empresária Limitada",
        "logradouro": faker.street_name(),
        "numero": faker.building_number(),
        "complemento": " ",
        "cep": faker.postcode().replace("-", ""),
        "bairro": faker.bairro(),
        "municipio": faker.city(),
        "uf": faker.estado_sigla(),
        "user": {
            "full_name": client.user.full_name,
            "phone": client.user.phone,
            "email": client.user.email,
            "password": faker.password(),
            "is_superuser": False,
            "groups": []
        }
    }
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email já cadastrado"


def test_login_success(test_app, client):
    response = test_app.post(
        "/auth/token",
        data={"username": client.user.email, "password": "test_password"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_app, client):
    response = test_app.post(
        "/auth/token",
        data={"username": client.user.email, "password": "wrong_password"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Usuário ou senha incorretos"


def test_login_nonexistent_user(test_app, faker):
    response = test_app.post(
        "/auth/token",
        data={"username": faker.unique.email(), "password": "password"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Usuário ou senha incorretos"


def test_protected_route_with_token(authorized_user):
    response = authorized_user.get("/auth/me")
    assert response.status_code == status.HTTP_200_OK


def test_protected_route_without_token(test_app):
    response = test_app.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_client_user(test_app, db, faker):
    email = faker.unique.email()
    cnpj = faker.unique.cnpj()
    payload = {
        "cnpj": cnpj,
        "nome_fantasia": faker.company(),
        "razao_social": faker.company_suffix(),
        "cnae_principal": "6201-5/01",
        "cnae_principal_desc": "Desenvolvimento de programas de computador sob encomenda",
        "cnae_secundario": "6202-3/00",
        "cnae_secundario_desc": "Desenvolvimento de programas de computador customizáveis",
        "natureza_juridica": "2062",
        "natureza_juridica_desc": "Sociedade Empresária Limitada",
        "logradouro": faker.street_name(),
        "numero": faker.building_number(),
        "complemento": "",
        "cep": faker.postcode().replace("-", ""),
        "bairro": faker.bairro(),
        "municipio": faker.city(),
        "uf": faker.estado_sigla(),
        "user": {
            "full_name": faker.name(),
            "phone": faker.msisdn()[0:11],
            "email": email,
            "password": faker.password(),
            "is_superuser": False,
            "groups": []
        }
    }
    response = test_app.post("/auth/register/client", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == email
    assert data["cnpj"] == cnpj
    db_user = db.query(User).filter(User.email == email).first()
    assert db_user is not None
    db_client = db.query(Client).filter(Client.cnpj == cnpj).first()
    assert db_client is not None
    assert db_client.user_id == db_user.id


def test_register_employee_user(test_app, db, faker):
    email = faker.unique.email()
    matricula = faker.unique.bothify(text="EMP###")
    cpf = faker.unique.cpf()
    payload = {
        "matricula": matricula,
        "cpf": cpf,
        "user": {
            "full_name": faker.name(),
            "phone": faker.msisdn()[0:11],
            "email": email,
            "password": faker.password(),
            "is_superuser": False,
            "groups": [],
        },
    }
    response = test_app.post("/auth/register/employee", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == email
    assert data["matricula"] == matricula
    db_user = db.query(User).filter(User.email == email).first()
    assert db_user is not None
    db_employee = db.query(Employee).filter(Employee.matricula == matricula).first()
    assert db_employee is not None
    assert db_employee.user_id == db_user.id
