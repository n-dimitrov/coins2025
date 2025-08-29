from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.bigquery_service import BigQueryService, get_bigquery_service as get_bq_provider
from app.services.group_service import GroupService
from app.models.coin import CoinResponse, CoinListResponse, StatsResponse, FilterOptions, Coin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coins")
bigquery_service = get_bq_provider()
group_service = GroupService()

@router.get("/", response_model=CoinListResponse)
async def get_coins(
    coin_type: Optional[str] = Query(None, description="Filter by coin type (RE/CC)"),
    value: Optional[float] = Query(None, description="Filter by coin value"),
    country: Optional[str] = Query(None, description="Filter by country"),
    commemorative: Optional[str] = Query(None, description="Filter by commemorative series"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(20, ge=1, le=2000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Get coins with optional filters."""
    try:
        filters = {}
        if coin_type:
            filters['coin_type'] = coin_type
        if value:
            filters['value'] = value
        if country:
            filters['country'] = country
        if commemorative:
            filters['series'] = commemorative

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

@router.get("/group/{group_name}", response_model=CoinListResponse)
async def get_group_coins(
    group_name: str,
    coin_type: Optional[str] = Query(None, description="Filter by coin type (RE/CC)"),
    value: Optional[float] = Query(None, description="Filter by coin value"),
    country: Optional[str] = Query(None, description="Filter by country"),
    commemorative: Optional[str] = Query(None, description="Filter by commemorative series"),
    owned_by: Optional[str] = Query(None, description="Filter by owner name"),
    ownership_status: Optional[str] = Query(None, description="Filter by ownership status (owned/missing)"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(20, ge=1, le=2000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Get coins with ownership information for a specific group."""
    try:
        # Validate group
        group_context = await group_service.get_group_context(group_name)
        if not group_context:
            raise HTTPException(status_code=404, detail="Group not found")
        
        filters = {}
        if coin_type:
            filters['coin_type'] = coin_type
        if value:
            filters['value'] = value
        if country:
            filters['country'] = country
        if commemorative:
            filters['series'] = commemorative
        if owned_by:
            filters['owned_by'] = owned_by
        if ownership_status:
            filters['ownership_status'] = ownership_status

        coins_data = await group_service.get_group_coins(
            group_context['id'], filters, limit, offset
        )
        
        # Convert to Pydantic models with ownership info
        coins = []
        for coin_data in coins_data:
            coin_dict = dict(coin_data)
            # Handle owners array (defensively coerce NULL aliases to a string)
            owners = []
            # Build a set of canonical member names for defensive filtering
            member_names = set()
            if group_context and group_context.get('members'):
                for m in group_context['members']:
                    if isinstance(m, dict):
                        candidate = m.get('user') or m.get('name')
                    else:
                        candidate = m
                    if candidate:
                        member_names.add(str(candidate).strip().lower())

            if 'owners' in coin_dict and coin_dict['owners']:
                for owner in coin_dict['owners']:
                    if not owner:
                        # Skip null owner entries
                        continue
                    owner_dict = dict(owner)
                    # Pydantic Owner.alias requires a string. If alias is None
                    # (NULL coming from BigQuery), fallback to the owner name
                    # or an empty string to satisfy validation.
                    if owner_dict.get('alias') is None:
                        owner_dict['alias'] = owner_dict.get('owner') or owner_dict.get('name') or ''

                    # Defensive: only include owners that are actual members of the group
                    owner_name = (owner_dict.get('owner') or owner_dict.get('name') or '')
                    if member_names:
                        if str(owner_name).strip().lower() in member_names:
                            owners.append(owner_dict)
                        else:
                            # skip non-member owner
                            continue
                    else:
                        # No member list available; include owner (backwards-compatible)
                        owners.append(owner_dict)

            coin_dict['owners'] = owners
            coin_dict['is_owned'] = len(owners) > 0

            coins.append(Coin(**coin_dict))
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group coins for {group_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
