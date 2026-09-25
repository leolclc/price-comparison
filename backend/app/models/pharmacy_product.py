from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PharmacyProduct(Base):
    __tablename__ = "pharmacy_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    external_name: Mapped[str] = mapped_column(String(500), nullable=False)
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ean: Mapped[str | None] = mapped_column(String(20), nullable=True)
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
    product: Mapped["Product"] = relationship(back_populates="pharmacy_products")
    pharmacy: Mapped["Pharmacy"] = relationship(back_populates="pharmacy_products")
    offers: Mapped[list["Offer"]] = relationship(back_populates="pharmacy_product")

    __table_args__ = (
        Index("ix_pharmacy_products_product_id", "product_id"),
        Index("ix_pharmacy_products_pharmacy_id", "pharmacy_id"),
        Index("ix_pharmacy_products_ean", "ean"),
        Index("uq_pharmacy_products_pharmacy_external", "pharmacy_id", "external_id", unique=True),
    )


from app.models.product import Product  # noqa: E402
from app.models.pharmacy import Pharmacy  # noqa: E402
from app.models.offer import Offer  # noqa: E402
