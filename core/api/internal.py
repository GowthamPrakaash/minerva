"""
core/api/internal.py — Operations and monitoring endpoints.
"""

import uuid
from fastapi import APIRouter, Response, status
from shared.config.config_cache import ConfigCache
from shared.db.connection import DBConnectionPool
from shared.utils.logging import get_logger

logger = get_logger("core.api.internal")
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/health")
async def health_check():
    """Service health status."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "db_connected": DBConnectionPool.get_instance().is_initialized()
    }


@router.post("/cache/refresh")
async def refresh_cache():
    """Manually trigger a full refresh of the ConfigCache."""
    cache = ConfigCache.get_instance()
    await cache.refresh_all()
    logger.info("Internal: ConfigCache manually refreshed.")
    return {"status": "success", "message": "Cache refreshed"}


@router.post("/cache/invalidate/{business_id}")
async def invalidate_business_cache(business_id: uuid.UUID):
    """Invalidate cache for a specific business."""
    cache = ConfigCache.get_instance()
    await cache.invalidate(business_id)
    return {"status": "success", "business_id": str(business_id)}
