import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models.pharmacy import Pharmacy
from app.models.product import Product
from app.models.pharmacy_product import PharmacyProduct
from app.models.offer import Offer


@pytest.mark.asyncio
async def test_search_empty(client):
    response = await client.get("/api/products/search?q=dipirona")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "dipirona"
    assert data["products"] == []


@pytest.mark.asyncio
async def test_search_with_product(client, db_session):
    # Seed pharmacy
    pharmacy = Pharmacy(name="Teste", slug="teste")
    db_session.add(pharmacy)
    await db_session.flush()

    # Seed product
    product = Product(
        name="Dipirona 500mg 10 comprimidos",
        normalized_name="dipirona 500mg 10 comprimidos",
        brand="Neo Quimica",
        dosage="500mg",
        quantity=10,
        unit="comprimidos",
    )
    db_session.add(product)
    await db_session.flush()

    # Seed pharmacy_product
    pp = PharmacyProduct(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        external_id="12345",
        external_name="Dipirona 500mg 10 comprimidos",
        external_url="https://example.com/produto/12345",
    )
    db_session.add(pp)
    await db_session.flush()

    # Seed offer
    offer = Offer(
        product_id=product.id,
        pharmacy_id=pharmacy.id,
        pharmacy_product_id=pp.id,
        price=Decimal("7.99"),
        list_price=Decimal("15.00"),
        available=True,
        collected_at=datetime.now(timezone.utc),
    )
    db_session.add(offer)
    await db_session.commit()

    response = await client.get("/api/products/search?q=dipirona")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["name"] == "Dipirona 500mg 10 comprimidos"
    assert len(data["products"][0]["offers"]) == 1
    assert data["products"][0]["offers"][0]["price"] == "7.99"
    assert data["products"][0]["offers"][0]["pharmacy_name"] == "Teste"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get("/api/products/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pharmacies(client, db_session):
    p = Pharmacy(name="Araujo", slug="araujo", active=True)
    db_session.add(p)
    await db_session.commit()

    response = await client.get("/api/pharmacies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(x["slug"] == "araujo" for x in data)
