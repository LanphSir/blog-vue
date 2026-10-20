"""评论 CRUD 与序列化：公开线程组装、管理端筛选与占位语义。

占位语义（comment_to_out + _keep）：
- 可展示真评论 = status=approved 且未删；
- 被删评论若线程内仍有存活后代，以占位形式显示（content 换 DELETED_PLACEHOLDER，
  昵称保留）；无存活后代的被删评论连同整条死链完全不出现；
- hidden 自身不显示，但其下存活回复照常平铺显示（回复自带 reply_to_nickname）。
隐私边界：公开 DTO CommentOut 根本没有 email/ip/user_agent 字段。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.schemas.comment import CommentAdminOut, CommentOut, CommentThreadOut

DELETED_PLACEHOLDER = "该评论已被删除"


def comment_to_out(c: Comment) -> CommentOut:
    """ORM → 公开 DTO；被删评论原文不外泄，content 换占位文案。"""
    out = CommentOut.model_validate(c)
    if c.is_deleted:
        out.content = DELETED_PLACEHOLDER
    return out


def _is_live(c: Comment) -> bool:
    return c.status == "approved" and not c.is_deleted


def _has_live_descendant(c: Comment, kids: dict[int, list[Comment]]) -> bool:
    for child in kids.get(c.id, []):
        if _is_live(child) or _has_live_descendant(child, kids):
            return True
    return False


def _keep(c: Comment, kids: dict[int, list[Comment]]) -> bool:
    """该行是否出现在公开视图：真评论，或被删但线程里还挂着活回复的占位。"""
    if _is_live(c):
        return True
    return c.is_deleted and _has_live_descendant(c, kids)


def _live_reply_exists():
    """IN 子查询（与 EXISTS 等价）：外层 comments 行（必为顶级楼，root_id 即楼
    id）所属线程是否有存活回复——与 _keep 对顶层楼的判定等价（存活后代不会隔着
    pending，回复只能挂在 approved 上产生，见端点校验）。"""
    return Comment.id.in_(
        select(Comment.root_id)
        .where(
            Comment.root_id.is_not(None),
            Comment.status == "approved",
            Comment.is_deleted.is_(False),
        )
        .correlate(None)  # 子查询外层同表，必须禁自动关联，否则 FROM 被吞
    )


async def get_by_id(db: AsyncSession, comment_id: int) -> Comment | None:
    return await db.get(Comment, comment_id)


async def count_public(db: AsyncSession, post_id: int) -> int:
    """文章 meta 用：approved 且未删的评论总数（含楼中回复）。"""
    result = await db.execute(
        select(func.count())
        .select_from(Comment)
        .where(
            Comment.post_id == post_id,
            Comment.status == "approved",
            Comment.is_deleted.is_(False),
        )
    )
    return int(result.scalar_one())


async def count_pending(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Comment)
        .where(Comment.status == "pending", Comment.is_deleted.is_(False))
    )
    return int(result.scalar_one())


async def _load_threads(
    db: AsyncSession, roots: list[Comment]
) -> dict[int, dict[str, list[Comment]]]:
    """给一批顶级楼，取回各自线程里除 pending 外的全部后代，按 parent 分组。"""
    root_ids = [r.id for r in roots]
    rows = (
        (
            await db.execute(
                select(Comment)
                .where(Comment.root_id.in_(root_ids), Comment.status != "pending")
                .order_by(Comment.created_at.asc(), Comment.id.asc())
            )
        )
        .scalars()
        .all()
    )
    by_root: dict[int, dict[str, list[Comment]]] = {
        rid: {"all": [], "kids": []} for rid in root_ids
    }
    # kids 用 parent_id 分组挂在各自行上
    kids_map: dict[int, dict[int, list[Comment]]] = {rid: {} for rid in root_ids}
    for row in rows:
        rid = row.root_id or 0
        by_root.setdefault(rid, {"all": [], "kids": []})["all"].append(row)
        kids_map.setdefault(rid, {}).setdefault(row.parent_id or 0, []).append(row)
    for rid in kids_map:
        by_root[rid]["kids"] = kids_map[rid]
    return by_root


async def list_comment_threads(
    db: AsyncSession, post_id: int, *, page: int, page_size: int
) -> tuple[list[CommentThreadOut], int]:
    """顶级评论分页：正常楼 + 有存活回复的被删占位楼，时间正序。"""
    top_visible = ((Comment.status == "approved") & (Comment.is_deleted.is_(False))) | (
        Comment.is_deleted.is_(True) & _live_reply_exists()
    )
    query = select(Comment).where(
        Comment.post_id == post_id, Comment.parent_id.is_(None), top_visible
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                query.order_by(Comment.created_at.asc(), Comment.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return [], int(total)

    loaded = await _load_threads(db, list(rows))
    threads: list[CommentThreadOut] = []
    for row in rows:
        data = loaded.get(row.id, {"all": [], "kids": {}})
        kids = data["kids"]
        replies = [c for c in data["all"] if _keep(c, kids)]
        threads.append(
            CommentThreadOut(
                comment=comment_to_out(row),
                replies=[comment_to_out(r) for r in replies[:3]],
                reply_count=len(replies),
            )
        )
    return threads, int(total)


async def list_replies(
    db: AsyncSession, root: Comment, *, page: int, page_size: int
) -> tuple[list[CommentOut], int]:
    """展开某楼的完整回复列表（含占位楼内回复），时间正序分页。"""
    loaded = await _load_threads(db, [root])
    data = loaded.get(root.id, {"all": [], "kids": {}})
    kids = data["kids"]
    visible = [comment_to_out(c) for c in data["all"] if _keep(c, kids)]
    total = len(visible)
    return visible[(page - 1) * page_size : page * page_size], total


async def list_admin_comments(
    db: AsyncSession,
    *,
    status: str | None = None,
    post_id: int | None = None,
    keyword: str | None = None,
    deleted_only: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[CommentAdminOut], int]:
    """管理端分页：默认排除软删除，deleted_only 进回收站视图（不再叠加状态过滤）。"""
    query = select(Comment)
    if deleted_only:
        query = query.where(Comment.is_deleted.is_(True))
    else:
        query = query.where(Comment.is_deleted.is_(False))
        if status:
            query = query.where(Comment.status == status)
    if post_id:
        query = query.where(Comment.post_id == post_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.where(Comment.content.like(like) | Comment.nickname.like(like))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                query.order_by(Comment.created_at.desc(), Comment.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return [CommentAdminOut.model_validate(r) for r in rows], int(total)
