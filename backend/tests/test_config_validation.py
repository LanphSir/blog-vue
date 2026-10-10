"""Whitelisted config-key validation on batch update."""


def _login(client):
    login = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _config_value(client, key):
    items = client.get("/api/v1/site/config").json()["data"]
    return next((i["value"] for i in items if i["key"] == key), None)


def test_invalid_accent_color_rejected(client):
    headers = _login(client)
    resp = client.put(
        "/api/v1/admin/site/config",
        headers=headers,
        json=[{"key": "site_accent_color", "value": "red"}],
    )
    assert resp.status_code == 422
    assert _config_value(client, "site_accent_color") != "red"


def test_out_of_range_counts_rejected(client):
    headers = _login(client)
    resp = client.put(
        "/api/v1/admin/site/config",
        headers=headers,
        json=[{"key": "sidebar_tag_count", "value": "0"}],
    )
    assert resp.status_code == 422
    assert _config_value(client, "sidebar_tag_count") != "0"


def test_one_bad_key_rejects_whole_batch(client):
    headers = _login(client)
    resp = client.put(
        "/api/v1/admin/site/config",
        headers=headers,
        json=[
            {"key": "site_name", "value": "不应该被写入"},
            {"key": "site_accent_color", "value": "#GGG"},
        ],
    )
    assert resp.status_code == 422
    assert _config_value(client, "site_name") != "不应该被写入"


def test_valid_values_and_unknown_keys_accepted(client):
    headers = _login(client)
    resp = client.put(
        "/api/v1/admin/site/config",
        headers=headers,
        json=[
            {"key": "site_accent_color", "value": "#16a34a"},
            {"key": "homepage_section_count", "value": "6"},
            {"key": "sidebar_tag_count", "value": "12"},
            {"key": "brand_new_key", "value": "anything goes"},
        ],
    )
    assert resp.status_code == 200
    assert _config_value(client, "site_accent_color") == "#16a34a"
    assert _config_value(client, "homepage_section_count") == "6"
    assert _config_value(client, "sidebar_tag_count") == "12"
    assert _config_value(client, "brand_new_key") == "anything goes"
