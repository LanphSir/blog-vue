"""评论模块回归测试：审核开关、占位语义、嵌套回复、开关与限流、管理状态机。"""

import pytest


@pytest.fixture(autouse=True)
def _clear_rate():
    """限流是进程内内存态：跨用例清空计数，并默认放宽窗口，让发多条评论的
    用例专注验证业务；限流用例用 _strict_rate 恢复真实阈值。"""
    from app.core import ratelimit as rl

    rl.reset()
    real_window, real_daily = rl.COMMENT_RATE_WINDOW, rl.COMMENT_RATE_DAILY
    rl.COMMENT_RATE_WINDOW, rl.COMMENT_RATE_DAILY = 0, 9999
    yield
    rl.COMMENT_RATE_WINDOW, rl.COMMENT_RATE_DAILY = real_window, real_daily
    rl.reset()


@pytest.fixture()
def strict_rate():
    """限流测试专用：恢复真实阈值（setup 顺序在 relax 之后）。"""
    from app.core import ratelimit as rl

    rl.COMMENT_RATE_WINDOW, rl.COMMENT_RATE_DAILY = 30, 20
    rl.reset()
    yield
    rl.reset()


def _login(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123", "captcha_id": "", "captcha_code": ""},
    )
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_post(client, token, slug="hello", **extra):
    payload = {
        "title": "评论测试文章",
        "slug": slug,
        "content": "# hi",
        "status": "published",
        **extra,
    }
    resp = client.post("/api/v1/admin/posts", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


def _set_config(client, token, key, value):
    resp = client.put(
        "/api/v1/admin/site/config", json=[{"key": key, "value": value}], headers=_auth(token)
    )
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def admin(client):
    return _login(client)


@pytest.fixture()
def post(client, admin):
    return _create_post(client, admin)


def _post_comment(client, content="写得真好", **extra):
    resp = client.post("/api/v1/comments", json={"content": content, **extra})
    return resp


class TestCreate:
    def test_audit_on_creates_pending(self, client, admin, post):
        # 默认开审核：新评论 pending，公开列表不可见
        resp = _post_comment(client, post_slug=post["slug"], nickname="用户_1234")
        assert resp.status_code == 201, resp.text
        body = resp.json()["data"]
        assert body["nickname"] == "用户_1234"
        listing = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]
        assert listing["total"] == 0

    def test_audit_off_creates_approved(self, client, admin, post):
        _set_config(client, admin, "site_comment_audit", "false")
        resp = _post_comment(client, post_slug=post["slug"], nickname="用户_1")
        assert resp.status_code == 201
        listing = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]
        assert listing["total"] == 1
        assert listing["items"][0]["comment"]["content"] == "写得真好"

    def test_captcha_skipped_when_id_empty(self, client, admin, post):
        # captcha_id 空 → 跳过校验（与登录同款向后兼容）
        resp = _post_comment(client, post_slug=post["slug"], nickname="n", captcha_code="")
        assert resp.status_code == 201

    def test_captcha_wrong_rejected(self, client, admin, post):
        resp = _post_comment(
            client,
            post_slug=post["slug"],
            nickname="n",
            captcha_id="nonexistent",
            captcha_code="abcd",
        )
        assert resp.status_code == 400

    def test_ratelimit_blocks_second_comment(self, client, admin, post, strict_rate):
        _set_config(client, admin, "site_comment_audit", "false")
        r1 = _post_comment(client, post_slug=post["slug"], nickname="n")
        assert r1.status_code == 201
        r2 = _post_comment(client, post_slug=post["slug"], nickname="n", content="再来一条")
        assert r2.status_code == 429

    def test_comments_disabled_403(self, client, admin):
        p = _create_post(client, admin, slug="closed", comments_enabled=False)
        resp = _post_comment(client, post_slug=p["slug"], nickname="n")
        assert resp.status_code == 403

    def test_draft_post_404(self, client, admin):
        resp = client.post(
            "/api/v1/admin/posts",
            json={"title": "草稿", "slug": "dft", "content": "x", "status": "draft"},
            headers=_auth(admin),
        )
        assert resp.status_code == 201
        r = _post_comment(client, post_slug="dft", nickname="n")
        assert r.status_code == 404


