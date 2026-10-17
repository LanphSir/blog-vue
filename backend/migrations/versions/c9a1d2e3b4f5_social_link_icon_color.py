"""social link icon/color

Revision ID: c9a1d2e3b4f5
Revises: b7e2f4a9c3d1
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9a1d2e3b4f5'
down_revision: Union[str, Sequence[str], None] = 'b7e2f4a9c3d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite 不支持直接 ADD COLUMN 带默认值的复杂约束，统一走 batch 模式更稳妥
    with op.batch_alter_table('social_links') as batch_op:
        batch_op.add_column(sa.Column('icon_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('color', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('social_links') as batch_op:
        batch_op.drop_column('color')
        batch_op.drop_column('icon_url')
