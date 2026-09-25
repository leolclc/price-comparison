from app.repositories.product_repository import ProductRepository
from app.repositories.search_term_repository import SearchTermRepository
from app.schemas.offer import OfferSchema, PromotionSchema
from app.schemas.product import PriceHistoryPoint, ProductSchema, SearchResultSchema


def _offer_to_schema(offer) -> OfferSchema:
    pharmacy = offer.pharmacy
    pp = offer.pharmacy_product
    return OfferSchema(
        id=offer.id,
        pharmacy_id=pharmacy.id,
        pharmacy_name=pharmacy.name,
        pharmacy_slug=pharmacy.slug,
        price=offer.price,
        list_price=offer.list_price,
        price_without_discount=offer.price_without_discount,
        discount_percent=offer.discount_percent,
        available=offer.available,
        collected_at=offer.collected_at,
        external_url=pp.external_url if pp else None,
        promotions=[
            PromotionSchema(
                id=p.id,
                type=p.type,
                description=p.description,
                minimum_quantity=p.minimum_quantity,
                promotion_price=p.promotion_price,
            )
            for p in getattr(offer, "promotions", [])
        ],
    )


def _product_to_schema(product, offers_schema: list[OfferSchema]) -> ProductSchema:
    return ProductSchema(
        id=product.id,
        ean=product.ean,
        name=product.name,
        brand=product.brand,
        active_ingredient=product.active_ingredient,
        dosage=product.dosage,
        pharmaceutical_form=product.pharmaceutical_form,
        quantity=product.quantity,
        unit=product.unit,
        offers=offers_schema,
    )


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        search_term_repo: SearchTermRepository,
    ) -> None:
        self._product_repo = product_repo
        self._search_term_repo = search_term_repo

    async def search(self, query: str) -> SearchResultSchema:
        # Increment search count for matching terms asynchronously
        try:
            await self._search_term_repo.increment_search_count(query)
        except Exception:
            pass

        products = await self._product_repo.search(query)

        product_schemas = []
        for product in products:
            # Sort offers: available first, then by price ascending
            sorted_offers = sorted(
                product.offers,
                key=lambda o: (not o.available, o.price),
            )
            offers_schema = [_offer_to_schema(o) for o in sorted_offers]
            product_schemas.append(_product_to_schema(product, offers_schema))

        # Sort products by lowest available price
        def min_price(p: ProductSchema) -> float:
            available = [o for o in p.offers if o.available]
            if not available:
                return float("inf")
            return float(min(o.price for o in available))

        product_schemas.sort(key=min_price)

        return SearchResultSchema(
            query=query,
            total=len(product_schemas),
            products=product_schemas,
        )

    async def get_by_id(self, product_id: int) -> ProductSchema | None:
        product = await self._product_repo.get_by_id(product_id)
        if not product:
            return None
        sorted_offers = sorted(
            product.offers,
            key=lambda o: (not o.available, o.price),
        )
        offers_schema = [_offer_to_schema(o) for o in sorted_offers]
        return _product_to_schema(product, offers_schema)

    async def get_price_history(
        self, product_id: int
    ) -> list[PriceHistoryPoint]:
        history = await self._product_repo.get_price_history(product_id)
        return [
            PriceHistoryPoint(
                pharmacy_id=h.pharmacy_id,
                pharmacy_name=h.pharmacy.name if h.pharmacy else "Desconhecida",
                price=h.price,
                list_price=h.list_price,
                available=h.available,
                collected_at=h.collected_at,
            )
            for h in history
        ]
