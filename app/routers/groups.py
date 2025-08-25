from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
import logging

from app.models.group import (
    GroupCreate, GroupUpdate, GroupResponse, 
    GroupUserAdd, GroupUserUpdate, GroupUserResponse,
    GroupListResponse, GroupUsersListResponse, ApiResponse
)
from app.services.bigquery_service import BigQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])

# Dependency to get BigQuery service
def get_bigquery_service() -> BigQueryService:
    return BigQueryService()

# Group management endpoints
@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Create a new group."""
    try:
        group_id = await bigquery_service.create_group(group.group_key, group.name)
        
        logger.info(f"Created group: {group.group_key} -> {group.name}")
        return ApiResponse(
            message="Group created successfully",
            success=True,
            id=group_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )

@router.get("/", response_model=GroupListResponse)
async def list_groups(
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """List all active groups."""
    try:
        groups_data = await bigquery_service.list_active_groups()
        groups = [GroupResponse(**group) for group in groups_data]
        
        return GroupListResponse(
            groups=groups,
            total=len(groups)
        )
    except Exception as e:
        logger.error(f"Error listing groups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list groups"
        )

@router.get("/{group_key}", response_model=GroupResponse)
async def get_group(
    group_key: str,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Get group details by group key."""
    try:
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        return GroupResponse(**group_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get group"
        )

@router.put("/{group_key}", response_model=ApiResponse)
async def update_group(
    group_key: str,
    group: GroupUpdate,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Update group information."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Update group
        await bigquery_service.update_group(group_data['id'], group.name)
        
        logger.info(f"Updated group: {group_key} -> {group.name}")
        return ApiResponse(
            message="Group updated successfully",
            success=True,
            id=group_data['id']
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update group"
        )

@router.delete("/{group_key}", response_model=ApiResponse)
async def delete_group(
    group_key: str,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Delete a group (soft delete)."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Delete group
        await bigquery_service.delete_group(group_data['id'])
        
        logger.info(f"Deleted group: {group_key}")
        return ApiResponse(
            message="Group deleted successfully",
            success=True,
            id=group_data['id']
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete group"
        )

# Group user management endpoints
@router.post("/{group_key}/users", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def add_user_to_group(
    group_key: str,
    user: GroupUserAdd,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Add a user to a group."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Add user to group
        user_id = await bigquery_service.add_user_to_group(
            group_data['id'], user.name, user.alias
        )
        
        logger.info(f"Added user to group: {user.name} -> {group_key}")
        return ApiResponse(
            message="User added to group successfully",
            success=True,
            id=user_id
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding user to group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add user to group"
        )

@router.get("/{group_key}/users", response_model=GroupUsersListResponse)
async def get_group_users(
    group_key: str,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Get all users in a group."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Get group users
        users_data = await bigquery_service.get_active_group_users(group_data['id'])
        users = [GroupUserResponse(**user) for user in users_data]
        
        return GroupUsersListResponse(
            users=users,
            total=len(users)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get group users"
        )

@router.put("/{group_key}/users/{user_name}", response_model=ApiResponse)
async def update_group_user(
    group_key: str,
    user_name: str,
    user: GroupUserUpdate,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Update a user in a group."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Update group user
        await bigquery_service.update_group_user(
            group_data['id'], user_name, user.alias
        )
        
        logger.info(f"Updated user in group: {user_name} -> {group_key}")
        return ApiResponse(
            message="User updated successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating group user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update group user"
        )

@router.delete("/{group_key}/users/{user_name}", response_model=ApiResponse)
async def remove_user_from_group(
    group_key: str,
    user_name: str,
    bigquery_service: BigQueryService = Depends(get_bigquery_service)
):
    """Remove a user from a group."""
    try:
        # Get group by key first
        group_data = await bigquery_service.get_group_by_key(group_key)
        if not group_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{group_key}' not found"
            )
        
        # Remove user from group
        await bigquery_service.remove_user_from_group(group_data['id'], user_name)
        
        logger.info(f"Removed user from group: {user_name} -> {group_key}")
        return ApiResponse(
            message="User removed from group successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing user from group: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user from group"
        )
