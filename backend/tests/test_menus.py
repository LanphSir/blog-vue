"""Navigation menu CRUD, public tree composition, validation rules."""


def _login(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_public_menus_fallback_when_table_empty(client):
    resp = client.get("/api/v1/menus")
    assert resp.status_code == 200
    menus = resp.json()["data"]
    assert menus[0]["label"] == "首页"
    assert menus[0]["path"] == "/"
    paths = [m["path"] for m in menus]
    assert "/posts" in paths and "/tags" in paths and "/friends" in paths and "/about" in paths


def test_menu_crud_and_public_tree(client):
    headers = _login(client)

    posts = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "文章", "path": "/posts", "icon": "Document", "sort_order": 1},
    )
    assert posts.status_code == 201
    posts_id = posts.json()["data"]["id"]

    category = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "栏目", "type": "category", "icon": "Grid", "sort_order": 2},
    )
    assert category.status_code == 201

    child = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "归档", "path": "/categories", "parent_id": posts_id, "sort_order": 1},
    )
    assert child.status_code == 201

    menus = client.get("/api/v1/menus").json()["data"]
    # fallback is replaced once the table is non-empty: home + posts + category only
    assert [m["label"] for m in menus] == ["首页", "文章", "栏目"]
    assert menus[1]["icon"] == "Document"
    assert [c["label"] for c in menus[1]["children"]] == ["归档"]
    assert menus[2]["type"] == "category"
    assert menus[2]["children"] == []

    admin_list = client.get("/api/v1/admin/menus", headers=headers).json()["data"]
    assert any(m["label"] == "归档" for m in admin_list)


def test_hidden_parent_hides_children(client):
    headers = _login(client)

    parent = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "隐藏父", "path": "/p", "visible": False},
    ).json()["data"]
    client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "可见子", "path": "/c", "parent_id": parent["id"]},
    )

    menus = client.get("/api/v1/menus").json()["data"]
    labels = [m["label"] for m in menus]
    assert "隐藏父" not in labels
    assert "可见子" not in "".join(c["label"] for m in menus for c in m.get("children", []))

    admin_labels = [
        m["label"] for m in client.get("/api/v1/admin/menus", headers=headers).json()["data"]
    ]
    assert "隐藏父" in admin_labels and "可见子" in admin_labels


def test_menu_validation_rules(client):
    headers = _login(client)

    top = client.post(
        "/api/v1/admin/menus", headers=headers, json={"label": "父", "path": "/top"}
    ).json()["data"]
    child = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "子", "path": "/child", "parent_id": top["id"]},
    ).json()["data"]

    # third level rejected
    bad = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "孙", "path": "/g", "parent_id": child["id"]},
    )
    assert bad.status_code == 422

    # internal link requires leading-slash path
    assert (
        client.post("/api/v1/admin/menus", headers=headers, json={"label": "无路径"}).status_code
        == 422
    )

    # external requires http(s) url
    assert (
        client.post(
            "/api/v1/admin/menus",
            headers=headers,
            json={"label": "外链", "path": "ftp://x.com", "is_external": True},
        ).status_code
        == 422
    )

    ok_external = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "外链", "path": "https://example.com", "is_external": True},
    )
    assert ok_external.status_code == 201

    # category must stay top-level
    assert (
        client.post(
            "/api/v1/admin/menus",
            headers=headers,
            json={"label": "子栏目", "type": "category", "parent_id": top["id"]},
        ).status_code
        == 422
    )

    # parent must exist
    assert (
        client.post(
            "/api/v1/admin/menus",
            headers=headers,
            json={"label": "x", "path": "/x", "parent_id": 999},
        ).status_code
        == 422
    )

    # cannot attach a node that already has children below another node
    assert (
        client.put(
            f"/api/v1/admin/menus/{top['id']}",
            headers=headers,
            json={"parent_id": child["id"]},
        ).status_code
        == 422
    )

    # cannot be own parent
    assert (
        client.put(
            f"/api/v1/admin/menus/{top['id']}", headers=headers, json={"parent_id": top["id"]}
        ).status_code
        == 422
    )

    # invalid type
    assert (
        client.post(
            "/api/v1/admin/menus",
            headers=headers,
            json={"label": "x", "path": "/x", "type": "weird"},
        ).status_code
        == 422
    )


