from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Owner(BaseModel):
    owner: str
    alias: str
    acquired_date: Optional[datetime] = None

class Coin(BaseModel):
    coin_type: str
    year: int
    country: str
    series: str
    value: float
    coin_id: str
    image_url: Optional[str] = None
    feature: Optional[str] = None
    volume: Optional[str] = None
    owners: Optional[List[Owner]] = []
    is_owned: Optional[bool] = False

class CoinResponse(BaseModel):
    coin: Coin

class CoinListResponse(BaseModel):
    coins: List[Coin]
    total: int
    limit: int
    offset: int

class StatsResponse(BaseModel):
    total_coins: int
    total_countries: int
    regular_coins: int
    commemorative_coins: int

class FilterOptions(BaseModel):
    countries: List[str]
    commemoratives: List[str]
    denominations: List[float]
