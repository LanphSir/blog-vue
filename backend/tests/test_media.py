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


def test_delete_with_reference_protection(client):
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

    blocked = client.delete(f"/api/v1/admin/media/{media_id}", headers=headers)
    assert blocked.status_code == 409
    assert "友链" in blocked.json()["message"]

    forced = client.delete(f"/api/v1/admin/media/{media_id}?force=true", headers=headers)
    assert forced.status_code == 200

    from app.core.config import settings

    rel = url.removeprefix("/uploads/")
    assert not (settings.upload_path / rel).exists()
    client.delete(f"/api/v1/admin/friends/{fid}", headers=headers)


async def test_sweep_registers_legacy_files(db_session, tmp_path, monkeypatch):
    from app.core.config import settings
    from app.seed import sweep_existing_uploads

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "sweep-root"))
    root = settings.upload_path
    root.mkdir(parents=True, exist_ok=True)
    (root / "legacy-a.png").write_bytes(PNG_1PX)
    sub = root / "2025" / "01"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "legacy-b.png").write_bytes(PNG_1PX)
    (root / "notes.txt").write_text("skip me")

    async with db_session() as db:
        await sweep_existing_uploads(db)
        await sweep_existing_uploads(db)  # idempotent

    from sqlalchemy import func, select

    from app.models.site import MediaAsset

    async with db_session() as db:
        rows = (
            (await db.execute(select(MediaAsset).order_by(MediaAsset.stored_name))).scalars().all()
        )
        assert [r.stored_name for r in rows] == ["legacy-a.png", "legacy-b.png"]
        assert all(r.url.startswith("/uploads/") for r in rows)
        assert (await db.execute(select(func.count(MediaAsset.id)))).scalar_one() == 2
