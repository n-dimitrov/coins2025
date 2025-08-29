from fastapi import APIRouter
from app.services.bigquery_service import BigQueryService, get_bigquery_service as get_bq_provider
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

@router.get("/health/bigquery")
async def bigquery_health():
    """Check BigQuery connection."""
    try:
        service = get_bq_provider()
        stats = await service.get_stats()
        return {
            "status": "healthy",
            "bigquery": "connected",
            "total_coins": stats.get("total_coins", 0)
        }
    except Exception as e:
        logger.error(f"BigQuery health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "bigquery": "disconnected",
            "error": str(e)
        }
