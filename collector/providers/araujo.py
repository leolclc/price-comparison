import html
import json
import logging
import re
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider

logger = logging.getLogger("ARAUJO")

BASE_URL = "https://www.araujo.com.br"
SEARCH_URL = f"{BASE_URL}/busca"


class AraujoProvider(PharmacyProvider):
    name = "Araujo"
    slug = "araujo"

    def __init__(self, timeout: float = 15.0, max_retries: int = 3) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9",
            },
            follow_redirects=True,
        )

    async def search(self, term: str) -> list[ProductCandidate]:
        logger.info(f"search term={term}")
        candidates: list[ProductCandidate] = []

        try:
            for attempt in range(self._max_retries):
                try:
                    params = {"q": term, "lang": "pt_BR"}
                    response = await self._client.get(SEARCH_URL, params=params)
                    response.raise_for_status()
                    html_content = response.text
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

            candidates = self._parse_html(html_content)
            logger.info(f"parsed products={len(candidates)}")
        except Exception as e:
            logger.error(f"Unexpected error in search term={term} error={e}")

        return candidates

    async def get_prices(
        self,
        products: list[ProductCandidate],
    ) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        if not products:
            return offers

        term = products[0].name.split()[0] if products[0].name else ""
        try:
            params = {"q": term, "lang": "pt_BR"}
            response = await self._client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            html_content = response.text

            now = datetime.now(timezone.utc)
            seen_ids = {p.external_id for p in products}
            offers = self._parse_html_offers(html_content, seen_ids, now)
        except Exception as e:
            logger.error(f"Error getting prices: {e}")

        return offers

    def _parse_html(self, html_content: str) -> list[ProductCandidate]:
        candidates: list[ProductCandidate] = []
        try:
            soup = BeautifulSoup(html_content, "lxml")
            containers = soup.find_all(
                attrs={"data-gtmga4data": True}
            )

            for container in containers:
                candidate = self._parse_container(container)
                if candidate:
                    candidates.append(candidate)
        except Exception as e:
            logger.error(f"HTML parsing error: {e}")
        return candidates

    def _parse_html_offers(
        self, html_content: str, seen_ids: set[str], now: datetime
    ) -> list[ProductOffer]:
        offers: list[ProductOffer] = []
        try:
            soup = BeautifulSoup(html_content, "lxml")
            containers = soup.find_all(attrs={"data-gtmga4data": True})

            for container in containers:
                gtm_raw = container.get("data-gtmga4data", "")
                pid = container.get("data-pid", "")
                if not pid or str(pid) not in seen_ids:
                    continue

                gtm_data = self._parse_gtm_data(gtm_raw)
                if not gtm_data:
                    continue

                offer = self._gtm_to_offer(gtm_data, str(pid), now)
                if offer:
                    offers.append(offer)
        except Exception as e:
            logger.error(f"HTML offer parsing error: {e}")
        return offers

    def _parse_container(
        self, container: Any
    ) -> ProductCandidate | None:
        try:
            pid = container.get("data-pid", "")
            if not pid:
                return None

            gtm_raw = container.get("data-gtmga4data", "")
            gtm_data = self._parse_gtm_data(gtm_raw)
            if not gtm_data:
                return None

            name = gtm_data.get("item_name", "")
            if not name:
                return None

            url = None
            link = container.find("a", href=True)
            if link:
                href = link["href"]
                url = href if href.startswith("http") else f"{BASE_URL}{href}"

            ean = gtm_data.get("item_ean") or gtm_data.get("ean")

            return ProductCandidate(
                pharmacy=self.slug,
                external_id=str(pid),
                name=name,
                brand=gtm_data.get("item_brand"),
                ean=str(ean) if ean else None,
                url=url,
            )
        except Exception as e:
            logger.warning(f"Failed to parse Araujo container: {e}")
            return None

    def _parse_gtm_data(self, raw: str) -> dict[str, Any] | None:
        if not raw:
            return None
        try:
            unescaped = html.unescape(raw)
            return json.loads(unescaped)
        except (json.JSONDecodeError, ValueError):
            return None

    def _gtm_to_offer(
        self, gtm_data: dict[str, Any], pid: str, now: datetime
    ) -> ProductOffer | None:
        try:
            price = gtm_data.get("price")
            if price is None:
                return None

            price = Decimal(str(price))
            list_price_val = gtm_data.get("item_list_price") or gtm_data.get("list_price")
            list_price = Decimal(str(list_price_val)) if list_price_val else None

            discount_pct = None
            if list_price and list_price > price:
                discount_pct = ((list_price - price) / list_price * 100).quantize(
                    Decimal("0.01")
                )

            return ProductOffer(
                pharmacy=self.slug,
                external_id=pid,
                price=price,
                list_price=list_price,
                available=True,
                discount_percentage=discount_pct,
                collected_at=now,
            )
        except Exception as e:
            logger.warning(f"Failed to create Araujo offer: {e}")
            return None
