import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.common import ProductCandidate, ProductOffer
from normalization.matcher import build_match_key, group_candidates
from normalization.text import normalize_text
from providers.araujo import AraujoProvider
from providers.pacheco import PachecoProvider
from providers.pague_menos import PagueMenosProvider
from providers.raia import RaiaProvider
from providers.drogasil import DrogasilProvider

logger = logging.getLogger("COLLECTOR")


class CollectorJob:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._pharmacy_ids: dict[str, int] = {}
        self._providers = [
            PachecoProvider(),
            PagueMenosProvider(),
            AraujoProvider(),
            RaiaProvider(),
            DrogasilProvider(),
        ]

    async def run(self, terms: list[str]) -> None:
        logger.info(f"Starting collection for {len(terms)} terms")
        await self._ensure_pharmacies()

        all_candidates: list[ProductCandidate] = []
        candidates_by_provider: dict[object, list[list[ProductCandidate]]] = {
            provider: [] for provider in self._providers
        }

        try:
            for provider in self._providers:
                for term in terms:
                    try:
                        candidates = await provider.search(term)
                        all_candidates.extend(candidates)
                        if candidates:
                            candidates_by_provider[provider].append(candidates)
                        logger.info(
                            f"[{provider.name}] search term={term} products={len(candidates)}"
                        )
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(
                            f"[{provider.name}] Error searching term={term}: {e}"
                        )
            if not all_candidates:
                logger.warning("No candidates collected")
                return

            groups = group_candidates(all_candidates)
            logger.info(f"Grouped into {len(groups)} unique products")
            await self._persist_candidates(groups)

            # Discovery only creates products. Fetching and persisting the offers in
            # the same cycle makes the prices and destination links available to the UI.
            for provider, batches in candidates_by_provider.items():
                if not batches:
                    continue
                for candidates in batches:
                    try:
                        offers = await provider.get_prices(candidates)
                        await self._persist_offers(offers)
                        logger.info(
                            "[%s] collected offers=%s", provider.name, len(offers)
                        )
                    except Exception as e:
                        logger.error(
                            "[%s] Error collecting prices: %s", provider.name, e
                        )
        finally:
            await self._close_providers()

    async def run_price_update(self, terms: list[str]) -> None:
        logger.info("Starting price update")
        await self._ensure_pharmacies()

        try:
            for provider in self._providers:
                try:
                    from app_db import get_pharmacy_products_for_provider
                    products = await get_pharmacy_products_for_provider(
                        self._session, provider.slug
                    )
                    if not products:
                        continue

                    candidates = [
                        ProductCandidate(
                            pharmacy=provider.slug,
                            external_id=p["external_id"],
                            name=p["external_name"],
                        )
                        for p in products
                    ]

                    offers = await provider.get_prices(candidates)
                    await self._persist_offers(offers)
                    logger.info(
                        f"[{provider.name}] price update offers={len(offers)}"
                    )
                except Exception as e:
                    logger.error(f"[{provider.name}] Error in price update: {e}")
        finally:
            await self._close_providers()

    async def _close_providers(self) -> None:
        for provider in self._providers:
            close = getattr(provider, "close", None)
            if close:
                try:
                    await close()
                except Exception as e:
                    logger.warning("Failed to close %s: %s", provider.name, e)

    async def _ensure_pharmacies(self) -> None:
        """Create records missing from databases initialized before newer providers."""
        from app_models import Pharmacy

        for provider in self._providers:
            result = await self._session.execute(
                select(Pharmacy).where(Pharmacy.slug == provider.slug)
            )
            pharmacy = result.scalar_one_or_none()
            if pharmacy is None:
                pharmacy = Pharmacy(name=provider.name, slug=provider.slug, active=True)
                self._session.add(pharmacy)
                await self._session.flush()
                logger.info(
                    "Created missing pharmacy name=%s slug=%s",
                    provider.name,
                    provider.slug,
                )
            self._pharmacy_ids[provider.slug] = pharmacy.id

        await self._session.commit()

    async def _persist_candidates(
        self, groups: list[list[ProductCandidate]]
    ) -> None:
        for group in groups:
            try:
                canonical = self._pick_canonical(group)
                product_id = await self._upsert_product(canonical)

                for candidate in group:
                    pharmacy_id = await self._get_pharmacy_id(candidate.pharmacy)
                    if not pharmacy_id:
                        logger.warning(f"Unknown pharmacy slug: {candidate.pharmacy}")
                        continue

                    pp_id = await self._upsert_pharmacy_product(
                        product_id, pharmacy_id, candidate
                    )

                await self._session.commit()
            except Exception as e:
                logger.error(f"Error persisting group: {e}")
                await self._session.rollback()

    async def _persist_offers(self, offers: list[ProductOffer]) -> None:
        for offer in offers:
            try:
                pharmacy_id = await self._get_pharmacy_id(offer.pharmacy)
                if not pharmacy_id:
                    continue

                from sqlalchemy import select as sa_select
                from app_models import PharmacyProduct

                result = await self._session.execute(
                    sa_select(PharmacyProduct).where(
                        PharmacyProduct.pharmacy_id == pharmacy_id,
                        PharmacyProduct.external_id == offer.external_id,
                    )
                )
                pp = result.scalar_one_or_none()
                if not pp:
                    continue

                await self._upsert_offer(pp.product_id, pharmacy_id, pp.id, offer)
                await self._session.commit()
            except Exception as e:
                logger.error(f"Error persisting offer {offer.external_id}: {e}")
                await self._session.rollback()

    def _pick_canonical(self, group: list[ProductCandidate]) -> ProductCandidate:
        def richness(c: ProductCandidate) -> int:
            score = 0
            if c.ean:
                score += 10
            if c.active_ingredient:
                score += 5
            if c.dosage:
                score += 3
            if c.quantity:
                score += 2
            if c.brand:
                score += 2
            if c.pharmaceutical_form:
                score += 1
            return score

        return max(group, key=richness)

    async def _get_pharmacy_id(self, slug: str) -> int | None:
        cached_id = self._pharmacy_ids.get(slug)
        if cached_id is not None:
            return cached_id

        from sqlalchemy import select as sa_select
        from app_models import Pharmacy

        result = await self._session.execute(
            sa_select(Pharmacy).where(Pharmacy.slug == slug)
        )
        pharmacy = result.scalar_one_or_none()
        if pharmacy:
            self._pharmacy_ids[slug] = pharmacy.id
            return pharmacy.id
        return None

    async def _upsert_product(self, candidate: ProductCandidate) -> int:
        from app_models import Product
        from normalization.text import extract_dosage_from_name, extract_quantity_from_name

        normalized_name = normalize_text(candidate.name)

        dosage = candidate.dosage
        quantity = candidate.quantity
        unit = candidate.unit

        if not dosage:
            dosage = extract_dosage_from_name(candidate.name)
        if not quantity:
            quantity, extracted_unit = extract_quantity_from_name(candidate.name)
            if extracted_unit and not unit:
                unit = extracted_unit

        if candidate.ean:
            from sqlalchemy import select as sa_select
            result = await self._session.execute(
                sa_select(Product).where(Product.ean == candidate.ean)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing.id

        from sqlalchemy import select as sa_select, and_
        conditions = [Product.normalized_name == normalized_name]
        if dosage:
            conditions.append(Product.dosage == dosage)
        if quantity:
            conditions.append(Product.quantity == quantity)

        result = await self._session.execute(
            sa_select(Product).where(and_(*conditions))
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing.id

        product = Product(
            ean=candidate.ean,
            name=candidate.name,
            normalized_name=normalized_name,
            brand=candidate.brand,
            active_ingredient=candidate.active_ingredient,
            dosage=dosage,
            pharmaceutical_form=candidate.pharmaceutical_form,
            quantity=quantity,
            unit=unit,
        )
        self._session.add(product)
        await self._session.flush()
        logger.info(f"New product: {candidate.name} (id={product.id})")
        return product.id

    async def _upsert_pharmacy_product(
        self,
        product_id: int,
        pharmacy_id: int,
        candidate: ProductCandidate,
    ) -> int:
        from sqlalchemy import select as sa_select
        from app_models import PharmacyProduct

        result = await self._session.execute(
            sa_select(PharmacyProduct).where(
                PharmacyProduct.pharmacy_id == pharmacy_id,
                PharmacyProduct.external_id == candidate.external_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.external_name = candidate.name
            if candidate.url:
                existing.external_url = candidate.url
            if candidate.ean:
                existing.ean = candidate.ean
            return existing.id

        pp = PharmacyProduct(
            product_id=product_id,
            pharmacy_id=pharmacy_id,
            external_id=candidate.external_id,
            external_name=candidate.name,
            external_url=candidate.url,
            ean=candidate.ean,
        )
        self._session.add(pp)
        await self._session.flush()
        return pp.id

    async def _upsert_offer(
        self,
        product_id: int,
        pharmacy_id: int,
        pharmacy_product_id: int,
        offer: ProductOffer,
    ) -> None:
        from sqlalchemy import select as sa_select
        from app_models import Offer, PriceHistory, Promotion

        result = await self._session.execute(
            sa_select(Offer).where(
                Offer.product_id == product_id,
                Offer.pharmacy_id == pharmacy_id,
            )
        )
        existing = result.scalar_one_or_none()

        price_changed = True
        if existing:
            price_changed = (
                existing.price != offer.price
                or existing.available != offer.available
            )

            existing.price = offer.price
            existing.list_price = offer.list_price
            existing.price_without_discount = offer.price_without_discount
            existing.discount_percent = offer.discount_percentage
            existing.available = offer.available
            existing.collected_at = offer.collected_at
            offer_id = existing.id
        else:
            new_offer = Offer(
                product_id=product_id,
                pharmacy_id=pharmacy_id,
                pharmacy_product_id=pharmacy_product_id,
                price=offer.price,
                list_price=offer.list_price,
                price_without_discount=offer.price_without_discount,
                discount_percent=offer.discount_percentage,
                available=offer.available,
                collected_at=offer.collected_at,
            )
            self._session.add(new_offer)
            await self._session.flush()
            offer_id = new_offer.id

        if offer.promotion_type and offer_id:
            from sqlalchemy import delete
            await self._session.execute(
                delete(Promotion).where(Promotion.offer_id == offer_id)
            )
            promo = Promotion(
                offer_id=offer_id,
                type=offer.promotion_type,
                description=(
                    f"Leve {offer.promotion_quantity} pague menos"
                    if offer.promotion_quantity
                    else offer.promotion_type
                ),
                minimum_quantity=offer.promotion_quantity,
                promotion_price=offer.promotion_price,
            )
            self._session.add(promo)

        if price_changed:
            history = PriceHistory(
                product_id=product_id,
                pharmacy_id=pharmacy_id,
                price=offer.price,
                list_price=offer.list_price,
                available=offer.available,
                collected_at=offer.collected_at,
            )
            self._session.add(history)
            logger.info(
                f"price update sku={offer.external_id} price={offer.price}"
            )
