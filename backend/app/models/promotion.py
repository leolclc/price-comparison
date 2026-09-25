from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. LMPM, DISCOUNT
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    minimum_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    promotion_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    offer: Mapped["Offer"] = relationship(back_populates="promotions")


from app.models.offer import Offer  # noqa: E402
