import json
import pytest
from decimal import Decimal
from pathlib import Path

from providers.pacheco import PachecoProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pacheco_search.json"


@pytest.fixture
def pacheco_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def provider():
    return PachecoProvider()


def test_parse_product_basic(provider, pacheco_data):
    product_data = pacheco_data["products"][0]
    candidate = provider._parse_product(product_data)

    assert candidate is not None
    assert candidate.external_id == "841188"
    assert "Dipirona" in candidate.name
    assert candidate.brand == "Cimed"
    assert candidate.ean == "7896422506528"
    assert candidate.pharmacy == "pacheco"


def test_parse_product_specifications(provider, pacheco_data):
    product_data = pacheco_data["products"][0]
    candidate = provider._parse_product(product_data)

    assert candidate is not None
    assert candidate.active_ingredient == "Dipirona Monoidratada"
    assert candidate.dosage == "1g"


def test_parse_offer_price(provider, pacheco_data):
    from datetime import datetime, timezone
    product_data = pacheco_data["products"][0]
    now = datetime.now(timezone.utc)
    offer = provider._parse_offer(product_data, now)

    assert offer is not None
    assert offer.price == Decimal("7.99")
    assert offer.list_price == Decimal("30.56")
    assert offer.available is True
    assert offer.pharmacy == "pacheco"


def test_parse_product_missing_id(provider):
    result = provider._parse_product({})
    assert result is None


def test_parse_multiple_products(provider, pacheco_data):
    candidates = [provider._parse_product(p) for p in pacheco_data["products"]]
    candidates = [c for c in candidates if c is not None]
    assert len(candidates) == 2

    assert candidates[0].dosage == "1g"
    assert candidates[1].brand == "EMS"
