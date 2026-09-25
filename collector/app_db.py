import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_engine():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://farma:farmapass@postgres:5432/farmacompare",
    )
    return create_async_engine(db_url, pool_pre_ping=True)


def get_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_pharmacy_products_for_provider(
    session: AsyncSession, pharmacy_slug: str
) -> list[dict]:
    from sqlalchemy import select
    from app_models import PharmacyProduct, Pharmacy

    result = await session.execute(
        select(PharmacyProduct, Pharmacy.slug)
        .join(Pharmacy, PharmacyProduct.pharmacy_id == Pharmacy.id)
        .where(Pharmacy.slug == pharmacy_slug)
    )
    rows = result.all()
    return [
        {
            "id": pp.id,
            "product_id": pp.product_id,
            "pharmacy_id": pp.pharmacy_id,
            "external_id": pp.external_id,
            "external_name": pp.external_name,
            "external_url": pp.external_url,
        }
        for pp, slug in rows
    ]
