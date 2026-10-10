"""Site config, banner and friend link CRUD operations."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Category, Post, Tag
from app.models.site import Banner, FriendLink, MenuItem, Notice, SiteConfig, SocialLink


async def get_config(db: AsyncSession, key: str) -> SiteConfig | None:
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == key))
    return result.scalar_one_or_none()


async def list_configs(db: AsyncSession) -> list[SiteConfig]:
    result = await db.execute(select(SiteConfig).order_by(SiteConfig.id))
    return list(result.scalars().all())


async def set_config(db: AsyncSession, key: str, value: str) -> SiteConfig:
    item = await get_config(db, key)
    if item is None:
        item = SiteConfig(key=key, value=value)
        db.add(item)
    else:
        item.value = value
    await db.flush()
    return item


async def list_friend_links(db: AsyncSession) -> list[FriendLink]:
    result = await db.execute(select(FriendLink).order_by(FriendLink.sort_order, FriendLink.id))
    return list(result.scalars().all())


async def get_friend_link(db: AsyncSession, friend_id: int) -> FriendLink | None:
    return await db.get(FriendLink, friend_id)


async def list_banners(db: AsyncSession, enabled_only: bool = False) -> list[Banner]:
    query = select(Banner)
    if enabled_only:
        query = query.where(Banner.enabled.is_(True))
    result = await db.execute(query.order_by(Banner.sort_order, Banner.id))
    return list(result.scalars().all())


async def get_banner(db: AsyncSession, banner_id: int) -> Banner | None:
    return await db.get(Banner, banner_id)


async def list_menus(db: AsyncSession) -> list[MenuItem]:
    result = await db.execute(select(MenuItem).order_by(MenuItem.sort_order, MenuItem.id))
    return list(result.scalars().all())


async def get_menu(db: AsyncSession, menu_id: int) -> MenuItem | None:
    return await db.get(MenuItem, menu_id)


async def list_social_links(db: AsyncSession, visible_only: bool = False) -> list[SocialLink]:
    query = select(SocialLink)
    if visible_only:
        query = query.where(SocialLink.visible.is_(True))
    result = await db.execute(query.order_by(SocialLink.sort_order, SocialLink.id))
    return list(result.scalars().all())


async def get_social_link(db: AsyncSession, link_id: int) -> SocialLink | None:
    return await db.get(SocialLink, link_id)


async def list_notices(db: AsyncSession, enabled_only: bool = False) -> list[Notice]:
    query = select(Notice)
    if enabled_only:
        query = query.where(Notice.enabled.is_(True))
    result = await db.execute(query.order_by(Notice.type, Notice.sort_order, Notice.id))
    return list(result.scalars().all())


async def get_notice(db: AsyncSession, notice_id: int) -> Notice | None:
    return await db.get(Notice, notice_id)


async def get_site_stats(db: AsyncSession) -> dict[str, int]:
    post_count = (
        await db.execute(select(func.count(Post.id)).where(Post.deleted_at.is_(None)))
    ).scalar_one()
    category_count = (await db.execute(select(func.count(Category.id)))).scalar_one()
    tag_count = (await db.execute(select(func.count(Tag.id)))).scalar_one()
    total_views = (
        await db.execute(
            select(func.coalesce(func.sum(Post.view_count), 0)).where(Post.deleted_at.is_(None))
        )
    ).scalar_one()

    earliest = (
        await db.execute(
            select(func.min(Post.published_at)).where(
                Post.status == "published", Post.deleted_at.is_(None)
            )
        )
    ).scalar_one()
    if earliest is None:
        days_since_launch = 0
    else:
        days_since_launch = max(0, (datetime.now(UTC).date() - earliest.date()).days)
    return {
        "post_count": post_count,
        "category_count": category_count,
        "tag_count": tag_count,
        "total_views": total_views,
        "days_since_launch": days_since_launch,
    }
