"""复现：带 tag_ids 创建/更新文章时 MissingGreenlet（见 posts.py:_apply_tags）。"""


def _login(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


def _mktag(client, h, name):
    r = client.post("/api/v1/admin/tags", headers=h, json={"name": name, "slug": name})
    assert r.status_code in (200, 201), r.text
    return r.json()["data"]["id"]


def test_create_post_with_tags(client):
    h = _login(client)
    tid = _mktag(client, h, "tg1")
    r = client.post(
        "/api/v1/admin/posts",
        headers=h,
        json={"title": "带标签", "slug": "with-tags", "content": "x", "tag_ids": [tid]},
    )
    assert r.status_code == 201, r.text[:400]


def test_update_post_clear_tags(client):
    """更新时传空 tag_ids 清空标签：同样会触发对 post.tags 旧值的同步懒加载。"""
    h = _login(client)
    tid = _mktag(client, h, "tg2")
    c = client.post(
        "/api/v1/admin/posts",
        headers=h,
        json={"title": "先带标签", "slug": "clear-tags", "content": "x", "tag_ids": [tid]},
    )
    assert c.status_code == 201, c.text[:400]
    pid = c.json()["data"]["id"]
    r = client.put(f"/api/v1/admin/posts/{pid}", headers=h, json={"tag_ids": []})
    assert r.status_code == 200, r.text[:400]
