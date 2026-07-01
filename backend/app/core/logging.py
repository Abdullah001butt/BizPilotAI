"""Structured logging configuration.

We use `structlog` so every log line is structured (key/value). In development
it renders as colourised console output; in production it emits JSON, which is
what log aggregators (Datadog, Loki, CloudWatch) expect.
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure stdlib logging + structlog once, at application startup."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Route the stdlib root logger (used by uvicorn, sqlalchemy, etc.) to stdout.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.is_production
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)
