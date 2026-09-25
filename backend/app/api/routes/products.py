from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_product_service
from app.schemas.product import PriceHistoryPoint, ProductSchema, SearchResultSchema
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/search", response_model=SearchResultSchema)
async def search_products(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> SearchResultSchema:
    return await service.search(q)


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: int,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductSchema:
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/history", response_model=list[PriceHistoryPoint])
async def get_product_history(
    product_id: int,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> list[PriceHistoryPoint]:
    return await service.get_price_history(product_id)
