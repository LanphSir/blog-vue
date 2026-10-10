"""media assets table

Revision ID: af5b7e9d2c31
Revises: 9c4e2f6a1d7b
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "af5b7e9d2c31"
down_revision: str | Sequence[str] | None = "9c4e2f6a1d7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing = sa.inspect(op.get_bind()).get_table_names()
    if "media_assets" in existing:  # table may pre-exist from create_all on dev DBs
        return
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("rel_path", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=600), nullable=False),
        sa.Column("ext", sa.String(length=10), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_name"),
    )
    op.create_index(op.f("ix_media_assets_created_at"), "media_assets", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_media_assets_created_at"), table_name="media_assets")
    op.drop_table("media_assets")