class TestThreadsAndReplies:
    def _approved_comment(self, client, admin, post, content="楼主体"):
        _set_config(client, admin, "site_comment_audit", "false")
        resp = _post_comment(client, post_slug=post["slug"], nickname="楼主", content=content)
        assert resp.status_code == 201
        return resp.json()["data"]

    def test_reply_nests_under_root(self, client, admin, post):
        root = self._approved_comment(client, admin, post)
        # 回复的回复：parent 指向回复，root 仍是顶级楼
        r1 = _post_comment(
            client, post_slug=post["slug"], nickname="甲", content="回复一", parent_id=root["id"]
        )
        assert r1.status_code == 201
        assert r1.json()["data"]["reply_to_nickname"] == "楼主"
        r2 = _post_comment(
            client,
            post_slug=post["slug"],
            nickname="乙",
            content="回复二",
            parent_id=r1.json()["data"]["id"],
        )
        assert r2.status_code == 201
        assert r2.json()["data"]["reply_to_nickname"] == "甲"

        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert len(threads) == 1
        assert threads[0]["reply_count"] == 2
        # 平铺展示：回复二带「回复 甲」前缀数据
        assert [r["nickname"] for r in threads[0]["replies"]] == ["甲", "乙"]
        assert threads[0]["replies"][1]["reply_to_nickname"] == "甲"

    def test_replies_pagination(self, client, admin, post):
        root = self._approved_comment(client, admin, post)
        for i in range(4):
            _post_comment(
                client,
                post_slug=post["slug"],
                nickname=f"n{i}",
                content=f"c{i}",
                parent_id=root["id"],
            )
        # 列表内嵌前 3 条
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert len(threads[0]["replies"]) == 3
        assert threads[0]["reply_count"] == 4
        # 展开分页
        page2 = client.get(f"/api/v1/comments/{root['id']}/replies?page=1&page_size=3").json()[
            "data"
        ]
        assert len(page2["items"]) == 3
        assert page2["total"] == 4

    def test_reply_to_hidden_or_pending_422(self, client, admin, post):
        # pending 评论（默认开审核）不可回复
        pending = _post_comment(client, post_slug=post["slug"], nickname="p", content="p")
        assert pending.status_code == 201
        r = _post_comment(
            client,
            post_slug=post["slug"],
            nickname="x",
            content="x",
            parent_id=pending.json()["data"]["id"],
        )
        assert r.status_code == 422


