"""社交链接端点：公开可见列表 + 管理端 CRUD。

社交链接的 platform 是预设键或 custom（custom 时需带 label）；url 必须满足
http(s):// 或 mailto: 前缀（_validate_url），防注入与误配。公开接口仅返回可见项。
"""

import re

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbDep
from app.crud import site as site_crud
from app.models.site import SocialLink
from app.schemas.common import ApiResponse, ok
from app.schemas.site import SocialLinkCreate, SocialLinkOut, SocialLinkUpdate

router = APIRouter()

URL_SCHEMES = ("http://", "https://", "mailto:")
_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _validate_color(color: str | None) -> None:
    """自定义徽章颜色只接受 #RGB/#RRGGBB；空值（回退预设色）放行。"""
    if color and not _HEX_COLOR.match(color):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="徽章颜色必须是 #RGB 或 #RRGGBB 格式",
        )


def _validate_url(url: str | None) -> None:
    if not url or not url.startswith(URL_SCHEMES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="链接必须以 http(s):// 或 mailto: 开头",
        )


@router.get("/social-links", summary="社交链接（公开）")
async def list_public_social_links(db: DbDep) -> ApiResponse[list[SocialLinkOut]]:
    links = await site_crud.list_social_links(db, visible_only=True)
    return ok([SocialLinkOut.model_validate(link) for link in links])


@router.get("/admin/social-links", summary="社交链接管理列表")
async def admin_list_social_links(db: DbDep, _: CurrentUser) -> ApiResponse[list[SocialLinkOut]]:
    links = await site_crud.list_social_links(db)
    return ok([SocialLinkOut.model_validate(link) for link in links])


@router.post("/admin/social-links", summary="创建社交链接", status_code=status.HTTP_201_CREATED)
async def create_social_link(
    payload: SocialLinkCreate, db: DbDep, _: CurrentUser
) -> ApiResponse[SocialLinkOut]:
    if not payload.platform.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="平台不能为空"
        )
    _validate_url(payload.url)
    _validate_color(payload.color)
    link = SocialLink(**payload.model_dump())
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return ok(SocialLinkOut.model_validate(link))


@router.put("/admin/social-links/{link_id}", summary="更新社交链接")
async def update_social_link(
    link_id: int, payload: SocialLinkUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[SocialLinkOut]:
    link = await site_crud.get_social_link(db, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="链接不存在")
    changes = payload.model_dump(exclude_unset=True)
    if "url" in changes:
        _validate_url(changes["url"])
    if "color" in changes:
        _validate_color(changes["color"])
    if "platform" in changes and (changes["platform"] or "").strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="平台不能为空"
        )
    for field, value in changes.items():
        setattr(link, field, value)
    await db.commit()
    await db.refresh(link)
    return ok(SocialLinkOut.model_validate(link))


@router.delete("/admin/social-links/{link_id}", summary="删除社交链接")
async def delete_social_link(link_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    link = await site_crud.get_social_link(db, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="链接不存在")
    await db.delete(link)
    await db.commit()
    return ok(None)
