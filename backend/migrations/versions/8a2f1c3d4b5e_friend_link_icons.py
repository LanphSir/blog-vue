"""friend link icons

Revision ID: 8a2f1c3d4b5e
Revises: 37d8cc4547f9
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8a2f1c3d4b5e"
down_revision: str | Sequence[str] | None = "37d8cc4547f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("friend_links") as batch_op:
        batch_op.add_column(sa.Column("icon", sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("friend_links") as batch_op:
        batch_op.drop_column("icon")
