from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, Dict

class ExchangeResultSchema(BaseModel):
    result: str
    documentation: str
    terms_of_use: str
    time_last_update_unix: int
    time_last_update_utc: str
    time_next_update_unix: int
    time_next_update_utc: str
    base_code: str
    conversion_rates: dict[str, float]

# https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,notcoin&price_change_percentage=14d,30d
class CoingeckoMarketCoin(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: Decimal
    market_cap: Decimal
    price_change_percentage_24h: Optional[Decimal] = Field(None)
    total_volume: Decimal
    high_24h: Optional[Decimal] = Field(None)
    low_24h: Optional[Decimal] = Field(None)
    total_supply: Optional[Decimal] = Field(None)
    max_supply: Optional[Decimal] = Field(None)
    ath: Decimal
    price_change_percentage_7d_in_currency: Optional[Decimal] = None
    price_change_percentage_14d_in_currency: Optional[Decimal] = None
    price_change_percentage_30d_in_currency: Optional[Decimal] = None
    price_change_percentage_1y_in_currency: Optional[Decimal] = None