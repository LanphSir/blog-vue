"""Site config and friend link endpoints: public reads + admin CRUD."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbDep
from app.core.config_validation import check_config_value
from app.crud import site as site_crud
from app.models.site import Banner, FriendLink
from app.schemas.common import ApiResponse, ok
from app.schemas.site import (
    BannerCreate,
    BannerOut,
    BannerUpdate,
    ConfigItem,
    ConfigOut,
    FriendLinkCreate,
    FriendLinkOut,
    FriendLinkUpdate,
    SiteStats,
)

router = APIRouter()


@router.get("/site/config", summary="站点配置（公开）")
async def get_site_config(db: DbDep) -> ApiResponse[list[ConfigOut]]:
    configs = await site_crud.list_configs(db)
    return ok([ConfigOut.model_validate(item) for item in configs])


@router.put("/admin/site/config", summary="批量更新站点配置")
async def update_site_config(
    payload: list[ConfigItem], db: DbDep, _: CurrentUser
) -> ApiResponse[list[ConfigOut]]:
    errors = [
        f"{item.key}: {error}"
        for item in payload
        if (error := check_config_value(item.key, item.value))
    ]
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="；".join(errors),
        )
    items = []
    for item in payload:
        saved = await site_crud.set_config(db, item.key, item.value)
        items.append(saved)
    await db.commit()
    return ok([ConfigOut.model_validate(i) for i in items])


@router.get("/friends", summary="友链列表（公开，仅显示中）")
async def list_friends(db: DbDep) -> ApiResponse[list[FriendLinkOut]]:
    links = await site_crud.list_friend_links(db, visible_only=True)
    return ok([FriendLinkOut.model_validate(link) for link in links])


@router.get("/admin/friends", summary="友链管理列表（含隐藏）")
async def admin_list_friends(db: DbDep, _: CurrentUser) -> ApiResponse[list[FriendLinkOut]]:
    links = await site_crud.list_friend_links(db)
    return ok([FriendLinkOut.model_validate(link) for link in links])


@router.post("/admin/friends", summary="创建友链", status_code=status.HTTP_201_CREATED)
async def create_friend(
    payload: FriendLinkCreate, db: DbDep, _: CurrentUser
) -> ApiResponse[FriendLinkOut]:
    link = FriendLink(**payload.model_dump())
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return ok(FriendLinkOut.model_validate(link))


@router.put("/admin/friends/{friend_id}", summary="更新友链")
async def update_friend(
    friend_id: int, payload: FriendLinkUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[FriendLinkOut]:
    link = await site_crud.get_friend_link(db, friend_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, field, value)
    await db.commit()
    await db.refresh(link)
    return ok(FriendLinkOut.model_validate(link))


@router.delete("/admin/friends/{friend_id}", summary="删除友链")
async def delete_friend(friend_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    link = await site_crud.get_friend_link(db, friend_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
    await db.delete(link)
    await db.commit()
    return ok(None)


@router.get("/banners", summary="轮播图列表（公开）")
async def list_banners(db: DbDep) -> ApiResponse[list[BannerOut]]:
    banners = await site_crud.list_banners(db, enabled_only=True)
    return ok([BannerOut.model_validate(b) for b in banners])


@router.get("/admin/banners", summary="轮播图管理列表")
async def admin_list_banners(db: DbDep, _: CurrentUser) -> ApiResponse[list[BannerOut]]:
    banners = await site_crud.list_banners(db)
    return ok([BannerOut.model_validate(b) for b in banners])


@router.post("/admin/banners", summary="创建轮播图", status_code=status.HTTP_201_CREATED)
async def create_banner(payload: BannerCreate, db: DbDep, _: CurrentUser) -> ApiResponse[BannerOut]:
    banner = Banner(**payload.model_dump())
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return ok(BannerOut.model_validate(banner))


@router.put("/admin/banners/{banner_id}", summary="更新轮播图")
async def update_banner(
    banner_id: int, payload: BannerUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[BannerOut]:
    banner = await site_crud.get_banner(db, banner_id)
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="轮播图不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    await db.commit()
    await db.refresh(banner)
    return ok(BannerOut.model_validate(banner))


@router.delete("/admin/banners/{banner_id}", summary="删除轮播图")
async def delete_banner(banner_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    banner = await site_crud.get_banner(db, banner_id)
    if banner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="轮播图不存在")
    await db.delete(banner)
    await db.commit()
    return ok(None)


@router.get("/site/stats", summary="站点统计（公开）")
async def get_site_stats(db: DbDep) -> ApiResponse[SiteStats]:
    return ok(SiteStats(**await site_crud.get_site_stats(db)))
