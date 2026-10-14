"""导航菜单端点：公开组合树 + 管理端 CRUD。

公开树把"首页"作为合成节点固定放在首位（不入库），并跳过隐藏菜单及其子项；
当菜单表为空时回退到内置默认菜单，保证即使配置被清空站点导航也能用。
管理端强制约束：最多两级、"栏目下拉必须位于顶级"等（见 _validate_menu）。
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbDep
from app.crud import site as site_crud
from app.models.site import MenuItem
from app.schemas.common import ApiResponse, ok
from app.schemas.site import MenuItemCreate, MenuItemOut, MenuItemUpdate, MenuNodeOut

router = APIRouter()

MENU_TYPES = {"link", "category"}

DEFAULT_EXTRA_MENUS = [
    ("文章", "/posts", "Document"),
    ("标签", "/tags", "PriceTag"),
    ("友链", "/friends", "Link"),
    ("关于", "/about", "InfoFilled"),
]


def _home_node() -> MenuNodeOut:
    return MenuNodeOut(label="首页", path="/", icon="HomeFilled", type="link", is_external=False)


def _default_menus() -> list[MenuNodeOut]:
    nodes = [_home_node()]
    for label, path, icon in DEFAULT_EXTRA_MENUS:
        nodes.append(MenuNodeOut(label=label, path=path, icon=icon, type="link", is_external=False))
    return nodes


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


async def _validate_menu(
    db,
    *,
    path: str | None,
    menu_type: str,
    is_external: bool,
    parent_id: int | None,
    current_id: int | None = None,
) -> None:
    if menu_type not in MENU_TYPES:
        raise _bad_request("菜单类型无效（link/category）")
    if menu_type == "category":
        if parent_id is not None:
            raise _bad_request("栏目下拉菜单必须位于顶级")
        return
    if parent_id is not None:
        if parent_id == current_id:
            raise _bad_request("菜单不能是自己的子项")
        parent = await site_crud.get_menu(db, parent_id)
        if parent is None:
            raise _bad_request("父级菜单不存在")
        if parent.parent_id is not None or parent.type == "category":
            raise _bad_request("导航最多支持两级，且栏目下拉不能有父级")
    if is_external:
        if not path or not path.startswith(("http://", "https://")):
            raise _bad_request("外链必须是 http(s) 地址")
    elif not path or not path.startswith("/"):
        raise _bad_request("站内路径必须以 / 开头")


@router.get("/menus", summary="导航菜单（公开树）")
async def get_menus(db: DbDep) -> ApiResponse[list[MenuNodeOut]]:
    menus = await site_crud.list_menus(db)
    if not menus:
        # 空表回退到内置默认菜单，避免用户删光菜单后站点导航失效
        return ok(_default_menus())

    # 只取可见菜单；隐藏的父项会连同其子项一并被跳过（子项挂在隐藏父下不可达）
    visible = [m for m in menus if m.visible]
    children_map: dict[int, list[MenuNodeOut]] = {}
    for m in visible:
        if m.parent_id is not None:
            children_map.setdefault(m.parent_id, []).append(
                MenuNodeOut(
                    label=m.label,
                    path=m.path,
                    icon=m.icon,
                    type=m.type,
                    is_external=m.is_external,
                )
            )
    nodes = [_home_node()]
    for m in visible:
        if m.parent_id is not None:
            continue
        nodes.append(
            MenuNodeOut(
                label=m.label,
                path=m.path,
                icon=m.icon,
                type=m.type,
                is_external=m.is_external,
                children=children_map.get(m.id, []),
            )
        )
    return ok(nodes)


@router.get("/admin/menus", summary="导航菜单管理列表")
async def admin_list_menus(db: DbDep, _: CurrentUser) -> ApiResponse[list[MenuItemOut]]:
    menus = await site_crud.list_menus(db)
    return ok([MenuItemOut.model_validate(m) for m in menus])


@router.post("/admin/menus", summary="创建菜单", status_code=status.HTTP_201_CREATED)
async def create_menu(
    payload: MenuItemCreate, db: DbDep, _: CurrentUser
) -> ApiResponse[MenuItemOut]:
    await _validate_menu(
        db,
        path=payload.path,
        menu_type=payload.type,
        is_external=payload.is_external,
        parent_id=payload.parent_id,
    )
    data = payload.model_dump()
    if payload.type == "category":
        data["path"] = None
        data["is_external"] = False
    menu = MenuItem(**data)
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return ok(MenuItemOut.model_validate(menu))


@router.put("/admin/menus/{menu_id}", summary="更新菜单")
async def update_menu(
    menu_id: int, payload: MenuItemUpdate, db: DbDep, _: CurrentUser
) -> ApiResponse[MenuItemOut]:
    menu = await site_crud.get_menu(db, menu_id)
    if menu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜单不存在")

    changes = payload.model_dump(exclude_unset=True)
    merged = {
        "label": menu.label,
        "path": menu.path,
        "icon": menu.icon,
        "type": menu.type,
        "is_external": menu.is_external,
        "parent_id": menu.parent_id,
        "sort_order": menu.sort_order,
        "visible": menu.visible,
    }
    merged.update(changes)

    await _validate_menu(
        db,
        path=merged["path"],
        menu_type=merged["type"],
        is_external=merged["is_external"],
        parent_id=merged["parent_id"],
        current_id=menu_id,
    )
    if merged["type"] == "category":
        merged["path"] = None
        merged["is_external"] = False
    if merged["parent_id"] is not None:
        all_menus = await site_crud.list_menus(db)
        if any(m.parent_id == menu_id for m in all_menus):
            raise _bad_request("该菜单含子项，不能降级为二级菜单")

    for field, value in merged.items():
        setattr(menu, field, value)
    await db.commit()
    await db.refresh(menu)
    return ok(MenuItemOut.model_validate(menu))


@router.delete("/admin/menus/{menu_id}", summary="删除菜单（连带子项）")
async def delete_menu(menu_id: int, db: DbDep, _: CurrentUser) -> ApiResponse[None]:
    menu = await site_crud.get_menu(db, menu_id)
    if menu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜单不存在")
    all_menus = await site_crud.list_menus(db)
    for child in all_menus:
        if child.parent_id == menu_id:
            await db.delete(child)
    await db.delete(menu)
    await db.commit()
    return ok(None)
