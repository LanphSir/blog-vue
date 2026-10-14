"""公告端点：公开列表/详情 + 管理端 CRUD（内容变更自动升版本）。

公开列表会隐去 page 类型公告的正文（避免把整页内容暴露给列表请求），详情接口
才返回正文，且禁用中的公告详情按 404 处理。管理端更新时若标题或正文有变化会
自动递增 version，前端据此判断是否该重新弹窗（localStorage 记忆版本号）。
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbDep
from app.crud import site as site_crud
from app.models.site import Notice
from app.schemas.common import ApiResponse, ok
from app.schemas.site import NoticeCreate, NoticeOut, NoticeUpdate

router = APIRouter()

NOTICE_TYPES = {"banner", "dialog", "page"}


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _to_out(notice: Notice, hide_content: bool = False) -> NoticeOut:
    item = NoticeOut.model_validate(notice)
    # page 类型公告正文很长，列表接口不返回，避免把整页内容塞进列表响应
    if hide_content and notice.type == "page":
        item.content = None
    return item


@router.get("/notices", summary="公告列表（公开）")
async def list_notices(db: DbDep) -> ApiResponse[list[NoticeOut]]:
    notices = await site_crud.list_notices(db, enabled_only=True)
    return ok([_to_out(n, hide_content=True) for n in notices])


@router.get("/notices/{notice_id}", summary="公告详情（公开）")
async def get_notice_detail(notice_id: int, db: DbDep) -> ApiResponse[NoticeOut]:
    notice = await site_crud.get_notice(db, notice_id)
    if notice is None or not notice.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    return ok(NoticeOut.model_validate(notice))


@router.get("/admin/notices", summary="公告管理列表")
async def admin_list_notices(db: DbDep, _: CurrentUser) -> ApiResponse[list[NoticeOut]]:
    notices = await site_crud.list_notices(db)
    return ok([NoticeOut.model_validate(n) for n in notices])


@router.post("/admin/notices", summary="创建公告", status_code=status.HTTP_201_CREATED)
async def create_notice(payload: NoticeCreate, db: DbDep, _: CurrentUser) -> ApiResponse[NoticeOut]:
    if payload.type not in NOTICE_TYPES:
        raise _bad_request("公告类型无效（banner/dialog/page）")
    notice = Notice(**payload.model_dump())
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return ok(NoticeOut.model_validate(notice))


@router.put("/admin/notices/{notice_id}", summary="更新公告（内容变更自动升版本）")
async def update_notice(
    notice_id: int, payload: NoticeUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[NoticeOut]:
    notice = await site_crud.get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")

    changes = payload.model_dump(exclude_unset=True)
    if "type" in changes and changes["type"] not in NOTICE_TYPES:
        raise _bad_request("公告类型无效（banner/dialog/page）")

    content_changed = ("title" in changes and changes["title"] != notice.title) or (
        "content" in changes and changes["content"] != notice.content
    )
    for field, value in changes.items():
        setattr(notice, field, value)
    if content_changed:
        # 标题/正文变更即升版本，前端按版本号判断本地是否已读过，从而决定是否再次展示
        notice.version += 1

    await db.commit()
    await db.refresh(notice)
    return ok(NoticeOut.model_validate(notice))


@router.delete("/admin/notices/{notice_id}", summary="删除公告")
async def delete_notice(notice_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    notice = await site_crud.get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    await db.delete(notice)
    await db.commit()
    return ok(None)
