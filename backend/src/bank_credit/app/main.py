# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bank_credit.app.database import engine, Base
from bank_credit.app.routers.auth import router as auth_router
from bank_credit.app.routers.credit_request import router as credit_router
from bank_credit.app.routers.graph import router as graph_router
from bank_credit.app.routers.notification import router as notification_router
import uvicorn

# Cria todas as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Solicitação de Crédito",
    version="1.0.0",
    description="Simulação de fluxo de solicitação de crédito bancário com checklist, roteamento por grafo, SLAs e notificações",
)

# Configuração de CORS para permitir chamadas do frontend
origins = [
    "http://localhost",
    "http://localhost:3000",
    # adicione outros domínios do frontend conforme necessário
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers do projeto
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(credit_router, prefix="/requests", tags=["credit_requests"])
app.include_router(graph_router, prefix="/graph", tags=["process_graph"])
app.include_router(notification_router, prefix="/notifications", tags=["notifications"])


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Solicitação de Crédito Bancário!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
