from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class PromotionSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    type: str
    description: str | None
    minimum_quantity: int | None
    promotion_price: Decimal | None


class OfferSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    pharmacy_id: int
    pharmacy_name: str
    pharmacy_slug: str
    price: Decimal
    list_price: Decimal | None
    price_without_discount: Decimal | None
    discount_percent: Decimal | None
    available: bool
    collected_at: datetime
    external_url: str | None
    promotions: list[PromotionSchema] = []
