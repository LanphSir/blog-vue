"""Notice CRUD, version bump, public list/detail rules."""


def _login(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_notice_crud_and_public_rules(client):
    headers = _login(client)

    banner = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "系统维护", "content": "今晚 10 点维护", "type": "banner", "sort_order": 1},
    )
    assert banner.status_code == 201
    assert banner.json()["data"]["version"] == 1

    dialog = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "新版本发布", "content": "# v2\n\n**新功能**", "type": "dialog"},
    )
    assert dialog.status_code == 201

    page = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "社区公约", "content": "长文公告正文", "type": "page"},
    )
    assert page.status_code == 201

    disabled = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "停用公告", "content": "x", "type": "banner", "enabled": False},
    )
    assert disabled.status_code == 201

    public = client.get("/api/v1/notices").json()["data"]
    titles = [n["title"] for n in public]
    assert "停用公告" not in titles
    by_type = {n["type"]: n for n in public}
    assert by_type["banner"]["content"] == "今晚 10 点维护"
    assert by_type["dialog"]["content"].startswith("# v2")
    assert by_type["page"]["content"] is None  # 列表不含单页正文，防大文本拖慢

    detail = client.get(f"/api/v1/notices/{page.json()['data']['id']}")
    assert detail.json()["data"]["content"] == "长文公告正文"

    assert client.get(f"/api/v1/notices/{disabled.json()['data']['id']}").status_code == 404

    admin_list = client.get("/api/v1/admin/notices", headers=headers).json()["data"]
    assert len(admin_list) == 4

    assert client.delete(f"/api/v1/admin/notices/{banner.json()['data']['id']}", headers=headers)


def test_notice_version_bumps_only_on_content_changes(client):
    headers = _login(client)
    created = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "T", "content": "C", "type": "dialog"},
    ).json()["data"]
    nid = created["id"]

    bumped = client.put(
        f"/api/v1/admin/notices/{nid}", headers=headers, json={"content": "修改后的正文"}
    )
    assert bumped.json()["data"]["version"] == 2

    renamed = client.put(f"/api/v1/admin/notices/{nid}", headers=headers, json={"title": "新标题"})
    assert renamed.json()["data"]["version"] == 3

    toggled = client.put(
        f"/api/v1/admin/notices/{nid}", headers=headers, json={"enabled": False, "sort_order": 9}
    )
    assert toggled.json()["data"]["version"] == 3  # 非内容字段不加版本


def test_notice_type_validation(client):
    headers = _login(client)
    assert (
        client.post(
            "/api/v1/admin/notices",
            headers=headers,
            json={"title": "x", "content": "y", "type": "popup"},
        ).status_code
        == 422
    )
    created = client.post(
        "/api/v1/admin/notices",
        headers=headers,
        json={"title": "x", "content": "y", "type": "banner"},
    ).json()["data"]
    assert (
        client.put(
            f"/api/v1/admin/notices/{created['id']}", headers=headers, json={"type": "sms"}
        ).status_code
        == 422
    )


def test_notices_require_auth_for_admin(client):
    assert client.get("/api/v1/admin/notices").status_code == 401
    assert (
        client.post("/api/v1/admin/notices", json={"title": "x", "content": "y"}).status_code == 401
    )


async def test_legacy_notice_migration(db_session):
    from app.crud import site as site_crud
    from app.seed import _migrate_notice

    async with db_session() as db:
        await site_crud.set_config(db, "notice_text", "旧版横幅公告")
        await site_crud.set_config(db, "notice_enabled", "false")
        await site_crud.set_config(db, "notice_version", "7")
        await db.commit()

        await _migrate_notice(db)
        notices = await site_crud.list_notices(db)
        assert len(notices) == 1
        assert notices[0].type == "banner"
        assert notices[0].enabled is False
        assert notices[0].version == 7
        assert notices[0].title == "网站公告"

        await _migrate_notice(db)  # idempotent
        assert len(await site_crud.list_notices(db)) == 1


async def test_legacy_notice_migration_skips_empty(db_session):
    from app.crud import site as site_crud
    from app.seed import _migrate_notice

    async with db_session() as db:
        await site_crud.set_config(db, "notice_text", "")
        await db.commit()
        await _migrate_notice(db)
        assert await site_crud.list_notices(db) == []
