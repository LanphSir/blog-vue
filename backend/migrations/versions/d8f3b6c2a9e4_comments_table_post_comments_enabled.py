"""comments table + posts.comments_enabled

Revision ID: d8f3b6c2a9e4
Revises: c9a1d2e3b4f5
Create Date: 2026-10-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f3b6c2a9e4'
down_revision: Union[str, Sequence[str], None] = 'c9a1d2e3b4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 新建表直接 CREATE 即可（SQLite 只在 ALTER 加 FK 时才需要 batch 模式）
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('root_id', sa.Integer(), nullable=True),
        sa.Column('reply_to_nickname', sa.String(length=30), nullable=True),
        sa.Column('nickname', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_comments_is_deleted'), 'comments', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_comments_parent_id'), 'comments', ['parent_id'], unique=False)
    op.create_index(op.f('ix_comments_post_id'), 'comments', ['post_id'], unique=False)
    op.create_index(op.f('ix_comments_root_id'), 'comments', ['root_id'], unique=False)
    op.create_index(op.f('ix_comments_status'), 'comments', ['status'], unique=False)

    # 存量文章默认开启评论（server_default 回填），与应用层 default=True 一致
    op.add_column(
        'posts',
        sa.Column('comments_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # 审核开关配置键（seed 只补新库；存量库在这里补齐，幂等写法）
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO site_configs (key, value) SELECT 'site_comment_audit', 'true' "
            "WHERE NOT EXISTS (SELECT 1 FROM site_configs WHERE key = 'site_comment_audit')"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_comments_status'), table_name='comments')
    op.drop_index(op.f('ix_comments_root_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_post_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_parent_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_is_deleted'), table_name='comments')
    op.drop_table('comments')
    with op.batch_alter_table('posts') as batch_op:
        batch_op.drop_column('comments_enabled')
