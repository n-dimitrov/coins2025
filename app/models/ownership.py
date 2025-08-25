from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OwnershipAdd(BaseModel):
    """Model for adding coin ownership."""
    name: str = Field(..., description="Owner name")
    coin_id: str = Field(..., description="Coin identifier")
    date: datetime = Field(..., description="Acquisition date")
    created_by: Optional[str] = Field(None, description="Who added this record")

class OwnershipRemove(BaseModel):
    """Model for removing coin ownership."""
    name: str = Field(..., description="Owner name")
    coin_id: str = Field(..., description="Coin identifier")
    removal_date: datetime = Field(default_factory=datetime.now, description="When ownership ended")
    created_by: Optional[str] = Field(None, description="Who recorded the removal")

class OwnershipRecord(BaseModel):
    """Model for ownership history record."""
    id: str
    name: str
    coin_id: str
    date: datetime
    created_at: datetime
    created_by: Optional[str]
    is_active: bool

class OwnershipResponse(BaseModel):
    """Response model for ownership operations."""
    message: str
    id: Optional[str] = None
    success: bool = True
