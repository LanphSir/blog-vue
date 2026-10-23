"""评论 ORM 模型：匿名访客评论与嵌套回复。

评论用 parent_id 存真正的回复树，root_id 冗余顶级祖先便于按楼取回复列表；
status 三态（pending/approved/hidden）承载审核，is_deleted 是软删除——被删评论
若有存活回复，前台以「该评论已被删除」占位显示（见端点序列化）。reply_to_nickname
冗余被回复者昵称，父级被删后「回复 @xx」前缀仍然可读。限流与验证码策略在端点层。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    # 回复树：parent 为直接父级，root 为顶级楼（顶级评论两者皆 NULL）
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id"), default=None, index=True
    )
    root_id: Mapped[int | None] = mapped_column(Integer, default=None, index=True)
    reply_to_nickname: Mapped[str | None] = mapped_column(String(30), default=None)
    nickname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(100), default=None)
    content: Mapped[str] = mapped_column(Text)
    # pending 待审核 / approved 公开 / hidden 后台隐藏（数据完好可随时恢复）
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # 置顶只对顶级楼有意义（端点拒绝给回复置顶）；pinned_at 决定多个置顶间先后
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    ip: Mapped[str | None] = mapped_column(String(45), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(300), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
