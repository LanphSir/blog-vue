"""图片上传：时间戳+哈希命名、按日分文件夹，以及媒体库管理。

上传先写临时文件并流式限大小，再用 magic bytes 校验真实 MIME（_sniff_mime），
杜绝伪装扩展名；最终落盘为 ``{时间戳}_{sha256前8位}{扩展名}`` 并登记 media_assets。
媒体库支持按目录分页/统计；删除为软删除（回收站，文件保留、引用不失效），
彻底删除才物理删文件且默认带引用保护（force 可绕过）；启动时会
sweep 导入库建立前遗留的旧文件（见 seed.py）。
"""

import hashlib
import logging
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbDep
from app.core.config import settings
from app.models.post import Post
from app.models.site import Banner, FriendLink, MediaAsset, SiteConfig
from app.schemas.common import ApiResponse, ok
from app.schemas.media import MediaAssetOut

logger = logging.getLogger("blog")

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024
_SAFE_SUFFIX = re.compile(r"^\.[a-z0-9]+$")


def _sniff_mime(head: bytes, ext: str) -> str | None:
    """Return the real MIME type from magic bytes, or None if it doesn't match the extension."""
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg" if head.startswith(b"\xff\xd8\xff") else None
    if ext == ".png":
        return "image/png" if head.startswith(b"\x89PNG\r\n\x1a\n") else None
    if ext == ".gif":
        return "image/gif" if head[:6] in (b"GIF87a", b"GIF89a") else None
    if ext == ".webp":
        return "image/webp" if head[:4] == b"RIFF" and head[8:12] == b"WEBP" else None
    if ext == ".svg":
        stripped = head.lstrip()
        is_svg = stripped.startswith(b"<svg") or (
            stripped.startswith(b"<?xml") and b"<svg" in stripped
        )
        return "image/svg+xml" if is_svg else None
    return None


@router.post("/admin/upload", summary="上传图片", status_code=status.HTTP_201_CREATED)
async def upload_image(
    _: CurrentUser,
    db: DbDep,
    file: UploadFile = File(...),
) -> ApiResponse[str]:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS or not _SAFE_SUFFIX.match(ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式：{ext or '未知'}",
        )

    upload_root = settings.upload_path
    now = datetime.now()
    day_dir = upload_root / f"{now:%Y}" / f"{now:%m}" / f"{now:%d}"
    day_dir.mkdir(parents=True, exist_ok=True)

    # 先写临时文件并流式读入：边限大小、边留前 32 字节供 magic bytes 嗅探、边累计 sha256
    digest = hashlib.sha256()
    size = 0
    head = b""
    tmp = day_dir / f".upload-{now:%Y%m%d%H%M%S}-{id(file)}.tmp"
    try:
        with tmp.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件超过 {settings.max_upload_size_mb}MB 限制",
                    )
                if len(head) < 32:
                    head = (head + chunk)[:32]
                digest.update(chunk)
                out.write(chunk)
    finally:
        await file.close()

    if size == 0:
        tmp.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="空文件")

    # 用 magic bytes 校验真实类型，防止"改后缀伪装成图片"的文件混入
    mime = _sniff_mime(head, ext)
    if mime is None:
        tmp.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件内容与扩展名 {ext} 不符（可能是伪装扩展名）",
        )

    stored_name = f"{now:%Y%m%d%H%M%S}_{digest.hexdigest()[:8]}{ext}"
    counter = 1
    while (day_dir / stored_name).exists():
        stored_name = f"{now:%Y%m%d%H%M%S}_{digest.hexdigest()[:8]}-{counter}{ext}"
        counter += 1
    dest = day_dir / stored_name
    tmp.replace(dest)

    rel_path = str(dest.relative_to(upload_root))
    asset = MediaAsset(
        name=Path(file.filename or stored_name).name[:255],
        stored_name=stored_name,
        rel_path=rel_path,
        url=f"/uploads/{rel_path}",
        ext=ext,
        mime=mime,
        size=size,
    )
    db.add(asset)
    await db.commit()

    logger.info("Uploaded %s (%d bytes, %s)", rel_path, size, mime)
    return ok(asset.url)


