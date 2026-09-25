import json
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

from providers.raia import RaiaProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "raia_graphql.json"


@pytest.fixture
def graphql_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def provider():
    return RaiaProvider()


@pytest.fixture
def now():
    return datetime.now(timezone.utc)


def test_parse_offer_with_lmpm(provider, graphql_data, now):
    items = graphql_data["data"]["productsBySkuList"]
    item = items[0]
    offer = provider._graphql_to_offer(item, now)

    assert offer is not None
    assert offer.external_id == "59568"
    assert offer.price == Decimal("5.99")
    assert offer.list_price == Decimal("9.55")
    assert offer.available is True
    assert offer.promotion_type == "LMPM"
    assert offer.promotion_quantity == 3
    assert offer.promotion_price == Decimal("4.99")
    assert offer.pharmacy == "raia"


def test_lmpm_price_is_not_base_price(provider, graphql_data, now):
    items = graphql_data["data"]["productsBySkuList"]
    item = items[0]
    offer = provider._graphql_to_offer(item, now)

    assert offer is not None
    assert offer.price == Decimal("5.99")
    assert offer.promotion_price == Decimal("4.99")
    assert offer.price != offer.promotion_price


def test_parse_regular_offer(provider, graphql_data, now):
    items = graphql_data["data"]["productsBySkuList"]
    item = items[1]
    offer = provider._graphql_to_offer(item, now)

    assert offer is not None
    assert offer.external_id == "824264"
    assert offer.price == Decimal("9.99")
    assert offer.promotion_type is None
    assert offer.promotion_price is None


def test_stock_availability(provider, graphql_data, now):
    items = graphql_data["data"]["productsBySkuList"]
    item = items[0]
    offer = provider._graphql_to_offer(item, now)
    assert offer.available is True


def test_url_construction(provider, graphql_data, now):
    items = graphql_data["data"]["productsBySkuList"]
    item = items[0]
    offer = provider._graphql_to_offer(item, now)
    assert offer.url and "drogaraia.com.br" in offer.url
