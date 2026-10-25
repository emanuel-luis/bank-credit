# Bank Credit API

API de solicitação de crédito bancário com autenticação, checklist, roteamento por grafo, SLAs e notificações.

## Configuração do Ambiente

1. Instale as dependências (requer [uv](https://docs.astral.sh/uv/)):
```bash
uv sync
```

2. Crie o arquivo de configuração a partir do exemplo e gere uma chave secreta:
```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```
Cole o valor gerado em `SECRET_KEY` no `.env`. A aplicação não inicia sem essa variável.

## Executando o Projeto

Execute o servidor (`--reload` é opcional, para desenvolvimento):
```bash
uv run serve --reload
```

Acesse a documentação da API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints Principais

- `/auth/register`: Registro de novos usuários
- `/auth/token`: Login e obtenção de token JWT
- `/requests`: Gerenciamento de solicitações de crédito
- `/graph`: Endpoints relacionados ao fluxo do processo
- `/notifications`: Sistema de notificações

## Estrutura do Projeto

```
bank_credit/
├── app/
│   ├── routers/
│   ├── auth.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── utils.py
├── .env
└── requirements.txt
```
