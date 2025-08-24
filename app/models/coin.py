from pydantic import BaseModel
from typing import List, Optional

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
