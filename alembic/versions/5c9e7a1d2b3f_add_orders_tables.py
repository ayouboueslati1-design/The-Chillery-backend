"""add orders and order_items tables

Revision ID: 5c9e7a1d2b3f
Revises: f1e2d3c4b5a6
Create Date: 2026-03-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c9e7a1d2b3f"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("guest_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("transaction_id", sa.String(length=255), nullable=True),
        sa.Column("auth_code", sa.String(length=64), nullable=True),
        sa.Column("amount_total", sa.Float(), nullable=False),
        sa.Column("shipping_address", sa.JSON(), nullable=False),
        sa.Column("shipping_method", sa.String(length=50), nullable=True),
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"], unique=True)
    op.create_index("ix_orders_guest_email", "orders", ["guest_email"], unique=False)
    op.create_index("ix_orders_transaction_id", "orders", ["transaction_id"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("product_image", sa.String(length=512), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_index("ix_orders_transaction_id", table_name="orders")
    op.drop_index("ix_orders_guest_email", table_name="orders")
    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_table("orders")
