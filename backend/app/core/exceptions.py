"""Domain-level exceptions and their HTTP mapping.

Services and repositories raise these *domain* exceptions — they never import
FastAPI. A single set of handlers (registered in `main.py`) translates them into
consistent JSON HTTP responses. This keeps the business layer framework-agnostic
and the error contract uniform across the whole API.
"""

from __future__ import annotations

from fastapi import status


class AppError(Exception):
    """Base class for all expected, handled application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "The requested resource was not found."


class ConflictError(AppError):
    """Resource already exists / unique-constraint violation."""

    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"
    message = "The resource already exists."


class BusinessRuleError(AppError):
    """A request is well-formed but violates a business rule."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "business_rule_violation"
    message = "This operation is not allowed."


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "authentication_failed"
    message = "Could not validate credentials."


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "permission_denied"
    message = "You do not have permission to perform this action."


class InactiveUserError(AuthenticationError):
    error_code = "inactive_user"
    message = "This account is inactive."
