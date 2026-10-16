"""media assets soft delete

Revision ID: b7e2f4a9c3d1
Revises: af5b7e9d2c31
Create Date: 2026-10-14 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e2f4a9c3d1"
down_revision: Union[str, Sequence[str], None] = "af5b7e9d2c31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("media_assets", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_media_assets_deleted_at"), "media_assets", ["deleted_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_media_assets_deleted_at"), table_name="media_assets")
    op.drop_column("media_assets", "deleted_at")
