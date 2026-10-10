"""Friend link CRUD with icon support."""

from fastapi.testclient import TestClient


def _login(client: TestClient) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


def test_friend_crud_with_icon(client: TestClient):
    headers = _login(client)
    created = client.post(
        "/api/v1/admin/friends",
        headers=headers,
        json={
            "name": "图标站",
            "url": "https://icon.example.com",
            "icon": "/uploads/f.png",
            "sort_order": 7,
        },
    )
    assert created.status_code == 201
    fid = created.json()["data"]["id"]
    assert created.json()["data"]["icon"] == "/uploads/f.png"

    updated = client.put(
        f"/api/v1/admin/friends/{fid}",
        headers=headers,
        json={"icon": None, "description": "清空图标"},
    )
    assert updated.json()["data"]["icon"] is None

    public = client.get("/api/v1/friends").json()["data"]
    row = next(f for f in public if f["id"] == fid)
    assert row["icon"] is None and row["description"] == "清空图标"

    assert client.delete(f"/api/v1/admin/friends/{fid}", headers=headers).status_code == 200


def test_friend_visibility_filtering(client: TestClient):
    headers = _login(client)
    created = client.post(
        "/api/v1/admin/friends",
        headers=headers,
        json={"name": "隐藏站", "url": "https://hidden.example.com", "visible": False},
    )
    fid = created.json()["data"]["id"]
    assert created.json()["data"]["visible"] is False

    public_ids = [f["id"] for f in client.get("/api/v1/friends").json()["data"]]
    assert fid not in public_ids
    admin_ids = [
        f["id"] for f in client.get("/api/v1/admin/friends", headers=headers).json()["data"]
    ]
    assert fid in admin_ids

    client.put(f"/api/v1/admin/friends/{fid}", headers=headers, json={"visible": True})
    public_ids = [f["id"] for f in client.get("/api/v1/friends").json()["data"]]
    assert fid in public_ids
