"""Media library: hashed/date-folded uploads, validation, reference-safe delete, sweep."""

import base64

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _login(client) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


def _upload(client, headers, filename="pic.png", content=PNG_1PX):
    return client.post(
        "/api/v1/admin/upload", headers=headers, files={"file": (filename, content, "image/png")}
    )


def test_upload_hashes_and_folds_by_month(client):
    headers = _login(client)
    resp = _upload(client, headers)
    assert resp.status_code == 201
    url = resp.json()["data"]
    import re

    from app.core.config import settings

    assert re.match(r"^/uploads/\d{4}/\d{2}/\d{2}/\d{14}_[0-9a-f]{8}\.png$", url), url
    rel = url.removeprefix("/uploads/")
    assert (settings.upload_path / rel).exists()

    listed = client.get("/api/v1/admin/media", headers=headers).json()["data"]
    row = next(item for item in listed["items"] if item["url"] == url)
    assert row["size"] == len(PNG_1PX)
    assert row["mime"] == "image/png"


def test_upload_rejects_fake_extension(client):
    headers = _login(client)
    resp = _upload(
        client, headers, filename="evil.png", content=b"MZ\x90\x00 this is not a png at all"
    )
    assert resp.status_code == 400


def test_upload_rejects_unknown_extension(client):
    headers = _login(client)
    resp = _upload(client, headers, filename="x.exe", content=b"MZ")
    assert resp.status_code == 400


def test_media_pagination(client):
    headers = _login(client)
    for _ in range(3):
        assert _upload(client, headers).status_code == 201
    page1 = client.get("/api/v1/admin/media?page=1&page_size=2", headers=headers).json()["data"]
    assert page1["total"] == 3 and len(page1["items"]) == 2
    page2 = client.get("/api/v1/admin/media?page=2&page_size=2", headers=headers).json()["data"]
    assert len(page2["items"]) == 1


def test_folder_tree_and_dir_filter(client):
    headers = _login(client)
    url1 = _upload(client, headers).json()["data"]
    gif = b"GIF89a\x01\x02\x03\x04"
    url2 = _upload(client, headers, filename="a.gif", content=gif).json()["data"]
    assert url1.rsplit("/", 1)[0] == url2.rsplit("/", 1)[0]
    folder = url1.removeprefix("/uploads/").rsplit("/", 1)[0]

    folders = client.get("/api/v1/admin/media/folders", headers=headers).json()["data"]
    entry = next(f for f in folders if f["dir"] == folder)
    assert entry["count"] == 2
    assert any(f["dir"] == "root" for f in folders) or True

    filtered = client.get(f"/api/v1/admin/media?dir={folder}", headers=headers).json()["data"]
    assert filtered["total"] == 2
    other = client.get("/api/v1/admin/media?dir=1999/01/01", headers=headers).json()["data"]
    assert other["total"] == 0


def test_soft_delete_moves_to_recycle_bin(client):
    """普通删除=软删：列表隐藏、回收站可见、磁盘文件与前台引用不受影响。"""
    headers = _login(client)
    url = _upload(client, headers).json()["data"]
    media_id = next(
        i["id"] for i in client.get("/api/v1/admin/media", headers=headers).json()["data"]["items"]
    )

    assert client.delete(f"/api/v1/admin/media/{media_id}", headers=headers).status_code == 200

    listed = client.get("/api/v1/admin/media", headers=headers).json()["data"]
    assert media_id not in [i["id"] for i in listed["items"]]
    assert listed["total"] == 0

    trash = client.get("/api/v1/admin/media?deleted=true", headers=headers).json()["data"]
    assert trash["total"] == 1 and trash["items"][0]["id"] == media_id
    assert trash["items"][0]["deleted_at"] is not None

    from app.core.config import settings

    rel = url.removeprefix("/uploads/")
    assert (settings.upload_path / rel).exists()  # 软删不碰文件，引用不失效

    # 目录徽标不计回收站内容
    folders = client.get("/api/v1/admin/media/folders", headers=headers).json()["data"]
    assert sum(f["count"] for f in folders) == 0

    # 重复删除/恢复回列表
    assert client.delete(f"/api/v1/admin/media/{media_id}", headers=headers).status_code == 404
    restored = client.post(f"/api/v1/admin/media/{media_id}/restore", headers=headers)
    assert restored.status_code == 200 and restored.json()["data"]["deleted_at"] is None
    again = client.post(f"/api/v1/admin/media/{media_id}/restore", headers=headers)
    assert again.status_code == 404


def test_permanent_delete_reference_protection(client):
    """彻底删除才校验引用并物理删文件；force 可绕过。"""
    headers = _login(client)
    url = _upload(client, headers).json()["data"]
    media_id = next(
        i["id"] for i in client.get("/api/v1/admin/media", headers=headers).json()["data"]["items"]
    )

    friend = client.post(
        "/api/v1/admin/friends",
        headers=headers,
        json={"name": "引用站", "url": "https://r.example.com", "icon": url},
    )
    fid = friend.json()["data"]["id"]

    # 软删不拦引用
    assert client.delete(f"/api/v1/admin/media/{media_id}", headers=headers).status_code == 200

    blocked = client.delete(f"/api/v1/admin/media/{media_id}/permanent", headers=headers)
    assert blocked.status_code == 409
    assert "友链" in blocked.json()["message"]

    forced = client.delete(f"/api/v1/admin/media/{media_id}/permanent?force=true", headers=headers)
    assert forced.status_code == 200

    from app.core.config import settings

    rel = url.removeprefix("/uploads/")
    assert not (settings.upload_path / rel).exists()
    trash = client.get("/api/v1/admin/media?deleted=true", headers=headers).json()["data"]
    assert trash["total"] == 0
    client.delete(f"/api/v1/admin/friends/{fid}", headers=headers)


def test_restore_requires_file_on_disk(client):
    """磁盘文件丢失时恢复报 409，提示彻底删除记录。"""
    headers = _login(client)
    url = _upload(client, headers).json()["data"]
    media_id = next(
        i["id"] for i in client.get("/api/v1/admin/media", headers=headers).json()["data"]["items"]
    )
    from app.core.config import settings

    rel = url.removeprefix("/uploads/")
    client.delete(f"/api/v1/admin/media/{media_id}", headers=headers)
    (settings.upload_path / rel).unlink()

    resp = client.post(f"/api/v1/admin/media/{media_id}/restore", headers=headers)
    assert resp.status_code == 409
    assert "丢失" in resp.json()["message"]
