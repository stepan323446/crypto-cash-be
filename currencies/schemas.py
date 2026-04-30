from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional

class FaqScheme(BaseModel):
    question: str
    answer: str

class StaticExtraDataSchema(BaseModel):
    faq: list[FaqScheme] = []

class PriceHistoryPercentage(BaseModel):
    percentage_7d: Optional[Decimal] = Field(None)
    percentage_14d: Optional[Decimal] = Field(None)
    percentage_30d: Optional[Decimal] = Field(None)
    percentage_1y: Optional[Decimal] = Field(None)

class DynamicExtraDataSchema(BaseModel):
    range_24h: tuple[Decimal, Decimal] = (Decimal(0), Decimal(0))
    ath: Decimal = Decimal(0)
    total_supply: Optional[Decimal] = Field(None)
    max_supply: Optional[Decimal] = Field(None)
    price_history: Optional[PriceHistoryPercentage] = None