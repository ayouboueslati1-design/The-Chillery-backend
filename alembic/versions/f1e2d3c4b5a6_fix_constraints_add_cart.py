"""fix email unique constraint, phone length, add cart_items table

Revision ID: f1e2d3c4b5a6
Revises: cc26a1c4eff0
Create Date: 2026-03-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, None] = 'cc26a1c4eff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint to users.email
    op.create_unique_constraint('uq_users_email', 'users', ['email'])

    # Widen phone column to accommodate international numbers
    op.alter_column(
        'users', 'phone',
        existing_type=sa.String(length=10),
        type_=sa.String(length=20),
        existing_nullable=True,
    )

    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('selected_color', sa.String(length=100), nullable=True),
        sa.Column('selected_size', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cart_items_user_id', 'cart_items', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_cart_items_user_id', table_name='cart_items')
    op.drop_table('cart_items')
    op.alter_column(
        'users', 'phone',
        existing_type=sa.String(length=20),
        type_=sa.String(length=10),
        existing_nullable=True,
    )
    op.drop_constraint('uq_users_email', 'users', type_='unique')
