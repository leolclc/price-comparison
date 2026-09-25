import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

import httpx

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider

logger = logging.getLogger("PACHECO")

BASE_URL = "https://www.drogariaspacheco.com.br"
SEARCH_URL = (
    f"{BASE_URL}/api/io/_v/api/intelligent-search/product_search/trade-policy/1"
)


class PachecoProvider(PharmacyProvider):
    name = "Drogaria Pacheco"
    slug = "pacheco"

    def __init__(self, timeout: float = 15.0, max_retries: int = 3) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; FarmaCompare/1.0)",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )

    async def search(self, term: str) -> list[ProductCandidate]:
        logger.info(f"search term={term}")
        candidates: list[ProductCandidate] = []
        page = 1
        count = 48

        try:
            for attempt in range(self._max_retries):
                try:
                    params = {"query": term, "count": count, "page": page}
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
        now = datetime.now(timezone.utc)

        for candidate in products:
            try:
                params = {"query": candidate.name, "count": 10, "page": 1}
                response = await self._client.get(SEARCH_URL, params=params)
                response.raise_for_status()
                data = response.json()

                for product in data.get("products", []):
                    if str(product.get("productId")) == candidate.external_id:
                        offer = self._parse_offer(product, now)
                        if offer:
                            offers.append(offer)
                        break
            except Exception as e:
                logger.error(f"Error getting price for {candidate.external_id}: {e}")

        return offers

    def _parse_product(self, product: dict[str, Any]) -> ProductCandidate | None:
        try:
            product_id = str(product.get("productId", ""))
            if not product_id:
                return None

            name = product.get("productName") or product.get("description", "")
            if not name:
                return None

            link_text = product.get("linkText", "")
            url = f"{BASE_URL}/{link_text}/p" if link_text else None

            ean = None
            items = product.get("items", [])
            if items:
                ean = items[0].get("ean")

            dosage = None
            pharmaceutical_form = None
            quantity = None
            unit = None
            active_ingredient = None

            specs = product.get("specificationGroups", [])
            for group in specs:
                for spec in group.get("specifications", []):
                    spec_name = spec.get("originalName", "").lower()
                    spec_values = spec.get("values", [])
                    if not spec_values:
                        continue
                    val = spec_values[0]

                    if "princ" in spec_name and "ativo" in spec_name:
                        active_ingredient = val
                    elif "dosagem" in spec_name or "concentra" in spec_name:
                        dosage = val
                    elif "forma" in spec_name and ("farm" in spec_name or "admin" in spec_name):
                        pharmaceutical_form = val
                    elif "quantidade" in spec_name or "unidades" in spec_name:
                        try:
                            quantity = int("".join(filter(str.isdigit, val)))
                        except (ValueError, TypeError):
                            pass

            return ProductCandidate(
                pharmacy=self.slug,
                external_id=product_id,
                name=name,
                brand=product.get("brand"),
                ean=str(ean) if ean else None,
                dosage=dosage,
                pharmaceutical_form=pharmaceutical_form,
                quantity=quantity,
                unit=unit,
                active_ingredient=active_ingredient,
                url=url,
            )
        except Exception as e:
            logger.warning(f"Failed to parse product: {e}")
            return None

    def _parse_offer(self, product: dict[str, Any], now: datetime) -> ProductOffer | None:
        try:
            product_id = str(product.get("productId", ""))
            if not product_id:
                return None

            price_range = product.get("priceRange", {})
            selling = price_range.get("sellingPrice", {})
            list_pr = price_range.get("listPrice", {})

            price = selling.get("lowPrice") or selling.get("highPrice")
            if price is None:
                return None

            list_price_val = list_pr.get("lowPrice") or list_pr.get("highPrice")

            price = Decimal(str(price))
            list_price = Decimal(str(list_price_val)) if list_price_val else None

            discount_pct = None
            if list_price and list_price > price:
                discount_pct = ((list_price - price) / list_price * 100).quantize(
                    Decimal("0.01")
                )

            link_text = product.get("linkText", "")
            url = f"{BASE_URL}/{link_text}/p" if link_text else None

            return ProductOffer(
                pharmacy=self.slug,
                external_id=product_id,
                price=price,
                list_price=list_price,
                price_without_discount=list_price,
                available=True,
                discount_percentage=discount_pct,
                url=url,
                collected_at=now,
            )
        except Exception as e:
            logger.warning(f"Failed to parse offer: {e}")
            return None
