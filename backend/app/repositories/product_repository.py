from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.offer import Offer
from app.models.pharmacy import Pharmacy
from app.models.pharmacy_product import PharmacyProduct
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.promotion import Promotion


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(self, query: str) -> list[Product]:
        """Search products by normalized_name with their latest offers."""
        normalized_query = query.lower().strip()
        terms = normalized_query.split()

        conditions = []
        for term in terms:
            conditions.append(
                Product.normalized_name.ilike(f"%{term}%")
            )

        stmt = (
            select(Product)
            .where(
                Product.active == True,  # noqa: E712
                *conditions,
            )
            .options(
                selectinload(Product.offers)
                .selectinload(Offer.pharmacy),
                selectinload(Product.offers)
                .selectinload(Offer.promotions),
                selectinload(Product.offers)
                .selectinload(Offer.pharmacy_product),
            )
            .order_by(Product.name)
            .limit(50)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.offers)
                .selectinload(Offer.pharmacy),
                selectinload(Product.offers)
                .selectinload(Offer.promotions),
                selectinload(Product.offers)
                .selectinload(Offer.pharmacy_product),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_price_history(
        self, product_id: int, limit: int = 100
    ) -> list[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .options(selectinload(PriceHistory.pharmacy))
            .order_by(PriceHistory.collected_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
