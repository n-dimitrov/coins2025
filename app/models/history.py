from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class History(BaseModel):
    name: str
    id: str  # coin_id
    date: datetime
    
    class Config:
        from_attributes = True

class HistoryCreate(BaseModel):
    name: str
    id: str
    date: datetime

class HistoryUpdate(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    date: Optional[datetime] = None
