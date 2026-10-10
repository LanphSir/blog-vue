"""friend link visible flag

Revision ID: 9c4e2f6a1d7b
Revises: 8a2f1c3d4b5e
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c4e2f6a1d7b"
down_revision: str | Sequence[str] | None = "8a2f1c3d4b5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("friend_links") as batch_op:
        batch_op.add_column(sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("1")))


def downgrade() -> None:
    with op.batch_alter_table("friend_links") as batch_op:
        batch_op.drop_column("visible")
