"""File upload endpoint (images) for the admin panel."""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUser
from app.core.config import settings
from app.schemas.common import ApiResponse, ok

logger = logging.getLogger("blog")

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("/admin/upload", summary="上传图片", status_code=status.HTTP_201_CREATED)
async def upload_image(
    _: CurrentUser,
    file: UploadFile = File(...),
) -> ApiResponse[str]:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式：{ext or '未知'}",
        )

    upload_dir = settings.upload_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / filename

    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件超过 {settings.max_upload_size_mb}MB 限制",
                    )
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    logger.info("Uploaded %s (%d bytes)", filename, size)
    return ok(f"/uploads/{filename}")
