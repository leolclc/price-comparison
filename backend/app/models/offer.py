from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False
    )
    pharmacy_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("pharmacy_products.id", ondelete="SET NULL"), nullable=True
    )

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_without_discount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    discount_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="offers")
    pharmacy: Mapped["Pharmacy"] = relationship(back_populates="offers")
    pharmacy_product: Mapped["PharmacyProduct | None"] = relationship(
        back_populates="offers"
    )
    promotions: Mapped[list["Promotion"]] = relationship(back_populates="offer")

    __table_args__ = (
        Index("ix_offers_product_id", "product_id"),
        Index("ix_offers_pharmacy_id", "pharmacy_id"),
        Index("ix_offers_collected_at", "collected_at"),
        Index("ix_offers_available", "available"),
        Index("uq_offers_product_pharmacy", "product_id", "pharmacy_id", unique=True),
    )


from app.models.product import Product  # noqa: E402
from app.models.pharmacy import Pharmacy  # noqa: E402
from app.models.pharmacy_product import PharmacyProduct  # noqa: E402
from app.models.promotion import Promotion  # noqa: E402
