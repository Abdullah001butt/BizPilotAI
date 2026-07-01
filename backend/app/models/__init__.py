"""ORM models.

Importing the models here ensures they are all registered on `Base.metadata`
before Alembic autogenerate or `create_all` runs. Add every new model to this
list as the schema grows across phases.
"""

from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

__all__ = ["RefreshToken", "User", "UserRole"]
