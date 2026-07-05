"""ORM models.

Importing the models here ensures they are all registered on `Base.metadata`
before Alembic autogenerate or `create_all` runs. Add every new model to this
list as the schema grows across phases.
"""

from app.models.api_key import ApiKey
from app.models.company import Company
from app.models.customer import Customer
from app.models.product import Product
from app.models.refresh_token import RefreshToken
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.stock_movement import StockMovement, StockMovementReason
from app.models.subscription import PlanTier, Subscription
from app.models.supplier import Supplier
from app.models.user import User, UserRole

__all__ = [
    "ApiKey",
    "Company",
    "Customer",
    "PlanTier",
    "Product",
    "RefreshToken",
    "Sale",
    "SaleItem",
    "SaleStatus",
    "StockMovement",
    "StockMovementReason",
    "Subscription",
    "Supplier",
    "User",
    "UserRole",
]
