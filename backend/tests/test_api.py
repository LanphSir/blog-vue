"""Basic API smoke tests: auth, posts, categories, site config."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_wrong_password(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_site_config_seeded(client):
    resp = client.get("/api/v1/site/config")
    assert resp.status_code == 200
    keys = {item["key"] for item in resp.json()["data"]}
    assert "site_name" in keys


def test_admin_create_and_publish_post(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={
            "title": "第一篇测试文章",
            "slug": "first-post",
            "content": "# Hello",
            "status": "published",
        },
    )
    assert created.status_code == 201

    listed = client.get("/api/v1/posts")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    detail = client.get("/api/v1/posts/first-post")
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "第一篇测试文章"

    assert client.get("/api/v1/posts/not-exist").status_code == 404


def test_post_neighbors(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={"title": "第一篇", "slug": "post-a", "status": "published"},
    )
    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={"title": "第二篇", "slug": "post-b", "status": "published"},
    )

    resp = client.get("/api/v1/posts/post-a/neighbors")
    assert resp.status_code == 200
    assert resp.json()["data"]["previous"] is None
    assert resp.json()["data"]["next"]["slug"] == "post-b"

    resp = client.get("/api/v1/posts/post-b/neighbors")
    assert resp.json()["data"]["previous"]["slug"] == "post-a"
    assert resp.json()["data"]["next"] is None


def test_admin_tags_crud(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    created = client.post(
        "/api/v1/admin/tags", headers=headers, json={"name": "Vue", "slug": "vue"}
    )
    assert created.status_code == 201
    tag_id = created.json()["data"]["id"]

    listed = client.get("/api/v1/tags")
    assert any(tag["slug"] == "vue" for tag in listed.json()["data"])

    updated = client.put(f"/api/v1/admin/tags/{tag_id}", headers=headers, json={"name": "Vue3"})
    assert updated.json()["data"]["name"] == "Vue3"

    deleted = client.delete(f"/api/v1/admin/tags/{tag_id}", headers=headers)
    assert deleted.status_code == 200


def test_upload_requires_auth_and_rejects_bad_type(client):
    unauth = client.post(
        "/api/v1/admin/upload",
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert unauth.status_code == 401

    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    bad = client.post(
        "/api/v1/admin/upload",
        headers=headers,
        files={"file": ("x.txt", b"hello", "text/plain")},
    )
    assert bad.status_code == 400

    ok_resp = client.post(
        "/api/v1/admin/upload",
        headers=headers,
        files={"file": ("cover.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png")},
    )
    assert ok_resp.status_code == 201
    assert ok_resp.json()["data"].startswith("/uploads/")


def _login(client):
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_category_tree_hierarchy_and_parent_filter(client):
    headers = _login(client)

    parent = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "后端开发", "slug": "backend", "color": "#2563EB"},
    ).json()["data"]
    child = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "数据库", "slug": "database", "parent_id": parent["id"]},
    ).json()["data"]

    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={
            "title": "数据库文章",
            "slug": "db-post",
            "category_id": child["id"],
            "status": "published",
        },
    )

    tree = client.get("/api/v1/categories/tree").json()["data"]
    node = next(c for c in tree if c["slug"] == "backend")
    assert [ch["slug"] for ch in node["children"]] == ["database"]
    assert node["post_count"] == 1

    filtered = client.get(f"/api/v1/posts?category_id={parent['id']}").json()["data"]
    assert filtered["total"] == 1
    assert filtered["items"][0]["slug"] == "db-post"

    blocked = client.delete(f"/api/v1/admin/categories/{parent['id']}", headers=headers)
    assert blocked.status_code == 409


def test_banners_and_site_stats(client):
    headers = _login(client)

    created = client.post(
        "/api/v1/admin/banners",
        headers=headers,
        json={"title": "轮播一", "subtitle": "介绍", "sort_order": 1, "enabled": True},
    )
    assert created.status_code == 201
    client.post(
        "/api/v1/admin/banners",
        headers=headers,
        json={"title": "隐藏轮播", "sort_order": 2, "enabled": False},
    )

    public = client.get("/api/v1/banners").json()["data"]
    assert [b["title"] for b in public] == ["轮播一"]

    admin_list = client.get("/api/v1/admin/banners", headers=headers).json()["data"]
    assert len(admin_list) == 2

    stats = client.get("/api/v1/site/stats").json()["data"]
    assert stats["post_count"] >= 0
    assert stats["category_count"] >= 0
    assert stats["total_views"] >= 0


def test_category_color_roundtrip(client):
    headers = _login(client)
    created = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "随笔", "slug": "notes", "color": "#EA580C"},
    ).json()["data"]
    assert created["color"] == "#EA580C"

    listed = client.get("/api/v1/categories").json()["data"]
    assert any(c["slug"] == "notes" and c["color"] == "#EA580C" for c in listed)


def test_post_sort_weight_featured_and_author(client):
    headers = _login(client)

    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={"title": "普通", "slug": "p-normal", "status": "published", "sort_weight": 0},
    )
    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={
            "title": "加权",
            "slug": "p-weighted",
            "status": "published",
            "sort_weight": 50,
            "author": "作者乙",
        },
    )
    client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={
            "title": "推荐",
            "slug": "p-featured",
            "status": "published",
            "sort_weight": 20,
            "is_featured": True,
            "author": "站长",
        },
    )

    titles = [p["title"] for p in client.get("/api/v1/posts").json()["data"]["items"]]
    assert titles[:3] == ["加权", "推荐", "普通"]

    detail = client.get("/api/v1/posts/p-weighted").json()["data"]
    assert detail["author"] == "作者乙"
    assert detail["is_featured"] is False
    assert detail["sort_weight"] == 50


def test_category_and_tag_visibility_flags(client):
    headers = _login(client)

    hidden = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "隐藏栏目", "slug": "hidden-cat", "visible": False},
    ).json()["data"]
    assert hidden["visible"] is False

    tag = client.post(
        "/api/v1/admin/tags",
        headers=headers,
        json={"name": "私密标签", "slug": "private-tag", "visible": False, "sort_order": 3},
    ).json()["data"]
    assert tag["visible"] is False
    assert tag["sort_order"] == 3

    tree = client.get("/api/v1/categories/tree").json()["data"]
    assert next(c for c in tree if c["slug"] == "hidden-cat")["visible"] is False

    tags = client.get("/api/v1/tags").json()["data"]
    assert next(t for t in tags if t["slug"] == "private-tag")["sort_order"] == 3


def test_post_soft_delete_restore_permanent(client):
    headers = _login(client)

    created = client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={"title": "回收测试", "slug": "recycle-test", "status": "published"},
    ).json()["data"]
    pid = created["id"]

    # soft delete → goes to recycle bin, disappears from normal/public lists
    assert client.delete(f"/api/v1/admin/posts/{pid}", headers=headers).status_code == 200
    normal_ids = [
        p["id"]
        for p in client.get("/api/v1/admin/posts?page_size=100", headers=headers).json()["data"][
            "items"
        ]
    ]
    assert pid not in normal_ids
    deleted_ids = [
        p["id"]
        for p in client.get(
            "/api/v1/admin/posts?deleted=true&page_size=100", headers=headers
        ).json()["data"]["items"]
    ]
    assert pid in deleted_ids
    public_slugs = [
        p["slug"] for p in client.get("/api/v1/posts?page_size=50").json()["data"]["items"]
    ]
    assert "recycle-test" not in public_slugs

    # restore → back in normal list
    assert client.post(f"/api/v1/admin/posts/{pid}/restore", headers=headers).status_code == 200
    normal_ids = [
        p["id"]
        for p in client.get("/api/v1/admin/posts?page_size=100", headers=headers).json()["data"][
            "items"
        ]
    ]
    assert pid in normal_ids

    # permanent delete → removed everywhere including recycle bin
    assert client.delete(f"/api/v1/admin/posts/{pid}/permanent", headers=headers).status_code == 200
    deleted_ids = [
        p["id"]
        for p in client.get(
            "/api/v1/admin/posts?deleted=true&page_size=100", headers=headers
        ).json()["data"]["items"]
    ]
    assert pid not in deleted_ids

    # editing a soft-deleted post → 404
    other = client.post(
        "/api/v1/admin/posts",
        headers=headers,
        json={"title": "再回收", "slug": "recycle-again", "status": "published"},
    ).json()["data"]
    client.delete(f"/api/v1/admin/posts/{other['id']}", headers=headers)
    assert client.get(f"/api/v1/admin/posts/{other['id']}", headers=headers).status_code == 404
