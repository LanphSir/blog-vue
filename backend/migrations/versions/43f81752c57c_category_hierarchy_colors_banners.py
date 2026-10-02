"""category hierarchy, colors, banners

Revision ID: 43f81752c57c
Revises: 6dc7bcedfce3
Create Date: 2026-09-14 16:43:10.243707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43f81752c57c'
down_revision: Union[str, Sequence[str], None] = '6dc7bcedfce3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'banners',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('subtitle', sa.String(length=500), nullable=True),
        sa.Column('image', sa.String(length=500), nullable=True),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_banners_enabled'), 'banners', ['enabled'], unique=False)

    with op.batch_alter_table('categories') as batch_op:
        batch_op.add_column(sa.Column('color', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_categories_parent_id', ['parent_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_categories_parent_id', 'categories', ['parent_id'], ['id']
        )

    op.add_column('tags', sa.Column('color', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tags', 'color')

    with op.batch_alter_table('categories') as batch_op:
        batch_op.drop_constraint('fk_categories_parent_id', type_='foreignkey')
        batch_op.drop_index('ix_categories_parent_id')
        batch_op.drop_column('parent_id')
        batch_op.drop_column('color')

    op.drop_index(op.f('ix_banners_enabled'), table_name='banners')
    op.drop_table('banners')