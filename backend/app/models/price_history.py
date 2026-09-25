from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False
    )

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="price_history")
    pharmacy: Mapped["Pharmacy"] = relationship(back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_product_id", "product_id"),
        Index("ix_price_history_pharmacy_id", "pharmacy_id"),
        Index("ix_price_history_collected_at", "collected_at"),
        Index("ix_price_history_product_pharmacy", "product_id", "pharmacy_id"),
    )


from app.models.product import Product  # noqa: E402
from app.models.pharmacy import Pharmacy  # noqa: E402
