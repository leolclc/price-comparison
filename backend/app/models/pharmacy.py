from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
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
        back_populates="pharmacy"
    )
    offers: Mapped[list["Offer"]] = relationship(back_populates="pharmacy")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="pharmacy"
    )


from app.models.pharmacy_product import PharmacyProduct  # noqa: E402
from app.models.offer import Offer  # noqa: E402
from app.models.price_history import PriceHistory  # noqa: E402
