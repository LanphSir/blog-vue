"""comment pinned flags

Revision ID: e1c7a9d4f2b8
Revises: d8f3b6c2a9e4
Create Date: 2026-10-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1c7a9d4f2b8'
down_revision: Union[str, Sequence[str], None] = 'd8f3b6c2a9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite 加列走 batch 模式（AGENTS 规矩：涉及约束/默认值的新列统一 batch）
    with op.batch_alter_table('comments') as batch_op:
        batch_op.add_column(sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('pinned_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('comments') as batch_op:
        batch_op.drop_column('pinned_at')
        batch_op.drop_column('is_pinned')
