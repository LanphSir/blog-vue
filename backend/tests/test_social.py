"""Social link CRUD, public visible filtering, URL validation."""


def _login(client):
    login = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_social_link_crud_and_public_visibility(client):
    headers = _login(client)

    created = client.post(
        "/api/v1/admin/social-links",
        headers=headers,
        json={"platform": "github", "url": "https://github.com/me", "sort_order": 1},
    )
    assert created.status_code == 201

    client.post(
        "/api/v1/admin/social-links",
        headers=headers,
        json={
            "platform": "custom",
            "label": "我的博客",
            "url": "https://me.example.com",
            "sort_order": 2,
            "visible": False,
        },
    )

    public = client.get("/api/v1/social-links").json()["data"]
    assert [s["platform"] for s in public] == ["github"]

    admin_list = client.get("/api/v1/admin/social-links", headers=headers).json()["data"]
    assert len(admin_list) == 2

    gid = created.json()["data"]["id"]
    updated = client.put(
        f"/api/v1/admin/social-links/{gid}",
        headers=headers,
        json={"url": "https://github.com/other", "sort_order": 5},
    )
    assert updated.json()["data"]["url"] == "https://github.com/other"

    assert client.delete(f"/api/v1/admin/social-links/{gid}", headers=headers).status_code == 200
    assert client.get("/api/v1/social-links").json()["data"] == []


def test_social_link_url_validation(client):
    headers = _login(client)

    assert (
        client.post(
            "/api/v1/admin/social-links",
            headers=headers,
            json={"platform": "github", "url": "github.com/me"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/admin/social-links", headers=headers, json={"platform": "github", "url": ""}
        ).status_code
        == 422
    )
    ok_mail = client.post(
        "/api/v1/admin/social-links",
        headers=headers,
        json={"platform": "email", "url": "mailto:me@example.com"},
    )
    assert ok_mail.status_code == 201


async def test_legacy_profile_links_migration(db_session):
    import json

    from app.crud import site as site_crud
    from app.seed import _migrate_social_links

    async with db_session() as db:
        await site_crud.set_config(
            db,
            "profile_links",
            json.dumps(
                [
                    {"platform": "github", "url": "https://github.com/me"},
                    {"platform": "juejin", "url": "https://juejin.cn/x", "visible": False},
                    {"url": "https://missing-platform.com"},
                    {"platform": "email"},
                    "not-a-dict",
                ]
            ),
        )
        await db.commit()

        await _migrate_social_links(db)
        links = await site_crud.list_social_links(db)
        assert [(s.platform, s.visible) for s in links] == [("github", True), ("juejin", False)]

        await _migrate_social_links(db)  # idempotent
        assert len(await site_crud.list_social_links(db)) == 2


async def test_legacy_profile_links_migration_invalid_json(db_session):
    from app.crud import site as site_crud
    from app.seed import _migrate_social_links

    async with db_session() as db:
        await site_crud.set_config(db, "profile_links", "[broken")
        await db.commit()
        await _migrate_social_links(db)
        assert await site_crud.list_social_links(db) == []
