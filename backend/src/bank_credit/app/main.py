# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bank_credit.app.config import get_settings
from bank_credit.app.routers.auth import router as auth_router
from bank_credit.app.routers.credit_request import router as credit_router
from bank_credit.app.routers.graph import router as graph_router
from bank_credit.app.routers.notification import router as notification_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="API de Solicitação de Crédito",
        version="1.0.0",
        description=(
            "Simulação de fluxo de solicitação de crédito bancário com checklist, "
            "roteamento por grafo, SLAs e notificações"
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(credit_router, prefix="/requests", tags=["credit_requests"])
    app.include_router(graph_router, prefix="/graph", tags=["process_graph"])
    app.include_router(notification_router, prefix="/notifications", tags=["notifications"])

    @app.get("/")
    def read_root():
        return {"message": "Bem-vindo à API de Solicitação de Crédito Bancário!"}

    return app
