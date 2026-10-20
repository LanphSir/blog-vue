"""评论端点：公开（线程列表/回复分页/发表评论）+ 管理（审核/隐藏/软删/恢复）。

发表评论的校验链：文章存在且已发布 → 允许评论 → 验证码（captcha_id 为空跳过，
与登录端点同款向后兼容）→ IP 限流 → 父级合法性 → 按 site_comment_audit 决定初始
status。公开序列化一律走 crud.comment_to_out，被删占位与隐私字段剥离都在那里。
管理端状态机：pending/hidden →approve→ approved；approved →hide→ hidden；
任意 →delete→ is_deleted；deleted →restore→ 回到原 status（approved）。
"""

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.core.captcha import verify as captcha_verify
from app.core.ratelimit import check_and_record
from app.crud import comment as comment_crud
from app.crud import post as post_crud
from app.crud import site as site_crud
from app.models.comment import Comment
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentOut, CommentThreadOut
from app.schemas.common import ApiResponse, PageData, ok

router = APIRouter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _audit_enabled(db) -> bool:
    """字符串布尔配置（"true"/其他），缺省视为开启审核（安全默认）。"""
    item = await site_crud.get_config(db, "site_comment_audit")
    if item is None:
        return True
    return (item.value or "").strip().lower() != "false"


# ---------------- Public ----------------


@router.get("/comments", summary="评论线程列表（公开）")
async def list_comments(
    db: DbDep,
    slug: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> ApiResponse[PageData[CommentThreadOut]]:
    post = await post_crud.get_by_slug(db, slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    items, total = await comment_crud.list_comment_threads(
        db, post.id, page=page, page_size=page_size
    )
    return ok(
        PageData(items=items, total=total, page=page, page_size=page_size)
    )


@router.get("/comments/count", summary="评论总数（公开）")
async def comment_count(db: DbDep, slug: str = Query(..., min_length=1)) -> ApiResponse[int]:
    """评论区头部计数：与文章详情的 comment_count 同一口径（approved 且未删，
    含楼中回复），供前端发表后轻量刷新，不重复拖整篇详情。"""
    post = await post_crud.get_by_slug(db, slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if not post.comments_enabled:
        return ok(0)
    return ok(await comment_crud.count_public(db, post.id))


@router.get("/comments/{comment_id}/replies", summary="楼中回复分页（公开）")
async def list_replies(
    db: DbDep,
    comment_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ApiResponse[PageData[CommentOut]]:
    root = await comment_crud.get_by_id(db, comment_id)
    if root is None or root.parent_id is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    items, total = await comment_crud.list_replies(db, root, page=page, page_size=page_size)
    return ok(PageData(items=items, total=total, page=page, page_size=page_size))


@router.post("/comments", summary="发表评论/回复（公开）", status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: CommentCreate, request: Request, db: DbDep
) -> ApiResponse[CommentOut]:
    post = await post_crud.get_by_slug(db, payload.post_slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if not post.comments_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该文章已关闭评论")
    if payload.captcha_id and not captcha_verify(payload.captcha_id, payload.captcha_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    ip = _client_ip(request)
    limited = check_and_record(ip)
    if limited:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=limited)

    parent: Comment | None = None
    if payload.parent_id is not None:
        parent = await comment_crud.get_by_id(db, payload.parent_id)
        if parent is None or parent.post_id != post.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="回复的评论不存在"
            )
        if parent.status != "approved" or parent.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="该评论不可回复"
            )

    nickname = payload.nickname.strip()
    content = payload.content.strip()
    if not nickname or not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="昵称和内容不能为空"
        )

    comment = Comment(
        post_id=post.id,
        parent_id=parent.id if parent else None,
        root_id=(parent.root_id or parent.id) if parent else None,
        reply_to_nickname=parent.nickname if parent else None,
        nickname=nickname,
        email=(payload.email or "").strip() or None,
        content=content,
        status="approved" if not await _audit_enabled(db) else "pending",
        ip=ip,
        user_agent=(request.headers.get("user-agent") or "")[:300] or None,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return ok(comment_crud.comment_to_out(comment))


# ---------------- Admin ----------------


@router.get("/admin/comments", summary="评论列表（管理）")
async def admin_list_comments(
    db: DbDep,
    _: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    post_id: int | None = None,
    keyword: str | None = None,
    deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> ApiResponse[PageData]:
    items, total = await comment_crud.list_admin_comments(
        db,
        status=status_filter,
        post_id=post_id,
        keyword=keyword,
        deleted_only=deleted,
        page=page,
        page_size=page_size,
    )
    post_ids = {c.post_id for c in items}
    titles: dict[int, str] = {}
    slugs: dict[int, str] = {}
    if post_ids:
        rows = (
            await db.execute(select(Post.id, Post.title, Post.slug).where(Post.id.in_(post_ids)))
        ).all()
        titles = {row[0]: row[1] for row in rows}
        slugs = {row[0]: row[2] for row in rows}
    for item in items:
        item.post_title = titles.get(item.post_id)
        item.post_slug = slugs.get(item.post_id)
    return ok(PageData(items=items, total=total, page=page, page_size=page_size))


@router.get("/admin/comments/pending-count", summary="待审评论数（管理）")
async def admin_pending_count(db: DbDep, _: CurrentUser) -> ApiResponse[int]:
    return ok(await comment_crud.count_pending(db))


async def _get_admin_comment(db, comment_id: int) -> Comment:
    comment = await comment_crud.get_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    return comment


def _admin_out(comment: Comment):
    from app.schemas.comment import CommentAdminOut

    return CommentAdminOut.model_validate(comment)


@router.post("/admin/comments/{comment_id}/approve", summary="通过评论（管理）")
async def admin_approve(comment_id: int, db: DbDep, _: CurrentUser) -> ApiResponse:
    comment = await _get_admin_comment(db, comment_id)
    if comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已删除的评论请先恢复")
    comment.status = "approved"
    await db.commit()
    await db.refresh(comment)
    return ok(_admin_out(comment))


@router.post("/admin/comments/{comment_id}/hide", summary="隐藏评论（管理）")
async def admin_hide(comment_id: int, db: DbDep, _: CurrentUser) -> ApiResponse:
    comment = await _get_admin_comment(db, comment_id)
    if comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已删除的评论请先恢复")
    comment.status = "hidden"
    await db.commit()
    await db.refresh(comment)
    return ok(_admin_out(comment))


@router.delete("/admin/comments/{comment_id}", summary="删除评论（软删除，管理）")
async def admin_delete(comment_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    comment = await _get_admin_comment(db, comment_id)
    comment.is_deleted = True
    await db.commit()
    return ok(None)


@router.post("/admin/comments/{comment_id}/restore", summary="恢复评论（管理）")
async def admin_restore(comment_id: int, db: DbDep, _: CurrentUser) -> ApiResponse:
    comment = await _get_admin_comment(db, comment_id)
    if not comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不在回收站中")
    comment.is_deleted = False
    if comment.status not in ("approved", "pending", "hidden"):
        comment.status = "approved"
    await db.commit()
    await db.refresh(comment)
    return ok(_admin_out(comment))
