"""API errors: every error body is {detail, code}."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from bank_credit.app.domain.workflow import WorkflowError


class ApiError(HTTPException):
    """An HTTPException that carries a stable machine-readable code."""

    def __init__(
        self, status_code: int, detail: str, code: str, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = getattr(exc, "code", f"http_{exc.status_code}")
        return JSONResponse(
            {"detail": exc.detail, "code": code}, status_code=exc.status_code, headers=exc.headers
        )

    @app.exception_handler(WorkflowError)
    async def workflow_error(_request: Request, exc: WorkflowError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail, "code": exc.code}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"detail": jsonable_encoder(exc.errors()), "code": "validation_error"},
            status_code=422,
        )
