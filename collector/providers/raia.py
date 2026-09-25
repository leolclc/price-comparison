import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

import httpx

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider

logger = logging.getLogger("RAIA")

BASE_URL = "https://www.drogaraia.com.br"
GRAPHQL_URL = f"{BASE_URL}/api/next/busca/graphql"
SEARCH_URL = f"{BASE_URL}/api/io/_v/api/intelligent-search/product_search/trade-policy/1"

PRODUCT_BY_SKU_QUERY = """
query ProductBySkuList($skuList: [String!]!, $origin: String) {
  productsBySkuList(skuList: $skuList, origin: $origin) {
    sku
    name
    slug
    liveComposition {
      livePrice {
        discountPercentage
        sku
        type
        valueFrom
        valueTo
        lmpmValueTo
        lmpmQty
      }
      liveStock {
        sku
        qty
      }
    }
  }
}
"""


class RaiaProvider(PharmacyProvider):
    name = "Drogaria Raia"
    slug = "raia"

    def __init__(self, timeout: float = 15.0, max_retries: int = 3) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; FarmaCompare/1.0)",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            follow_redirects=True,
        )

    async def search(self, term: str) -> list[ProductCandidate]:
        logger.info(f"search term={term}")
        candidates: list[ProductCandidate] = []

        try:
            for attempt in range(self._max_retries):
                try:
                    params = {"query": term, "count": 48, "page": 1}
                    response = await self._client.get(SEARCH_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 503) and attempt < self._max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)
                        continue
                    logger.error(
                        f"HTTP error status={e.response.status_code} url={SEARCH_URL}"
                    )
                    return candidates
                except httpx.RequestError as e:
                    logger.error(f"Request error url={SEARCH_URL} error={e}")
                    return candidates
            else:
                return candidates

            products_data = data.get("products", [])
            for product in products_data:
                candidate = self._parse_search_product(product)
                if candidate:
                    candidates.append(candidate)

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

        sku_list = [p.external_id for p in products]
        now = datetime.now(timezone.utc)
        offers: list[ProductOffer] = []

        batch_size = 20
        for i in range(0, len(sku_list), batch_size):
            batch = sku_list[i : i + batch_size]
            try:
                graphql_data = await self._fetch_graphql_prices(batch)
                for item in graphql_data:
                    offer = self._graphql_to_offer(item, now)
                    if offer:
                        offers.append(offer)
            except Exception as e:
                logger.error(f"Error getting prices for batch {i}: {e}")

        logger.info(f"price update skus={len(sku_list)} offers={len(offers)}")
        return offers

    async def _fetch_graphql_prices(
        self, sku_list: list[str]
    ) -> list[dict[str, Any]]:
        try:
            payload = {
                "query": PRODUCT_BY_SKU_QUERY,
                "variables": {"skuList": sku_list, "origin": "search"},
            }
            response = await self._client.post(GRAPHQL_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("productsBySkuList", [])
        except Exception as e:
            logger.error(f"GraphQL error: {e}")
            return []

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