class TestDeletePlaceholder:
    def _thread(self, client, admin, post):
        _set_config(client, admin, "site_comment_audit", "false")
        root = _post_comment(
            client, post_slug=post["slug"], nickname="楼主", content="楼主内容"
        ).json()["data"]
        rep = _post_comment(
            client, post_slug=post["slug"], nickname="甲", content="甲的回复", parent_id=root["id"]
        ).json()["data"]
        return root, rep

    def test_deleted_root_with_reply_shows_placeholder(self, client, admin, post):
        root, _ = self._thread(client, admin, post)
        token = admin
        resp = client.delete(f"/api/v1/admin/comments/{root['id']}", headers=_auth(token))
        assert resp.status_code == 200
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert len(threads) == 1
        assert threads[0]["comment"]["content"] == "该评论已被删除"
        assert threads[0]["comment"]["nickname"] == "楼主"
        assert threads[0]["replies"][0]["content"] == "甲的回复"

    def test_deleted_root_without_reply_hidden(self, client, admin, post):
        root, _ = self._thread(client, admin, post)
        # 删掉唯一回复 → 楼变成"无存活回复的被删楼"时整楼消失
        rep2 = _post_comment(
            client, post_slug=post["slug"], nickname="乙", content="乙", parent_id=root["id"]
        )
        rep3 = _post_comment(
            client, post_slug=post["slug"], nickname="丙", content="丙", parent_id=root["id"]
        )
        _ = rep2, rep3
        # 先把楼的回复全部删除
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        for r in threads[0]["replies"]:
            client.delete(f"/api/v1/admin/comments/{r['id']}", headers=_auth(admin))
        client.delete(f"/api/v1/admin/comments/{root['id']}", headers=_auth(admin))
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert threads == []

    def test_deleted_reply_keeps_thread(self, client, admin, post):
        root, rep = self._thread(client, admin, post)
        client.delete(f"/api/v1/admin/comments/{rep['id']}", headers=_auth(admin))
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert len(threads) == 1
        assert threads[0]["reply_count"] == 0  # 被删且无存活后代 → 不占位不计数
        assert threads[0]["replies"] == []

    def test_deleted_content_never_leaks(self, client, admin, post):
        root, _ = self._thread(client, admin, post)
        client.delete(f"/api/v1/admin/comments/{root['id']}", headers=_auth(admin))
        body = client.get(f"/api/v1/comments?slug={post['slug']}").text
        assert "楼主内容" not in body

    def test_count_endpoint(self, client, admin, post):
        assert client.get(f"/api/v1/comments/count?slug={post['slug']}").json()["data"] == 0
        _set_config(client, admin, "site_comment_audit", "false")
        root = _post_comment(client, post_slug=post["slug"], nickname="n", content="c").json()[
            "data"
        ]
        _post_comment(
            client, post_slug=post["slug"], nickname="r", content="r", parent_id=root["id"]
        )
        # 总数口径 = approved 且未删（含回复）
        assert client.get(f"/api/v1/comments/count?slug={post['slug']}").json()["data"] == 2
        # 关闭评论后计数返回 0
        client.put(
            f"/api/v1/admin/posts/{post['id']}",
            json={"comments_enabled": False},
            headers=_auth(admin),
        )
        assert client.get(f"/api/v1/comments/count?slug={post['slug']}").json()["data"] == 0
        # 未审文章 → 404
        assert client.get("/api/v1/comments/count?slug=nope").status_code == 404


class TestVisibility:
    def test_hidden_comment_keeps_replies(self, client, admin, post):
        _set_config(client, admin, "site_comment_audit", "false")
        root = _post_comment(client, post_slug=post["slug"], nickname="楼主", content="楼").json()[
            "data"
        ]
        rep = _post_comment(
            client, post_slug=post["slug"], nickname="甲", content="甲言", parent_id=root["id"]
        ).json()["data"]
        client.post(f"/api/v1/admin/comments/{rep['id']}/hide", headers=_auth(admin))
        threads = client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["items"]
        assert threads[0]["reply_count"] == 0
        # hidden 不可回复
        r = _post_comment(
            client, post_slug=post["slug"], nickname="x", content="x", parent_id=rep["id"]
        )
        assert r.status_code == 422


