from pydantic import BaseModel, Field
from typing import Optional, List

class GroupCreate(BaseModel):
    """Model for creating a new group."""
    group_key: str = Field(..., description="Unique group identifier (URL-friendly)")
    name: str = Field(..., description="Group display name")

class GroupUpdate(BaseModel):
    """Model for updating a group."""
    name: str = Field(..., description="Updated group name")

class GroupResponse(BaseModel):
    """Model for group data response."""
    id: str
    group_key: str
    name: str
    is_active: bool

class GroupUserAdd(BaseModel):
    """Model for adding a user to a group."""
    name: str = Field(..., description="User name")
    alias: str = Field(..., description="User display name")

class GroupUserUpdate(BaseModel):
    """Model for updating a group user."""
    alias: str = Field(..., description="Updated user alias")

class GroupUserResponse(BaseModel):
    """Model for group user data response."""
    id: str
    group_id: str
    name: str
    alias: str
    is_active: bool

class GroupListResponse(BaseModel):
    """Model for listing groups."""
    groups: List[GroupResponse]
    total: int

class GroupUsersListResponse(BaseModel):
    """Model for listing group users."""
    users: List[GroupUserResponse]
    total: int

class ApiResponse(BaseModel):
    """Generic API response model."""
    message: str
    success: bool = True
    id: Optional[str] = None
