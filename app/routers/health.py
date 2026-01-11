from fastapi import APIRouter
from app.services.neon_service import get_neon_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "My EuroCoins API"}

@router.get("/ready")
async def readiness_check():
    """Readiness check - this can be more complex."""
    return {"status": "ready", "service": "My EuroCoins API"}

@router.get("/health/database")
async def database_health():
    """Check Neon PostgreSQL connection."""
    try:
        service = get_neon_service()
        stats = await service.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "total_coins": stats.get("total_coins", 0)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
