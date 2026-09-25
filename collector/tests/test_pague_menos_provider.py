import json
import pytest
from decimal import Decimal
from pathlib import Path

from providers.pague_menos import PagueMenosProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pague_menos_search.json"


@pytest.fixture
def data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def provider():
    return PagueMenosProvider()


def test_parse_product(provider, data):
    product_data = data["products"][0]
    candidate = provider._parse_product(product_data)

    assert candidate is not None
    assert candidate.external_id == "999001"
    assert "Dipirona" in candidate.name
    assert candidate.brand == "Neo Química"
    assert candidate.ean == "7896714240102"
    assert candidate.pharmacy == "pague-menos"


def test_parse_offer(provider, data):
    from datetime import datetime, timezone
    product_data = data["products"][0]
    now = datetime.now(timezone.utc)
    offer = provider._parse_offer(product_data, now)

    assert offer is not None
    assert offer.price == Decimal("8.89")
    assert offer.list_price == Decimal("29.52")
    assert offer.discount_percentage == Decimal("70")
    assert offer.available is True
    assert offer.pharmacy == "pague-menos"


def test_parse_offer_promotion(provider, data):
    from datetime import datetime, timezone
    product_data = data["products"][0]
    now = datetime.now(timezone.utc)
    offer = provider._parse_offer(product_data, now)

    assert offer is not None
    assert offer.promotion_type == "QUANTITY_DISCOUNT"
    assert offer.promotion_quantity == 2
    assert offer.promotion_price == Decimal("7.99")


def test_parse_product_missing_id(provider):
    result = provider._parse_product({})
    assert result is None
