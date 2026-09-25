from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.repositories.search_term_repository import SearchTermRepository

router = APIRouter(prefix="/api/search-terms", tags=["admin"])


class SearchTermSchema(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    term: str
    priority: int
    search_count: int
    last_searched_at: datetime | None
    next_search_at: datetime | None
    active: bool


@router.get("", response_model=list[SearchTermSchema])
@router.get("/", response_model=list[SearchTermSchema], include_in_schema=False)
async def list_search_terms(
    session: DbSession,
) -> list[SearchTermSchema]:
    repo = SearchTermRepository(session)
    terms = await repo.get_all_active()
    return [SearchTermSchema.model_validate(t) for t in terms]
