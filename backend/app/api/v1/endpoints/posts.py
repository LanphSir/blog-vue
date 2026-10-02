"""Post endpoints: public browsing + admin CRUD."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbDep
from app.crud import category as category_crud
from app.crud import post as post_crud
from app.models.post import Post, Tag
from app.schemas.common import ApiResponse, PageData, ok
from app.schemas.post import (
    PostCreate,
    PostDetailOut,
    PostListOut,
    PostNeighbor,
    PostNeighborsOut,
    PostOut,
    PostUpdate,
)

router = APIRouter()


async def _apply_tags(db: DbDep, post: Post, tag_ids: list[int]) -> None:
    if not tag_ids:
        return
    rows = (await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))).scalars().all()
    post.tags = list(rows)


# ---------------- Public ----------------


@router.get("/posts", summary="文章列表（公开）")
async def list_posts(
    db: DbDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category_id: int | None = None,
    tag_id: int | None = None,
    keyword: str | None = None,
) -> ApiResponse[PageData[PostListOut]]:
    if category_id is not None:
        category_ids = await category_crud.get_descendant_category_ids(db, category_id)
    else:
        category_ids = None
    items, total = await post_crud.list_posts(
        db,
        page=page,
        page_size=page_size,
        status="published",
        category_id=category_ids,
        tag_id=tag_id,
        keyword=keyword,
    )
    for post in items:
        await db.refresh(post, attribute_names=["category", "tags"])
    return ok(
        PageData(
            items=[PostListOut.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/posts/{slug}", summary="文章详情（公开）")
async def get_post(db: DbDep, slug: str) -> ApiResponse[PostDetailOut]:
    post = await post_crud.get_by_slug(db, slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    await post_crud.increment_view_count(db, post)
    await db.refresh(post)
    await db.refresh(post, attribute_names=["tags"])
    return ok(PostDetailOut.model_validate(post))


@router.get("/posts/{slug}/neighbors", summary="文章上一篇/下一篇（公开）")
async def get_neighbors(db: DbDep, slug: str) -> ApiResponse[PostNeighborsOut]:
    post = await post_crud.get_by_slug(db, slug)
    if post is None or post.status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    previous, next_post = await post_crud.get_neighbors(db, post)
    return ok(
        PostNeighborsOut(
            previous=PostNeighbor.model_validate(previous) if previous else None,
            next=PostNeighbor.model_validate(next_post) if next_post else None,
        )
    )


# ---------------- Admin ----------------


@router.get("/admin/posts", summary="文章管理列表")
async def admin_list_posts(
    db: DbDep,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
) -> ApiResponse[PageData[PostOut]]:
    items, total = await post_crud.list_posts(
        db, page=page, page_size=page_size, status=status, keyword=keyword
    )
    return ok(
        PageData(
            items=[PostOut.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/admin/posts/{post_id}", summary="文章详情（管理）")
async def admin_get_post(post_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[PostDetailOut]:
    post = await post_crud.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    await db.refresh(post, attribute_names=["tags"])
    return ok(PostDetailOut.model_validate(post))


@router.post("/admin/posts", summary="创建文章", status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: DbDep, _: CurrentUser) -> ApiResponse[PostOut]:
    post = await post_crud.create_post(db, payload)
    await _apply_tags(db, post, payload.tag_ids)
    await db.commit()
    await db.refresh(post)
    return ok(PostOut.model_validate(post))


@router.put("/admin/posts/{post_id}", summary="更新文章")
async def update_post(
    post_id: int, payload: PostUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[PostOut]:
    post = await post_crud.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    post = await post_crud.update_post(db, post, payload)
    if payload.tag_ids is not None:
        await _apply_tags(db, post, payload.tag_ids)
    await db.commit()
    await db.refresh(post)
    return ok(PostOut.model_validate(post))


@router.delete("/admin/posts/{post_id}", summary="删除文章")
async def delete_post(post_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    post = await post_crud.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    await post_crud.delete_post(db, post)
    await db.commit()
    return ok(None)
