"""Current-user self-service endpoints (profile + password)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, UserServiceDep
from app.schemas.user import PasswordChange, ProfileUpdate, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserPublic, summary="Update my profile")
async def update_me(
    data: ProfileUpdate, current_user: CurrentUser, service: UserServiceDep
) -> UserPublic:
    """Update the authenticated user's own profile."""
    updated = await service.update_profile(current_user, data)
    return UserPublic.model_validate(updated)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change my password",
)
async def change_password(
    data: PasswordChange, current_user: CurrentUser, service: UserServiceDep
) -> Response:
    """Change the authenticated user's password and revoke other sessions."""
    await service.change_password(current_user, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
