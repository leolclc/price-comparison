from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.schemas.offer import OfferSchema


class PriceHistoryPoint(BaseModel):
    model_config = {"from_attributes": True}

    pharmacy_id: int
    pharmacy_name: str
    price: Decimal
    list_price: Decimal | None
    available: bool
    collected_at: datetime


class ProductSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ean: str | None
    name: str
    brand: str | None
    active_ingredient: str | None
    dosage: str | None
    pharmaceutical_form: str | None
    quantity: int | None
    unit: str | None
    offers: list[OfferSchema] = []


class SearchResultSchema(BaseModel):
    query: str
    total: int
    products: list[ProductSchema]
