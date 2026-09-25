import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

import httpx

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider

logger = logging.getLogger("PAGUE_MENOS")

BASE_URL = "https://www.paguemenos.com.br"
SEARCH_URL = "https://prod.apipmenos.com/buscacatalogo/api/searchurl"


class PagueMenosProvider(PharmacyProvider):
    name = "Pague Menos"
    slug = "pague-menos"

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
                    payload = {
                        "searchUrl": f"/busca?q={term}&map=ft",
                    }
                    response = await self._client.post(SEARCH_URL, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 503) and attempt < self._max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)
                        continue
                    logger.warning(
                        f"HTTP {e.response.status_code} at {SEARCH_URL}, attempting public VTEX fallback..."
                    )
                    # Fallback to public VTEX intelligent-search endpoint
                    vtex_url = f"{BASE_URL}/api/io/_v/api/intelligent-search/product_search/trade-policy/1"
                    try:
                        vtex_resp = await self._client.get(
                            vtex_url, params={"query": term, "count": 48, "page": 1}
                        )
                        vtex_resp.raise_for_status()
                        data = vtex_resp.json()
                        break
                    except Exception as fallback_err:
                        logger.error(f"Fallback to {vtex_url} also failed: {fallback_err}")
                        return candidates
                except httpx.RequestError as e:
                    logger.error(f"Request error url={SEARCH_URL} error={e}")
                    return candidates
            else:
                return candidates

            products_data = data.get("products", []) if isinstance(data, dict) else []
            if not products_data:
                products_data = data if isinstance(data, list) else []

            for product in products_data:
                candidate = self._parse_product(product)
                if candidate:
                    candidates.append(candidate)

            logger.info(f"search term={term} products={len(candidates)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error url={SEARCH_URL} error={e}")
        except Exception as e:
            logger.error(f"Unexpected error in search term={term} error={e}")

        return candidates

    async def get_prices(
        self,
        products: list[ProductCandidate],
    ) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        seen_ids = {p.external_id for p in products}

        if not products:
            return offers

        first_name = products[0].name.split()[0] if products[0].name else ""
        try:
            payload = {"searchUrl": f"/busca?q={first_name}&map=ft"}
            response = await self._client.post(SEARCH_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            products_data = data.get("products", []) if isinstance(data, dict) else []
            now = datetime.now(timezone.utc)

            for product in products_data:
                sku_id = self._get_sku_id(product)
                if sku_id and sku_id in seen_ids:
                    offer = self._parse_offer(product, now)
                    if offer:
                        offers.append(offer)
        except Exception as e:
            logger.error(f"Error getting prices: {e}")

        return offers

    def _get_sku_id(self, product: dict[str, Any]) -> str | None:
        items = product.get("items", [])
        if items:
            sellers = items[0].get("sellers", [])
            if sellers:
                return str(sellers[0].get("sellerId", "") or items[0].get("itemId", ""))
        return str(product.get("productId", "")) or None

    def _parse_product(self, product: dict[str, Any]) -> ProductCandidate | None:
        try:
            product_id = str(product.get("productId", ""))
            if not product_id:
                return None

            name = product.get("productName") or product.get("description", "")
            if not name:
                return None

            link = product.get("link", "")
            url = f"{BASE_URL}{link}" if link else None

            ean = None
            brand = product.get("brand")
            items = product.get("items", [])
            if items:
                ean = items[0].get("ean")

            return ProductCandidate(
                pharmacy=self.slug,
                external_id=product_id,
                name=name,
                brand=brand,
                ean=str(ean) if ean else None,
                url=url,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Pague Menos product: {e}")
            return None

    def _parse_offer(self, product: dict[str, Any], now: datetime) -> ProductOffer | None:
        try:
            product_id = str(product.get("productId", ""))
            if not product_id:
                return None

            items = product.get("items", [])
            if not items:
                return None

            sellers = items[0].get("sellers", [])
            if not sellers:
                return None

            seller = None
            for s in sellers:
                if s.get("sellerDefault") or s.get("sellerId") == "1":
                    seller = s
                    break
            if not seller:
                seller = sellers[0]

            offer_data = seller.get("commertialOffer", {})
            price = offer_data.get("price") or offer_data.get("Price")
            if price is None:
                return None

            list_price_val = offer_data.get("listPrice") or offer_data.get("ListPrice")
            price_without_discount = offer_data.get("priceWithoutDiscount")
            discount = offer_data.get("discount") or offer_data.get("Discount")
            available_qty = offer_data.get("AvailableQuantity", 1)

            promotion_type = None
            promotion_quantity = None
            promotion_price = None

            teasers = offer_data.get("teasers", [])
            if teasers:
                teaser = teasers[0]
                conditions = teaser.get("conditions", {})
                effects = teaser.get("effects", {})
                min_qty = conditions.get("minimumQuantityKBackingField")
                if min_qty:
                    promotion_type = "QUANTITY_DISCOUNT"
                    try:
                        promotion_quantity = int(min_qty)
                    except (ValueError, TypeError):
                        pass
                promo_price = effects.get("discountKBackingField")
                if promo_price:
                    try:
                        promotion_price = Decimal(str(promo_price))
                    except Exception:
                        pass

            link = product.get("link", "")
            url = f"{BASE_URL}{link}" if link else None

            return ProductOffer(
                pharmacy=self.slug,
                external_id=product_id,
                price=Decimal(str(price)),
                list_price=Decimal(str(list_price_val)) if list_price_val else None,
                price_without_discount=(
                    Decimal(str(price_without_discount))
                    if price_without_discount
                    else None
                ),
                available=available_qty > 0,
                discount_percentage=Decimal(str(discount)) if discount else None,
                promotion_type=promotion_type,
                promotion_quantity=promotion_quantity,
                promotion_price=promotion_price,
                url=url,
                collected_at=now,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Pague Menos offer: {e}")
            return None
