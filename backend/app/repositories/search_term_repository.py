from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_term import SearchTerm


class SearchTermRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all_active(self) -> list[SearchTerm]:
        result = await self._session.execute(
            select(SearchTerm)
            .where(SearchTerm.active == True)  # noqa: E712
            .order_by(SearchTerm.priority.desc(), SearchTerm.search_count.desc())
        )
        return list(result.scalars().all())

    async def increment_search_count(self, term: str) -> None:
        clean_term = term.lower().strip()
        result = await self._session.execute(
            select(SearchTerm).where(SearchTerm.term == clean_term)
        )
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if existing:
            existing.search_count += 1
            existing.last_searched_at = now
        else:
            new_term = SearchTerm(
                term=clean_term,
                priority=3,
                search_count=1,
                last_searched_at=now,
                active=True,
            )
            self._session.add(new_term)
        await self._session.commit()
