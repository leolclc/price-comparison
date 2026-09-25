from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.pharmacy_repository import PharmacyRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.search_term_repository import SearchTermRepository
from app.services.product_service import ProductService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_product_service(session: DbSession) -> ProductService:
    return ProductService(
        product_repo=ProductRepository(session),
        search_term_repo=SearchTermRepository(session),
    )


def get_pharmacy_repo(session: DbSession) -> PharmacyRepository:
    return PharmacyRepository(session)