class TestAdminFlow:
    def test_approve_hide_restore_state_machine(self, client, admin, post):
        # 默认开审核 → pending
        c = _post_comment(client, post_slug=post["slug"], nickname="n", content="c").json()["data"]
        # pending 不公开
        assert client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["total"] == 0
        # approve → 公开
        assert (
            client.post(
                f"/api/v1/admin/comments/{c['id']}/approve", headers=_auth(admin)
            ).status_code
            == 200
        )
        assert client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["total"] == 1
        # hide → 不公开
        assert (
            client.post(f"/api/v1/admin/comments/{c['id']}/hide", headers=_auth(admin)).status_code
            == 200
        )
        assert client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["total"] == 0
        # delete 软删 → 回收站可见 + 不能直接 approve
        assert (
            client.delete(f"/api/v1/admin/comments/{c['id']}", headers=_auth(admin)).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/admin/comments/{c['id']}/approve", headers=_auth(admin)
            ).status_code
            == 409
        )
        trash = client.get("/api/v1/admin/comments?deleted=true", headers=_auth(admin)).json()[
            "data"
        ]
        assert trash["total"] == 1
        # restore → 回到 hidden 状态且不公开
        assert (
            client.post(
                f"/api/v1/admin/comments/{c['id']}/restore", headers=_auth(admin)
            ).status_code
            == 200
        )
        assert client.get(f"/api/v1/comments?slug={post['slug']}").json()["data"]["total"] == 0

    def test_admin_list_filters(self, client, admin, post):
        _set_config(client, admin, "site_comment_audit", "false")
        _post_comment(client, post_slug=post["slug"], nickname="张三", content="关键词内容")
        c2 = _post_comment(client, post_slug=post["slug"], nickname="李四", content="另一条")
        client.post(f"/api/v1/admin/comments/{c2.json()['data']['id']}/hide", headers=_auth(admin))
        listing = client.get("/api/v1/admin/comments?status=hidden", headers=_auth(admin)).json()[
            "data"
        ]
        assert listing["total"] == 1
        assert listing["items"][0]["nickname"] == "李四"
        assert listing["items"][0]["post_title"] == "评论测试文章"
        keyword = client.get("/api/v1/admin/comments?keyword=张三", headers=_auth(admin)).json()[
            "data"
        ]
        assert keyword["total"] == 1
        # 公开列表里绝不含 email/ip/UA
        public = client.get(f"/api/v1/comments?slug={post['slug']}").text
        for secret in ("user_agent", '"ip"', '"email"'):
            assert secret not in public

    def test_pending_count(self, client, admin, post):
        assert (
            client.get("/api/v1/admin/comments/pending-count", headers=_auth(admin)).json()["data"]
            == 0
        )
        _post_comment(client, post_slug=post["slug"], nickname="n", content="c")
        assert (
            client.get("/api/v1/admin/comments/pending-count", headers=_auth(admin)).json()["data"]
            == 1
        )

    def test_admin_requires_auth(self, client):
        assert client.get("/api/v1/admin/comments").status_code in (401, 403)


class TestPostIntegration:
    def test_detail_comment_count(self, client, admin, post):
        assert client.get(f"/api/v1/posts/{post['slug']}").json()["data"]["comment_count"] == 0
        _set_config(client, admin, "site_comment_audit", "false")
        _post_comment(client, post_slug=post["slug"], nickname="n", content="c")
        c2 = _post_comment(client, post_slug=post["slug"], nickname="h", content="隐藏的")
        client.post(f"/api/v1/admin/comments/{c2.json()['data']['id']}/hide", headers=_auth(admin))
        assert client.get(f"/api/v1/posts/{post['slug']}").json()["data"]["comment_count"] == 1

    def test_comments_enabled_roundtrip(self, client, admin, post):
        pid = post["id"]
        resp = client.put(
            f"/api/v1/admin/posts/{pid}", json={"comments_enabled": False}, headers=_auth(admin)
        )
        assert resp.json()["data"]["comments_enabled"] is False
        assert _post_comment(client, post_slug=post["slug"], nickname="n").status_code == 403

    def test_permanent_delete_removes_comments(self, client, admin, post):
        _set_config(client, admin, "site_comment_audit", "false")
        _post_comment(client, post_slug=post["slug"], nickname="n", content="c")
        client.delete(f"/api/v1/admin/posts/{post['id']}", headers=_auth(admin))
        client.delete(f"/api/v1/admin/posts/{post['id']}/permanent", headers=_auth(admin))
        admin_listing = client.get("/api/v1/admin/comments", headers=_auth(admin)).json()["data"]
        assert admin_listing["total"] == 0

    def test_invalid_payload_422(self, client, admin, post):
        assert (
            _post_comment(client, post_slug=post["slug"], nickname="", content="c").status_code
            == 422
        )
        assert (
            _post_comment(client, post_slug=post["slug"], nickname="n", content="").status_code
            == 422
        )
        assert (
            _post_comment(
                client, post_slug=post["slug"], nickname="n" * 31, content="c"
            ).status_code
            == 422
        )
