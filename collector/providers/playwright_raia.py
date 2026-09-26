import logging
from datetime import datetime, timezone
from decimal import Decimal

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from models.common import ProductCandidate, ProductOffer
from providers.base import PharmacyProvider

log = logging.getLogger('PlaywrightRaia')

BASE_URL = 'https://www.raia.com.br'
SEARCH_URL = f'{BASE_URL}/busca'

class PlaywrightRaiaProvider(PharmacyProvider):
    name = 'Raia'
    slug = 'raia'

    async def _fetch_page(self, term: str) -> str:
        async def attempt_fetch(attempt: int) -> str:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
                context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                page = await context.new_page()
                url = f'{SEARCH_URL}?q={term}&lang=pt_BR'
                try:
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                    await page.wait_for_selector('[data-gtmga4data]', timeout=30000)
                    html = await page.content()
                finally:
                    await context.close()
                    await browser.close()
                return html
        for attempt in range(3):
            try:
                return await attempt_fetch(attempt)
            except Exception as e:
                log.warning(f'Playwright fetch attempt {attempt+1} failed: {e}')
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def search(self, term: str) -> list[ProductCandidate]:
        log.info('search term=%s', term)
        html = await self._fetch_page(term)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[ProductCandidate] = []
        for container in soup.find_all(attrs={'data-gtmga4data': True}):
            pid = container.get('data-pid')
            if not pid:
                continue
            gtm_raw = container.get('data-gtmga4data', '')
            gtm = self._parse_gtm_data(gtm_raw)
            if not gtm:
                continue
            name = gtm.get('item_name') or ''
            if not name:
                continue
            # Extract URL if present
            link = container.find('a', href=True)
            url = None
            if link:
                href = link['href']
                url = href if href.startswith('http') else f'{BASE_URL}{href}'
            ean = gtm.get('item_ean') or gtm.get('ean')
            candidates.append(
                ProductCandidate(
                    pharmacy=self.slug,
                    external_id=str(pid),
                    name=name,
                    brand=gtm.get('item_brand'),
                    ean=str(ean) if ean else None,
                    url=url,
                )
            )
        return candidates

    async def get_prices(self, products: list[ProductCandidate]) -> list[ProductOffer]:
        if not products:
            return []
        # Use the first product name's first word as a quick term for fetching the page
        term = products[0].name.split()[0] if products[0].name else ''
        html = await self._fetch_page(term)
        now = datetime.now(timezone.utc)
        seen_ids = {p.external_id for p in products}
        offers: list[ProductOffer] = []
        soup = BeautifulSoup(html, 'lxml')
        for container in soup.find_all(attrs={'data-gtmga4data': True}):
            pid = container.get('data-pid')
            if not pid or pid not in seen_ids:
                continue
            gtm_raw = container.get('data-gtmga4data', '')
            gtm = self._parse_gtm_data(gtm_raw)
            if not gtm:
                continue
            price_raw = gtm.get('price')
            if price_raw is None:
                continue
            price = Decimal(str(price_raw))
            list_price_raw = gtm.get('item_list_price') or gtm.get('list_price')
            list_price = Decimal(str(list_price_raw)) if list_price_raw else None
            discount_pct = None
            if list_price and list_price > price:
                discount_pct = ((list_price - price) / list_price * 100).quantize(Decimal('0.01'))
            offers.append(
                ProductOffer(
                    pharmacy=self.slug,
                    external_id=str(pid),
                    price=price,
                    list_price=list_price,
                    discount_percentage=discount_pct,
                    available=True,
                    collected_at=now,
                )
            )
        return offers

    def _parse_gtm_data(self, raw: str) -> dict | None:
        if not raw:
            return None
        try:
            import html, json
            unescaped = html.unescape(raw)
            return json.loads(unescaped)
        except Exception:
            return None
