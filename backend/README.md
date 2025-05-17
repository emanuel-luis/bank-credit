# Bank Credit API

API de solicitação de crédito bancário com autenticação, checklist, roteamento por grafo, SLAs e notificações.

## Configuração do Ambiente

1. Crie um ambiente virtual Python:
```bash
python -m venv venv
```

2. Ative o ambiente virtual:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```env
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./bank_credit.db
```

## Executando o Projeto

1. Certifique-se de que o ambiente virtual está ativado

2. Execute o servidor:
```bash
python -m uvicorn bank_credit.app.main:app --reload
```

3. Acesse a documentação da API:
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
