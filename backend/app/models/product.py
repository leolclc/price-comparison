from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    ean: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active_ingredient: Mapped[str | None] = mapped_column(String(300), nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pharmaceutical_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int | None] = mapped_column(nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    pharmacy_products: Mapped[list["PharmacyProduct"]] = relationship(
        back_populates="product"
    )
    offers: Mapped[list["Offer"]] = relationship(back_populates="product")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product"
    )

    __table_args__ = (
        Index("ix_products_ean", "ean"),
        Index("ix_products_normalized_name", "normalized_name"),
    )


from app.models.pharmacy_product import PharmacyProduct  # noqa: E402
from app.models.offer import Offer  # noqa: E402
from app.models.price_history import PriceHistory  # noqa: E402
