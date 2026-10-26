from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from bank_credit.app.config import get_settings
from bank_credit.app.db import get_db
from bank_credit.app.errors import register_error_handlers
from bank_credit.app.routers.analytics import router as analytics_router
from bank_credit.app.routers.auth import router as auth_router
from bank_credit.app.routers.credit_request import router as credit_router
from bank_credit.app.routers.credit_request import workflow_router
from bank_credit.app.routers.notification import router as notification_router


def create_app(cors_origins: list[str] | None = None) -> FastAPI:
    """Build the app. Without cors_origins they come from the settings (which need SECRET_KEY)."""
    app = FastAPI(
        title="Bank Credit API",
        version="1.0.0",
        description="Credit requests with a staged workflow, SLAs and an append-only event log.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins if cors_origins is None else cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(credit_router, prefix="/requests", tags=["credit_requests"])
    app.include_router(workflow_router, tags=["workflow"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(notification_router, prefix="/notifications", tags=["notifications"])

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {"message": "Bank Credit API"}

    @app.get("/health", include_in_schema=False)
    def health(db: Session = Depends(get_db)) -> JSONResponse:
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({"status": "ok"})

    return app
