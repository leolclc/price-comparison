import html
import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider
from providers.browser import BrowserPageFetcher

logger = logging.getLogger("RAIA")

BASE_URL = "https://www.drogaraia.com.br"
SEARCH_URL = f"{BASE_URL}/busca"


class RaiaProvider(PharmacyProvider):
    name = "Drogaria Raia"
    slug = "raia"

    def __init__(self, timeout: float = 45.0) -> None:
        self._browser = BrowserPageFetcher(timeout_seconds=timeout)

    async def _fetch_search_page(self, term: str) -> str:
        query = urlencode({"q": term, "lang": "pt_BR"})
        return await self._browser.fetch_page(
            f"{SEARCH_URL}?{query}",
            wait_for_selector="[data-gtmga4data][data-pid]",
        )

    async def close(self) -> None:
        await self._browser.close()

    async def search(self, term: str) -> list[ProductCandidate]:
        logger.info(f"search term={term}")
        candidates: list[ProductCandidate] = []

        try:
            html_content = await self._fetch_search_page(term)
            candidates = self._parse_html(html_content)

            logger.info(f"search term={term} products={len(candidates)}")
        except Exception as e:
            logger.error(f"Unexpected error in search term={term} error={e}")

        return candidates

    async def get_prices(
        self,
        products: list[ProductCandidate],
    ) -> list[ProductOffer]:
        if not products:
            return []

        now = datetime.now(timezone.utc)
        term = products[0].name.split()[0] if products[0].name else ""
        try:
            html_content = await self._fetch_search_page(term)
            offers = self._parse_html_offers(
                html_content,
                {product.external_id for product in products},
                now,
            )
            logger.info("price update skus=%s offers=%s", len(products), len(offers))
            return offers
        except Exception as e:
            logger.error("Error getting Raia prices: %s", e)
            return []

    def _parse_html(self, html_content: str) -> list[ProductCandidate]:
        candidates: list[ProductCandidate] = []
        soup = BeautifulSoup(html_content, "lxml")
        for container in soup.find_all(attrs={"data-gtmga4data": True}):
            pid = container.get("data-pid", "")
            gtm_data = self._parse_gtm_data(container.get("data-gtmga4data", ""))
            if not pid or not gtm_data:
                continue

            name = gtm_data.get("item_name", "")
            if not name:
                continue

            link = container.find("a", href=True)
            href = link["href"] if link else ""
            url = (
                href
                if href.startswith("http")
                else f"{BASE_URL}{href}"
                if href
                else None
            )
            ean = gtm_data.get("item_ean") or gtm_data.get("ean")
            candidates.append(
                ProductCandidate(
                    pharmacy=self.slug,
                    external_id=str(pid),
                    name=name,
                    brand=gtm_data.get("item_brand"),
                    ean=str(ean) if ean else None,
                    url=url,
                )
            )
        return candidates

    def _parse_html_offers(
        self, html_content: str, seen_ids: set[str], now: datetime
    ) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        soup = BeautifulSoup(html_content, "lxml")
        for container in soup.find_all(attrs={"data-gtmga4data": True}):
            pid = str(container.get("data-pid", ""))
            if not pid or pid not in seen_ids:
                continue
            gtm_data = self._parse_gtm_data(container.get("data-gtmga4data", ""))
            if not gtm_data:
                continue
            offer = self._gtm_to_offer(gtm_data, pid, now)
            if offer:
                offers.append(offer)
        return offers

    def _parse_gtm_data(self, raw: str) -> dict[str, Any] | None:
        if not raw:
            return None
        try:
            return json.loads(html.unescape(raw))
        except (json.JSONDecodeError, ValueError):
            return None

    def _gtm_to_offer(
        self, gtm_data: dict[str, Any], pid: str, now: datetime
    ) -> ProductOffer | None:
        price = gtm_data.get("price")
        if price is None:
            return None

        try:
            price = Decimal(str(price))
            list_price_value = gtm_data.get("item_list_price") or gtm_data.get(
                "list_price"
            )
            list_price = Decimal(str(list_price_value)) if list_price_value else None
            discount = None
            if list_price and list_price > price:
                discount = ((list_price - price) / list_price * 100).quantize(
                    Decimal("0.01")
                )
            return ProductOffer(
                pharmacy=self.slug,
                external_id=pid,
                price=price,
                list_price=list_price,
                available=True,
                discount_percentage=discount,
                collected_at=now,
            )
        except (ArithmeticError, ValueError, TypeError) as e:
            logger.warning("Failed to parse Raia offer for %s: %s", pid, e)
            return None

    def _parse_search_product(
        self, product: dict[str, Any]
    ) -> ProductCandidate | None:
        try:
            items = product.get("items", [])
            if not items:
                return None

            sku = str(items[0].get("itemId", ""))
            if not sku:
                return None

            name = product.get("productName") or product.get("description", "")
            if not name:
                return None

            ean = items[0].get("ean")
            link_text = product.get("linkText", "")
            url = f"{BASE_URL}/{link_text}/p" if link_text else None

            return ProductCandidate(
                pharmacy=self.slug,
                external_id=sku,
                name=name,
                brand=product.get("brand"),
                ean=str(ean) if ean else None,
                url=url,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Raia search product: {e}")
            return None

    def _graphql_to_offer(
        self, item: dict[str, Any], now: datetime
    ) -> ProductOffer | None:
        try:
            sku = str(item.get("sku", ""))
            if not sku:
                return None

            live_comp = item.get("liveComposition", {})
            live_price = live_comp.get("livePrice", {})
            live_stock = live_comp.get("liveStock", {})

            if not live_price:
                return None

            value_from = live_price.get("valueFrom")
            value_to = live_price.get("valueTo")
            lmpm_value_to = live_price.get("lmpmValueTo")
            lmpm_qty = live_price.get("lmpmQty")
            discount_pct = live_price.get("discountPercentage")
            price_type = live_price.get("type")

            stock_qty = live_stock.get("qty", 0)
            available = stock_qty > 0 if stock_qty is not None else True

            price = value_to if value_to is not None else value_from
            if price is None:
                return None

            price = Decimal(str(price))
            list_price = Decimal(str(value_from)) if value_from else None

            promotion_type = None
            promotion_quantity = None
            promotion_price = None

            if lmpm_value_to and lmpm_qty:
                promotion_type = price_type or "LMPM"
                try:
                    promotion_quantity = int(lmpm_qty)
                    promotion_price = Decimal(str(lmpm_value_to))
                except (ValueError, TypeError):
                    pass

            slug = item.get("slug", "")
            url = f"{BASE_URL}/{slug}/p" if slug else None

            return ProductOffer(
                pharmacy=self.slug,
                external_id=sku,
                price=price,
                list_price=list_price,
                price_without_discount=list_price,
                available=available,
                discount_percentage=(
                    Decimal(str(discount_pct)) if discount_pct else None
                ),
                promotion_type=promotion_type,
                promotion_quantity=promotion_quantity,
                promotion_price=promotion_price,
                url=url,
                collected_at=now,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Raia GraphQL offer: {e}")
            return None
