from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.bigquery_service import BigQueryService
from app.models.coin import CoinResponse, CoinListResponse, StatsResponse, FilterOptions, Coin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coins")
bigquery_service = BigQueryService()

@router.get("/", response_model=CoinListResponse)
async def get_coins(
    coin_type: Optional[str] = Query(None, description="Filter by coin type (RE/CC)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    year: Optional[int] = Query(None, description="Filter by year"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Get coins with optional filters."""
    try:
        filters = {}
        if coin_type:
            filters['coin_type'] = coin_type
        if country:
            filters['country'] = country
        if year:
            filters['year'] = year

        coins_data = await bigquery_service.get_coins(filters, limit, offset)
        
        # Convert to Pydantic models
        coins = [Coin(**coin_data) for coin_data in coins_data]
        
        # Client-side search if needed
        if search and coins:
            search_lower = search.lower()
            coins = [
                coin for coin in coins 
                if search_lower in coin.country.lower() or 
                   (coin.feature and search_lower in coin.feature.lower())
            ]

        return CoinListResponse(
            coins=coins,
            total=len(coins),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error getting coins: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get collection statistics."""
    try:
        stats = await bigquery_service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/filters", response_model=FilterOptions)
async def get_filter_options():
    """Get available filter options."""
    try:
        options = await bigquery_service.get_filter_options()
        return FilterOptions(**options)
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{coin_id}", response_model=CoinResponse)
async def get_coin(coin_id: str):
    """Get a specific coin by ID."""
    try:
        coin_data = await bigquery_service.get_coin_by_id(coin_id)
        if not coin_data:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        coin = Coin(**coin_data)
        return CoinResponse(coin=coin)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coin {coin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
