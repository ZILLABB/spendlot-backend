"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    receipts,
    transactions,
    categories,
    bank_accounts,
    analytics,
    health,
    webhooks
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(bank_accounts.router, prefix="/bank-accounts", tags=["bank-accounts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
