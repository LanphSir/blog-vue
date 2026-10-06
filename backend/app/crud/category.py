"""Category and Tag CRUD operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Category, Post, Tag


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.sort_order, Category.id))
    return list(result.scalars().all())


async def list_tags(db: AsyncSession) -> list[Tag]:
    result = await db.execute(select(Tag).order_by(Tag.sort_order, Tag.id))
    return list(result.scalars().all())


async def count_posts_by_category(db: AsyncSession) -> dict[int, int]:
    rows = (
        await db.execute(
            select(Post.category_id, func.count(Post.id))
            .where(Post.deleted_at.is_(None))
            .group_by(Post.category_id)
        )
    ).all()
    return {category_id: count for category_id, count in rows if category_id is not None}


async def count_posts_by_tag(db: AsyncSession) -> dict[int, int]:
    rows = (
        await db.execute(
            select(Tag.id, func.count(Tag.id))
            .join(Tag.posts)
            .where(Post.deleted_at.is_(None))
            .group_by(Tag.id)
        )
    ).all()
    return dict(rows)


async def get_category_by_id(db: AsyncSession, category_id: int) -> Category | None:
    return await db.get(Category, category_id)


async def get_category_by_slug(db: AsyncSession, slug: str) -> Category | None:
    result = await db.execute(select(Category).where(Category.slug == slug))
    return result.scalar_one_or_none()


async def get_tag_by_id(db: AsyncSession, tag_id: int) -> Tag | None:
    return await db.get(Tag, tag_id)


async def get_tag_by_slug(db: AsyncSession, slug: str) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    return result.scalar_one_or_none()


async def get_descendant_category_ids(db: AsyncSession, category_id: int) -> list[int]:
    """Return the category id plus all direct child ids (two-level hierarchy)."""
    result = await db.execute(select(Category.id).where(Category.parent_id == category_id))
    child_ids = [row[0] for row in result.all()]
    return [category_id, *child_ids]
