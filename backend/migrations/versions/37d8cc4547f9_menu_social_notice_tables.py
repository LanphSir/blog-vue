"""menu social notice tables

Revision ID: 37d8cc4547f9
Revises: ddd6a85857d5
Create Date: 2026-10-09 08:27:03.226278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d8cc4547f9'
down_revision: Union[str, Sequence[str], None] = 'ddd6a85857d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="link"),
        sa.Column("is_external", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["parent_id"], ["menu_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_menu_items_parent_id"), "menu_items", ["parent_id"])
    op.create_index(op.f("ix_menu_items_visible"), "menu_items", ["visible"])

    op.create_table(
        "social_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_links_visible"), "social_links", ["visible"])

    op.create_table(
        "notices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="banner"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notices_type"), "notices", ["type"])
    op.create_index(op.f("ix_notices_enabled"), "notices", ["enabled"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_notices_enabled"), table_name="notices")
    op.drop_index(op.f("ix_notices_type"), table_name="notices")
    op.drop_table("notices")
    op.drop_index(op.f("ix_social_links_visible"), table_name="social_links")
    op.drop_table("social_links")
    op.drop_index(op.f("ix_menu_items_visible"), table_name="menu_items")
    op.drop_index(op.f("ix_menu_items_parent_id"), table_name="menu_items")
    op.drop_table("menu_items")
