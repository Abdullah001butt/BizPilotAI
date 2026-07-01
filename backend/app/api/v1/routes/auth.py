"""Authentication endpoints: register, login, refresh, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.token import TokenPair
from app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
async def register(data: RegisterRequest, service: AuthServiceDep) -> UserPublic:
    """Register a new user. Self-service signups receive the Employee role."""
    user = await service.register(data)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenPair, summary="Log in and get tokens")
async def login(data: LoginRequest, service: AuthServiceDep) -> TokenPair:
    """Exchange email + password for an access/refresh token pair."""
    _, tokens = await service.login(data)
    return tokens


@router.post("/refresh", response_model=TokenPair, summary="Rotate tokens")
async def refresh(data: RefreshRequest, service: AuthServiceDep) -> TokenPair:
    """Exchange a valid refresh token for a new (rotated) token pair."""
    return await service.refresh(data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
async def logout(data: RefreshRequest, service: AuthServiceDep) -> Response:
    """Revoke the presented refresh token, ending that session."""
    await service.logout(data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic, summary="Current user profile")
async def me(current_user: CurrentUser) -> UserPublic:
    """Return the profile of the currently authenticated user."""
    return UserPublic.model_validate(current_user)
