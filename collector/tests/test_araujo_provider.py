import html
import pytest
from decimal import Decimal
from pathlib import Path

from providers.araujo import AraujoProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "araujo_search.html"


@pytest.fixture
def html_content():
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def provider():
    return AraujoProvider()


def test_parse_html_returns_candidates(provider, html_content):
    candidates = provider._parse_html(html_content)
    assert len(candidates) == 2


def test_parse_first_product(provider, html_content):
    candidates = provider._parse_html(html_content)
    first = candidates[0]

    assert first.external_id == "72248"
    assert "Dipirona" in first.name
    assert first.brand == "Neo Química"
    assert first.pharmacy == "araujo"
    assert "araujo.com.br" in first.url


def test_parse_second_product(provider, html_content):
    candidates = provider._parse_html(html_content)
    second = candidates[1]

    assert second.external_id == "85432"
    assert "500mg" in second.name
    assert second.brand == "EMS"


def test_parse_gtm_data_valid(provider):
    raw = '{&quot;item_name&quot;:&quot;Test&quot;,&quot;price&quot;:9.99}'
    result = provider._parse_gtm_data(raw)
    assert result is not None
    assert result["price"] == 9.99


def test_parse_gtm_data_invalid(provider):
    result = provider._parse_gtm_data("invalid json{")
    assert result is None


def test_gtm_to_offer(provider):
    from datetime import datetime, timezone
    gtm = {"price": 9.99, "item_list_price": 19.99}
    now = datetime.now(timezone.utc)
    offer = provider._gtm_to_offer(gtm, "72248", now)

    assert offer is not None
    assert offer.price == Decimal("9.99")
    assert offer.list_price == Decimal("19.99")
    assert offer.external_id == "72248"


def test_empty_html(provider):
    candidates = provider._parse_html("<html><body></body></html>")
    assert candidates == []
