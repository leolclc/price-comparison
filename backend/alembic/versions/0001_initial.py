"""Initial migration

Revision ID: 0001
Revises:
Create Date: 2026-09-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pharmacies
    op.create_table(
        "pharmacies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ean", sa.String(length=20), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("normalized_name", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=200), nullable=True),
        sa.Column("active_ingredient", sa.String(length=300), nullable=True),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("pharmaceutical_form", sa.String(length=100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_ean", "products", ["ean"])
    op.create_index("ix_products_normalized_name", "products", ["normalized_name"])

    # pharmacy_products
    op.create_table(
        "pharmacy_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("external_name", sa.String(length=500), nullable=False),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("ean", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pharmacy_products_product_id", "pharmacy_products", ["product_id"])
    op.create_index("ix_pharmacy_products_pharmacy_id", "pharmacy_products", ["pharmacy_id"])
    op.create_index("ix_pharmacy_products_ean", "pharmacy_products", ["ean"])
    op.create_index(
        "uq_pharmacy_products_pharmacy_external",
        "pharmacy_products",
        ["pharmacy_id", "external_id"],
        unique=True,
    )

    # offers
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_product_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("list_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_without_discount", sa.Numeric(10, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pharmacy_product_id"], ["pharmacy_products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offers_product_id", "offers", ["product_id"])
    op.create_index("ix_offers_pharmacy_id", "offers", ["pharmacy_id"])
    op.create_index("ix_offers_collected_at", "offers", ["collected_at"])
    op.create_index("ix_offers_available", "offers", ["available"])
    op.create_index("uq_offers_product_pharmacy", "offers", ["product_id", "pharmacy_id"], unique=True)

    # price_history
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("pharmacy_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("list_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pharmacy_id"], ["pharmacies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_history_product_id", "price_history", ["product_id"])
    op.create_index("ix_price_history_pharmacy_id", "price_history", ["pharmacy_id"])
    op.create_index("ix_price_history_collected_at", "price_history", ["collected_at"])
    op.create_index("ix_price_history_product_pharmacy", "price_history", ["product_id", "pharmacy_id"])

    # promotions
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("minimum_quantity", sa.Integer(), nullable=True),
        sa.Column("promotion_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # search_terms
    op.create_table(
        "search_terms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("term", sa.String(length=200), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("search_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_searched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_search_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("term"),
    )


def downgrade() -> None:
    op.drop_table("search_terms")
    op.drop_table("promotions")
    op.drop_table("price_history")
    op.drop_table("offers")
    op.drop_table("pharmacy_products")
    op.drop_table("products")
    op.drop_table("pharmacies")
