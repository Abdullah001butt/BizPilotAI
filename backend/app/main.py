"""FastAPI application factory.

Assembles the app from its parts: logging, middleware, a uniform error contract,
and the versioned API router. Keeping this in a factory function makes the app
easy to instantiate fresh inside tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)


def _error_body(code: str, message: str, details: object | None = None) -> dict:
    """Uniform error envelope returned by every handled failure."""
    body: dict[str, object] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details  # type: ignore[index]
    return body


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    configure_logging()
    logger.info(
        "app_startup",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT.value,
        version=__version__,
    )
    yield
    logger.info("app_shutdown")


def register_exception_handlers(app: FastAPI) -> None:
    """Translate domain and validation errors into the uniform JSON envelope."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "validation_error",
                "Request validation failed.",
                # `jsonable_encoder` strips non-serialisable bits (e.g. the raw
                # ValueError stored in a Pydantic error's `ctx`).
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        message = (
            str(exc) if settings.DEBUG else "An unexpected error occurred."
        )
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", message),
        )


def create_application() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=__version__,
        description="AI-powered Business Operating System for SMBs.",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(RequestContextMiddleware)
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["root"], include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.PROJECT_NAME,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()
