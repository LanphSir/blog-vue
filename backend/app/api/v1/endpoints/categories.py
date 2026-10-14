"""分类与标签端点：公开列表 + 管理端 CRUD。

公开接口把文章计数附加到每个分类/标签上；分类树把子分类挂到父分类下并把子节点
计数上卷到父级。管理端用唯一约束的 IntegrityError 来判断名称/Slug 冲突，
并禁止删除仍含子分类或文章的父分类。
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbDep
from app.crud import category as category_crud
from app.models.post import Category, Post, Tag
from app.schemas.category import (
    CategoryCreate,
    CategoryOut,
    CategoryTreeOut,
    CategoryUpdate,
    TagCreate,
    TagOut,
    TagUpdate,
)
from app.schemas.common import ApiResponse, ok

router = APIRouter()


@router.get("/categories", summary="分类列表（公开）")
async def list_categories(db: DbDep) -> ApiResponse[list[CategoryOut]]:
    categories = await category_crud.list_categories(db)
    counts = await category_crud.count_posts_by_category(db)
    return ok(
        [
            CategoryOut.model_validate(cat).model_copy(update={"post_count": counts.get(cat.id, 0)})
            for cat in categories
        ]
    )


@router.get("/categories/tree", summary="分类树（公开）")
async def list_category_tree(db: DbDep) -> ApiResponse[list[CategoryTreeOut]]:
    categories = await category_crud.list_categories(db)
    counts = await category_crud.count_posts_by_category(db)

    by_id: dict[int, CategoryTreeOut] = {}
    for cat in categories:
        by_id[cat.id] = CategoryTreeOut(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            sort_order=cat.sort_order,
            color=cat.color,
            visible=cat.visible,
            parent_id=cat.parent_id,
            post_count=counts.get(cat.id, 0),
            children=[],
        )

    # 按 parent_id 挂接子节点并上卷计数；无父或父缺失的节点视为根节点
    roots: list[CategoryTreeOut] = []
    for cat in categories:
        node = by_id[cat.id]
        if cat.parent_id is not None and cat.parent_id in by_id:
            parent = by_id[cat.parent_id]
            parent.children.append(node)
            parent.post_count += node.post_count
        else:
            roots.append(node)
    return ok(roots)


@router.get("/tags", summary="标签列表（公开）")
async def list_tags(db: DbDep) -> ApiResponse[list[TagOut]]:
    tags = await category_crud.list_tags(db)
    counts = await category_crud.count_posts_by_tag(db)
    return ok(
        [
            TagOut.model_validate(tag).model_copy(update={"post_count": counts.get(tag.id, 0)})
            for tag in tags
        ]
    )


@router.post("/admin/categories", summary="创建分类", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate, db: DbDep, _: CurrentUser
) -> ApiResponse[CategoryOut]:
    category = Category(**payload.model_dump())
    db.add(category)
    try:
        await db.commit()
    except IntegrityError:
        # 名称/Slug 有唯一约束，靠数据库约束捕获冲突比先查后写更可靠（无竞态窗口）
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="分类名称或 Slug 已存在"
        ) from None
    await db.refresh(category)
    return ok(CategoryOut.model_validate(category))


@router.put("/admin/categories/{category_id}", summary="更新分类")
async def update_category(
    category_id: int, payload: CategoryUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[CategoryOut]:
    category = await category_crud.get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="分类名称或 Slug 已存在"
        ) from None
    await db.refresh(category)
    return ok(CategoryOut.model_validate(category))


@router.delete("/admin/categories/{category_id}", summary="删除分类")
async def delete_category(category_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    category = await category_crud.get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    has_children = (
        await db.execute(select(func.count(Category.id)).where(Category.parent_id == category_id))
    ).scalar_one()
    if has_children > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="该分类下存在子分类，无法删除"
        )
    post_count = (
        await db.execute(select(func.count(Post.id)).where(Post.category_id == category_id))
    ).scalar_one()
    if post_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"该分类下存在 {post_count} 篇文章，请先移出或删除后再操作",
        )
    await db.delete(category)
    await db.commit()
    return ok(None)


@router.post("/admin/tags", summary="创建标签", status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, db: DbDep, _: CurrentUser) -> ApiResponse[TagOut]:
    tag = Tag(**payload.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return ok(TagOut.model_validate(tag))


@router.put("/admin/tags/{tag_id}", summary="更新标签")
async def update_tag(
    tag_id: int, payload: TagUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[TagOut]:
    tag = await category_crud.get_tag_by_id(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return ok(TagOut.model_validate(tag))


@router.delete("/admin/tags/{tag_id}", summary="删除标签")
async def delete_tag(tag_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    tag = await category_crud.get_tag_by_id(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    await db.delete(tag)
    await db.commit()
    return ok(None)
