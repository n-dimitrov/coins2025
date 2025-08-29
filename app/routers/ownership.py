from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
import logging

from app.models.ownership import OwnershipAdd, OwnershipRemove, OwnershipRecord, OwnershipResponse
from app.services.bigquery_service import BigQueryService
from app.services.group_service import GroupService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ownership", tags=["ownership"])

# Dependency to get BigQuery service
def get_bigquery_service() -> BigQueryService:
    return BigQueryService()

def get_group_service() -> GroupService:
    return GroupService()

@router.post("/add", response_model=OwnershipResponse, status_code=status.HTTP_201_CREATED)
async def add_coin_ownership(
    ownership: OwnershipAdd,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Add coin to user's collection."""
    try:
        # Validate coin exists in catalog
        coin_query = f"""
        SELECT coin_id FROM `{bigquery_service.client.project}.{bigquery_service.dataset_id}.{bigquery_service.table_id}`
        WHERE coin_id = @coin_id
        """
        coin_results = await bigquery_service._get_cached_or_query(coin_query, {'coin_id': ownership.coin_id})
        if not coin_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coin {ownership.coin_id} not found in catalog"
            )
        
        # Add ownership record
        record_id = await bigquery_service.add_coin_ownership(
            name=ownership.name,
            coin_id=ownership.coin_id,
            date=ownership.date,
            created_by=ownership.created_by
        )
        
        logger.info(f"Added ownership: {ownership.name} -> {ownership.coin_id}")
        return OwnershipResponse(
            message="Ownership added successfully",
            id=record_id,
            success=True
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding ownership: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add ownership"
        )

@router.post("/remove", response_model=OwnershipResponse, status_code=status.HTTP_200_OK)
async def remove_coin_ownership(
    ownership: OwnershipRemove,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Remove coin from user's collection."""
    try:
        # Remove ownership record
        record_id = await bigquery_service.remove_coin_ownership(
            name=ownership.name,
            coin_id=ownership.coin_id,
            removal_date=ownership.removal_date,
            created_by=ownership.created_by
        )
        
        logger.info(f"Removed ownership: {ownership.name} -> {ownership.coin_id}")
        return OwnershipResponse(
            message="Ownership removed successfully",
            id=record_id,
            success=True
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing ownership: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove ownership"
        )

@router.get("/user/{user_name}/coins")
async def get_user_coins(
    user_name: str,
    group_id: Optional[str] = None,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Get all coins currently owned by a user."""
    try:
        coins = await bigquery_service.get_user_owned_coins(user_name, group_id)
        return {
            "user": user_name,
            "group_id": group_id,
            "coins": coins,
            "total": len(coins)
        }
    except Exception as e:
        logger.error(f"Error getting user coins: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user coins"
        )

@router.get("/coin/{coin_id}/owners")
async def get_coin_owners(
    coin_id: str,
    group_id: Optional[str] = None,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Get current owners of a specific coin."""
    try:
        if group_id:
            owners = await bigquery_service.get_coin_ownership_by_group(coin_id, group_id)
        else:
            owners = await bigquery_service.get_current_coin_ownership(coin_id)
            
        return {
            "coin_id": coin_id,
            "group_id": group_id,
            "owners": owners,
            "total_owners": len(owners)
        }
    except Exception as e:
        logger.error(f"Error getting coin owners: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get coin owners"
        )

@router.get("/user/{user_name}/history")
async def get_user_ownership_history(
    user_name: str,
    group_id: Optional[str] = None,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Get complete ownership history for a user (including removed coins)."""
    try:
        group_join = ""
        group_where = ""
        params = {'name': user_name}
        
        if group_id:
            group_join = f"JOIN `{bigquery_service.client.project}.{bigquery_service.dataset_id}.{settings.bq_group_users_table}` gu ON h.name = gu.user"
            group_where = "AND gu.group_id = @group_id"
            params['group_id'] = group_id
            
        query = f"""
        SELECT 
            h.id,
            h.name,
            h.coin_id,
            h.date,
            h.created_at,
            h.created_by,
            h.is_active,
            c.coin_type,
            c.year,
            c.country,
            c.series,
            c.value
        FROM `{bigquery_service.client.project}.{bigquery_service.dataset_id}.{settings.bq_history_table}` h
        {group_join}
        JOIN `{bigquery_service.client.project}.{bigquery_service.dataset_id}.{bigquery_service.table_id}` c 
            ON h.coin_id = c.coin_id
        WHERE h.name = @name {group_where}
        ORDER BY h.created_at DESC, h.date DESC
        """
        
        history = await bigquery_service._get_cached_or_query(query, params)
        
        return {
            "user": user_name,
            "group_id": group_id,
            "history": history,
            "total_records": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user history"
        )