@router.get("/admin/media", summary="媒体库列表（分页）")
async def list_media(
    _: CurrentUser,
    db: DbDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    dir: str | None = Query(None, description="dir prefix, e.g. 2026-10-01 or root"),
    deleted: bool = Query(False, description="true 只看回收站（已软删）文件"),
) -> ApiResponse[dict]:
    # 软删除过滤是硬约束：列表、计数与选择器数据源都只能看到当前视图的资产
    conditions = [
        MediaAsset.deleted_at.is_(None) if not deleted else MediaAsset.deleted_at.isnot(None)
    ]
    if dir == "root":
        conditions.append(MediaAsset.rel_path.notlike("%/%"))
    elif dir:
        conditions.append(MediaAsset.rel_path.like(f"{dir}/%"))

    total_stmt = select(func.count(MediaAsset.id))
    list_stmt = select(MediaAsset)
    for cond in conditions:
        total_stmt = total_stmt.where(cond)
        list_stmt = list_stmt.where(cond)

    total = (await db.execute(total_stmt)).scalar_one()
    result = await db.execute(
        list_stmt.order_by(MediaAsset.created_at.desc(), MediaAsset.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [MediaAssetOut.model_validate(a) for a in result.scalars().all()]
    return ok({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/admin/media/folders", summary="媒体库目录统计（按存储目录聚合）")
async def list_media_folders(_: CurrentUser, db: DbDep) -> ApiResponse[list[dict]]:
    # 目录计数只统计未删除文件，回收站内容不计入目录树徽标
    result = await db.execute(select(MediaAsset.rel_path).where(MediaAsset.deleted_at.is_(None)))
    counts: dict[str, int] = {}
    for (rel,) in result.all():
        parent = str(PurePosixPath(rel).parent)
        key = "" if parent == "." else parent
        counts[key] = counts.get(key, 0) + 1
    folders = [{"dir": key or "root", "count": count} for key, count in sorted(counts.items())]
    return ok(folders)


async def _media_references(db: AsyncSession, asset: MediaAsset) -> list[str]:
    needle = f"%{asset.stored_name}%"
    refs: list[str] = []
    post_count = (
        await db.execute(
            select(func.count(Post.id)).where(
                or_(Post.content.like(needle), Post.cover_image.like(needle))
            )
        )
    ).scalar_one()
    if post_count:
        refs.append(f"{post_count} 篇文章")
    banner_count = (
        await db.execute(select(func.count(Banner.id)).where(Banner.image.like(needle)))
    ).scalar_one()
    if banner_count:
        refs.append(f"{banner_count} 个轮播图")
    friend_count = (
        await db.execute(select(func.count(FriendLink.id)).where(FriendLink.icon.like(needle)))
    ).scalar_one()
    if friend_count:
        refs.append(f"{friend_count} 条友链图标")
    config_count = (
        await db.execute(select(func.count(SiteConfig.id)).where(SiteConfig.value.like(needle)))
    ).scalar_one()
    if config_count:
        refs.append(f"{config_count} 项站点配置")
    return refs


@router.delete("/admin/media/{media_id}", summary="删除媒体文件（软删除，移入回收站）")
async def delete_media(
    media_id: int,
    _: CurrentUser,
    db: DbDep,
) -> ApiResponse[None]:
    """软删除：仅打标记，文件保留在磁盘，前台已引用的图片继续可访问。"""
    asset = await db.get(MediaAsset, media_id)
    if asset is None or asset.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或已在回收站")
    asset.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    return ok(None)


@router.post("/admin/media/{media_id}/restore", summary="从回收站恢复媒体文件")
async def restore_media(
    media_id: int,
    _: CurrentUser,
    db: DbDep,
) -> ApiResponse[MediaAssetOut]:
    asset = await db.get(MediaAsset, media_id)
    if asset is None or asset.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在或未在回收站")
    if not (settings.upload_path / asset.rel_path).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="磁盘文件已丢失，无法恢复，请彻底删除该记录",
        )
    asset.deleted_at = None
    await db.commit()
    return ok(MediaAssetOut.model_validate(asset))


@router.delete(
    "/admin/media/{media_id}/permanent", summary="彻底删除媒体文件（物理删除，默认带引用保护）"
)
async def permanent_delete_media(
    media_id: int,
    _: CurrentUser,
    db: DbDep,
    force: bool = Query(False),
) -> ApiResponse[None]:
    """物理删除文件与记录：被引用时返回 409，force=true 才放行。"""
    asset = await db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    if not force:
        refs = await _media_references(db, asset)
        if refs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"文件仍被引用：{'、'.join(refs)}。确认后可强制删除",
            )
    (settings.upload_path / asset.rel_path).unlink(missing_ok=True)
    await db.delete(asset)
    await db.commit()
    return ok(None)
