from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class ProductCandidate:
    pharmacy: str
    external_id: str
    name: str
    brand: str | None = None
    ean: str | None = None

    dosage: str | None = None
    pharmaceutical_form: str | None = None
    quantity: int | None = None
    unit: str | None = None

    active_ingredient: str | None = None

    url: str | None = None


@dataclass
class ProductOffer:
    pharmacy: str
    external_id: str

    price: Decimal
    list_price: Decimal | None = None
    price_without_discount: Decimal | None = None

    available: bool = True

    discount_percentage: Decimal | None = None

    promotion_type: str | None = None
    promotion_quantity: int | None = None
    promotion_price: Decimal | None = None

    url: str | None = None

    collected_at: datetime = field(default_factory=lambda: datetime.now())