def test_menu_update_and_delete_cascades_children(client):
    headers = _login(client)

    parent = client.post(
        "/api/v1/admin/menus", headers=headers, json={"label": "父", "path": "/p"}
    ).json()["data"]
    child = client.post(
        "/api/v1/admin/menus",
        headers=headers,
        json={"label": "子", "path": "/c", "parent_id": parent["id"]},
    ).json()["data"]

    updated = client.put(
        f"/api/v1/admin/menus/{parent['id']}",
        headers=headers,
        json={"label": "改名", "icon": "Star"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["label"] == "改名"

    assert client.delete(f"/api/v1/admin/menus/{parent['id']}", headers=headers).status_code == 200
    admin_ids = [m["id"] for m in client.get("/api/v1/admin/menus", headers=headers).json()["data"]]
    assert parent["id"] not in admin_ids
    assert child["id"] not in admin_ids


def test_menus_require_auth_for_admin(client):
    assert client.post("/api/v1/admin/menus", json={"label": "x", "path": "/x"}).status_code == 401
    assert client.get("/api/v1/admin/menus").status_code == 401


async def test_legacy_site_menus_migration(db_session):
    import json

    from app.crud import site as site_crud
    from app.seed import _migrate_menus

    async with db_session() as db:
        await site_crud.set_config(
            db,
            "site_menus",
            json.dumps(
                [
                    {"label": "首页", "path": "/"},
                    {
                        "label": "文章",
                        "path": "/posts",
                        "children": [{"label": "归档", "path": "/categories"}],
                    },
                    {"label": "专栏", "type": "category"},
                    {"path": "/missing-label"},
                ]
            ),
        )
        await db.commit()

        await _migrate_menus(db)
        menus = await site_crud.list_menus(db)
        assert len(menus) == 4  # 首页/文章/归档/专栏; broken item skipped
        category = next(m for m in menus if m.type == "category")
        assert category.parent_id is None and category.path is None
        child = next(m for m in menus if m.label == "归档")
        parent = next(m for m in menus if m.label == "文章")
        assert child.parent_id == parent.id

        await _migrate_menus(db)  # idempotent only while table empty→second run sees data
        assert len(await site_crud.list_menus(db)) == 4


async def test_legacy_site_menus_migration_invalid_json(db_session):
    from app.crud import site as site_crud
    from app.seed import _migrate_menus

    async with db_session() as db:
        await site_crud.set_config(db, "site_menus", "{not json")
        await db.commit()
        await _migrate_menus(db)
        assert await site_crud.list_menus(db) == []


async def test_default_menus_seeded_once(db_session):
    from app.crud import site as site_crud
    from app.seed import _seed_default_menus

    async with db_session() as db:
        await _seed_default_menus(db)
        menus = await site_crud.list_menus(db)
        assert [m.label for m in menus] == ["文章", "标签", "友链", "关于"]
        assert all(m.parent_id is None and m.visible and m.icon for m in menus)

        await _seed_default_menus(db)  # marker prevents re-seed
        assert len(await site_crud.list_menus(db)) == 4


async def test_default_menus_never_reseeded_after_user_deletes(db_session):
    from app.crud import site as site_crud
    from app.seed import _seed_default_menus

    async with db_session() as db:
        await _seed_default_menus(db)
        for menu in await site_crud.list_menus(db):
            await db.delete(menu)
        await db.commit()

        await _seed_default_menus(db)
        assert await site_crud.list_menus(db) == []


async def test_default_menus_skip_when_legacy_migrated(db_session):
    import json

    from app.crud import site as site_crud
    from app.seed import _migrate_menus, _seed_default_menus

    async with db_session() as db:
        await site_crud.set_config(db, "site_menus", json.dumps([{"label": "旧", "path": "/old"}]))
        await db.commit()
        await _migrate_menus(db)
        await _seed_default_menus(db)
        assert [m.label for m in await site_crud.list_menus(db)] == ["旧"]
