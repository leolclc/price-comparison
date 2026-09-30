"""Shared Playwright browser session for rendered pharmacy pages."""

import logging
import os

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

logger = logging.getLogger("PHARMACY_BROWSER")


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BrowserPageFetcher:
    """Reuse one Chromium instance while loading individual search pages."""

    def __init__(self, timeout_seconds: float = 45.0) -> None:
        self._timeout_ms = int(timeout_seconds * 1000)
        self._headless = _env_flag("COLLECTOR_BROWSER_HEADLESS", True)
        self._playwright = None
        self._browser = None
        self._context = None

    async def _ensure_started(self) -> None:
        if self._context:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            viewport={"width": 1365, "height": 900},
        )
        logger.info("Started Chromium (headless=%s)", self._headless)

    async def fetch_page(
        self,
        url: str,
        *,
        wait_for_selector: str | None = None,
        selector_timeout_ms: int = 20_000,
    ) -> str:
        await self._ensure_started()
        page = await self._context.new_page()
        denied_responses: list[str] = []

        def record_denied_response(response) -> None:
            if response.status == 403 and response.url.startswith("https://"):
                denied_responses.append(response.url)

        page.on("response", record_denied_response)
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self._timeout_ms,
            )
            if response and response.status == 403:
                raise PermissionError(f"Page returned HTTP 403: {url}")

            if wait_for_selector:
                try:
                    await page.wait_for_selector(
                        wait_for_selector,
                        state="attached",
                        timeout=selector_timeout_ms,
                    )
                except PlaywrightTimeoutError:
                    logger.warning(
                        "Timed out waiting for %s at %s; parsing rendered page anyway",
                        wait_for_selector,
                        url,
                    )

            if denied_responses:
                logger.warning(
                    "Browser received HTTP 403 for %s resource(s): %s",
                    len(denied_responses),
                    ", ".join(denied_responses[:3]),
                )
            return await page.content()
        finally:
            await page.close()

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
