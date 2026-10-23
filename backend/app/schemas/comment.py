"""评论的请求/响应模型。

公开端只用 CommentOut（绝不含 email/ip/user_agent，这是隐私边界）；管理端用
CommentAdminOut 补充查删参考信息。CommentThreadOut 是一条顶级评论 + 前 N 条
回复 + 回复总数；CommentPage 分页壳的 items 在「顶级线程」与「平铺评论」两种
形态间复用。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    post_slug: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None
    nickname: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=100)
    content: str = Field(min_length=1, max_length=500)
    captcha_id: str = ""
    captcha_code: str = ""


class CommentOut(BaseModel):
    id: int
    post_id: int
    parent_id: int | None
    reply_to_nickname: str | None
    nickname: str
    content: str
    created_at: datetime
    # 占位标记（原文已被端点替换为占位文案）；前端据此灰显并禁用回复
    deleted: bool = False
    # 置顶（仅顶级楼有意义）；前端排序徽标用
    is_pinned: bool = False

    model_config = {"from_attributes": True}


class CommentThreadOut(BaseModel):
    comment: CommentOut
    replies: list[CommentOut] = []
    reply_count: int = 0


class CommentAdminOut(CommentOut):
    status: str
    is_deleted: bool
    email: str | None
    ip: str | None
    user_agent: str | None
    updated_at: datetime
    post_title: str | None = None  # 端点组装时手动填充
    post_slug: str | None = None
