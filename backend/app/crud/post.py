"""Post CRUD operations with pagination/filtering support."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


async def list_posts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    category_id: int | list[int] | None = None,
    tag_id: int | None = None,
    keyword: str | None = None,
    include_deleted: bool = False,
    deleted_only: bool = False,
) -> tuple[list[Post], int]:
    query = select(Post)
    if deleted_only:
        query = query.where(Post.deleted_at.is_not(None))
    elif not include_deleted:
        query = query.where(Post.deleted_at.is_(None))
    if status:
        query = query.where(Post.status == status)
    if category_id:
        if isinstance(category_id, list):
            query = query.where(Post.category_id.in_(category_id))
        else:
            query = query.where(Post.category_id == category_id)
    if tag_id:
        query = query.where(Post.tags.any(id=tag_id))
    if keyword:
        query = query.where(Post.title.contains(keyword))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Post.is_top.desc(), Post.sort_weight.desc(), Post.published_at.desc())
    rows = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return list(rows), total


async def get_by_slug(db: AsyncSession, slug: str) -> Post | None:
    result = await db.execute(select(Post).where(Post.slug == slug, Post.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, post_id: int) -> Post | None:
    return await db.get(Post, post_id)


async def get_by_id_not_deleted(db: AsyncSession, post_id: int) -> Post | None:
    result = await db.execute(select(Post).where(Post.id == post_id, Post.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def create_post(db: AsyncSession, payload: PostCreate) -> Post:
    post = Post(**payload.model_dump(exclude={"tag_ids"}))
    post.published_at = datetime.now(UTC) if post.status == "published" else None
    db.add(post)
    await db.flush()
    return post


async def update_post(db: AsyncSession, post: Post, payload: PostUpdate) -> Post:
    for field, value in payload.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(post, field, value)
    if payload.status == "published" and post.published_at is None:
        post.published_at = datetime.now(UTC)
    return post


async def soft_delete_post(db: AsyncSession, post: Post) -> None:
    post.deleted_at = datetime.now(UTC)
    await db.flush()


async def restore_post(db: AsyncSession, post: Post) -> None:
    post.deleted_at = None
    await db.flush()


async def hard_delete_post(db: AsyncSession, post: Post) -> None:
    await db.delete(post)


async def increment_view_count(db: AsyncSession, post: Post) -> None:
    post.view_count += 1
    await db.commit()


async def get_neighbors(db: AsyncSession, post: Post) -> tuple[Post | None, Post | None]:
    if post.published_at is None:
        return None, None
    prev_result = await db.execute(
        select(Post)
        .where(
            Post.status == "published",
            Post.deleted_at.is_(None),
            Post.published_at < post.published_at,
        )
        .order_by(Post.published_at.desc())
        .limit(1)
    )
    next_result = await db.execute(
        select(Post)
        .where(
            Post.status == "published",
            Post.deleted_at.is_(None),
            Post.published_at > post.published_at,
        )
        .order_by(Post.published_at.asc())
        .limit(1)
    )
    return prev_result.scalar_one_or_none(), next_result.scalar_one_or_none()
