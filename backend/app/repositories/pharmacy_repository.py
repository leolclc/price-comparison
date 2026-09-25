from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pharmacy import Pharmacy


class PharmacyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Pharmacy]:
        result = await self._session.execute(
            select(Pharmacy).where(Pharmacy.active == True).order_by(Pharmacy.name)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Pharmacy | None:
        result = await self._session.execute(
            select(Pharmacy).where(Pharmacy.slug == slug)
        )
        return result.scalar_one_or_none()
