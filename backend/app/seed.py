"""启动时播种初始管理员、默认站点配置与演示内容。

应用启动自动调用，可安全重复执行（幂等）：管理员/配置/演示数据都按"存在即跳过"
的方式插入；一次性迁移（默认菜单、归档菜单项、旧 JSON 配置迁移、媒体库扫描等）
都依赖对应的配置标记（menus_seeded、archive_menu_added 等）或"表为空"判断，
确保不会因重复启动而重复写入或覆盖用户已做的修改。
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.crud import site as site_crud
from app.crud import user as user_crud
from app.models.post import Category, Post, Tag
from app.models.site import (
    Banner,
    FriendLink,
    MediaAsset,
    MenuItem,
    Notice,
    SiteConfig,
    SocialLink,
)

logger = logging.getLogger("blog")

ABOUT_MARKDOWN_TEMPLATE = """
你好，我是这里的站长——欢迎来到我在互联网上的一小块自留地。

## 我在做什么

白天以软件开发为生，折腾**后端与分布式系统**；业余时间写前端、捣鼓 homelab 和各种小工具。
信奉一句话：能把麻烦事自动化掉，就不该第二次手动做。

## 这里会写什么

- **技术笔记** —— 工作里踩过的坑：后端、数据库、部署，以及修 bug 的血泪史
- **工具与效率** —— 我真实在用的工具和打磨过的工作流，希望能帮你少走弯路
- **生活与思考** —— 跑步、读书、和一些值得记下来的瞬间

不承诺固定更新频率，但承诺只写对读者有用的内容。

## 关于本站

这个博客是完全自建、不依赖任何第三方平台的小站：

| 部分 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | FastAPI + SQLAlchemy (async) |
| 数据库 | SQLite |
| 部署 | Docker + Nginx |

## 找到我

最方便的方式是点击本页的社交图标（GitHub、邮箱等），也欢迎在任意文章下留言，评论我都会看。

> 这段文字可以在后台「站点配置 → 基础信息 → 关于我介绍」中修改，换成你自己的故事吧。
"""

DEFAULT_SITE_CONFIG = {
    "site_name": "我的个人博客",
    "site_description": "记录技术、生活与思考",
    "site_slogan": "",
    "site_accent_color": "#2563EB",
    "site_author": "站长",
    "site_avatar": "",
    "site_bio": "热爱编程与写作，记录技术、生活与思考。",
    "profile_visible": "true",
    "sidebar_tags_visible": "true",
    "sidebar_tag_count": "8",
    "sidebar_recent_visible": "true",
    "sidebar_notice_visible": "true",
    "site_logo": "",
    "site_favicon": "",
    "site_background": "none",
    "site_loading": "spinner",
    "icp": "",
    "footer_text": "Powered by Vue3 + FastAPI",
    "site_about_markdown": ABOUT_MARKDOWN_TEMPLATE.strip(),
}

DEMO_CATEGORIES = [
    {"name": "后端开发", "slug": "backend", "sort_order": 1, "color": "#2563EB"},
    {
        "name": "数据库",
        "slug": "database",
        "sort_order": 1,
        "color": "#7C3AED",
        "parent": "backend",
    },
    {
        "name": "部署运维",
        "slug": "deploy",
        "sort_order": 2,
        "color": "#0EA5E9",
        "parent": "backend",
    },
    {"name": "前端开发", "slug": "frontend", "sort_order": 2, "color": "#DB2777"},
    {
        "name": "Vue 生态",
        "slug": "vue-ecosystem",
        "sort_order": 1,
        "color": "#16A34A",
        "parent": "frontend",
    },
    {"name": "技术随笔", "slug": "notes", "sort_order": 3, "color": "#EA580C"},
]

DEMO_TAGS = [
    {"name": "FastAPI", "slug": "fastapi", "color": "#2563EB"},
    {"name": "Vue", "slug": "vue", "color": "#16A34A"},
    {"name": "Python", "slug": "python", "color": "#2563EB"},
    {"name": "SQLite", "slug": "sqlite", "color": "#7C3AED"},
    {"name": "Docker", "slug": "docker", "color": "#0EA5E9"},
    {"name": "JavaScript", "slug": "javascript", "color": "#F59E0B"},
    {"name": "TypeScript", "slug": "typescript", "color": "#3178C6"},
    {"name": "Nginx", "slug": "nginx", "color": "#10B981"},
    {"name": "Git", "slug": "git", "color": "#F05032"},
    {"name": "Redis", "slug": "redis", "color": "#DC2626"},
    {"name": "架构", "slug": "architecture", "color": "#64748B"},
    {"name": "笔记", "slug": "notes", "color": "#B45309"},
    {"name": "CSS", "slug": "css", "color": "#06B6D4"},
    {"name": "AI", "slug": "ai", "color": "#8B5CF6"},
]

DEMO_BANNERS = [
    {
        "title": "欢迎来到我的博客",
        "subtitle": "记录技术、生活与思考，愿与你分享每一次成长。",
        "image": None,
        "link": "/posts",
        "sort_order": 1,
    },
    {
        "title": "后端与前端，两手都要抓",
        "subtitle": "FastAPI + Vue 3 构建前后端分离的个人博客。",
        "image": None,
        "link": "/posts/fastapi-blog-backend",
        "sort_order": 2,
    },
]

DEMO_POSTS = [
    {
        "title": "用 FastAPI 快速搭建个人博客后端",
        "slug": "fastapi-blog-backend",
        "category": "backend",
        "tags": ["fastapi", "python", "sqlite"],
        "author": "站长",
        "featured": True,
        "sort_weight": 20,
        "summary": "介绍个人博客后端的技术选型、分层结构与核心实现要点。",
        "content": """# 为什么选择 FastAPI

FastAPI 是现代 Python 后端的事实标准之一，具备类型安全、自动文档等优点。

## 核心技术点

- **Pydantic v2**：请求/响应校验
- **SQLAlchemy 2.0 异步**：配合 aiosqlite
- **JWT 认证**：登录后签发 token

## 示例代码

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/")
async def root():
    return {"hello": "world"}

with TestClient(app) as client:
    resp = client.get("/")
    assert resp.status_code == 200
```

> 关键点：`TestClient` 必须使用上下文管理器，否则启动生命周期不会执行。

## 小结

| 关注点 | 方案 |
| --- | --- |
| 性能 | 异步 + uvicorn |
| 可维护 | 分层清晰，职责单一 |
| 可测试 | pytest 全流程覆盖 |
""",
    },
    {
        "title": "Vue 3 组合式 API 开发实战",
        "slug": "vue3-composition-api",
        "category": "frontend",
        "tags": ["vue"],
        "author": "站长",
        "featured": True,
        "sort_weight": 15,
        "summary": "使用 <script setup> 与组合式函数组织前端代码的实践记录。",
        "content": """# 组合式 API 的优势

组合式 API 让我们按逻辑组织代码，而不是按选项分散。

## 常用模式

```js
import { ref, computed } from 'vue'

const count = ref(0)
const double = computed(() => count.value * 2)

function increment() {
  count.value += 1
}
```

## 组件化思维

1. 拆分可复用组件（Markdown 编辑器、上传组件）
2. 抽取组合式函数复用业务逻辑
3. 保持模板简单，逻辑放到脚本中

### 状态管理

配合 **Pinia** 管理登录态、站点配置与主题等全局状态，比 Props 逐层传递更优雅。
""",
    },
    {
        "title": "将博客部署到 Docker 的一步步记录",
        "slug": "deploy-blog-with-docker",
        "category": "notes",
        "tags": ["docker", "git"],
        "summary": "前后端分离项目如何用 Docker Compose 一键部署。",
        "content": """# 部署思路

一个容器跑后端，一个容器跑前端（nginx 托管静态资源并反向代理）。

## 后端镜像

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## 数据持久化

通过卷挂载保证数据库、上传文件与日志不随容器销毁：

```yaml
volumes:
  - ./backend/data:/app/data
  - ./backend/uploads:/app/uploads
```

## 验证部署

```bash
docker compose up -d --build
curl http://localhost:8080/health
```

至此，一个前后端分离的个人博客就完整跑起来了。
""",
    },
    {
        "title": "给博客加上 Markdown 编辑器",
        "slug": "markdown-editor-for-blog",
        "category": "frontend",
        "tags": ["vue", "javascript", "css"],
        "summary": "为后台文章编辑页面实现带实时预览的 Markdown 编辑器。",
        "content": """# 需求

后台写文章时希望能边写边看效果，于是实现了左右分栏的实时预览。

## 实现方式

使用 `marked` 解析 Markdown，`highlight.js` 做代码高亮，抽成组合式函数复用：

```js
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

export function useMarkdown(source) {
  const html = computed(() => marked.parse(source.value))
  return { html }
}
```

## 附加功能

- 编辑 / 预览 Tab 切换
- 分栏模式开关
- 封面上传组件

这套组合让写文章变成一件愉快的事。
""",
    },
    {
        "title": "Python 异步编程入门：从 async/await 到 FastAPI",
        "slug": "python-async-programming",
        "category": "backend",
        "tags": ["python", "fastapi", "ai"],
        "author": "站长",
        "featured": False,
        "sort_weight": 10,
        "summary": "深入理解 Python 异步机制，写出高效的非阻塞代码。",
        "content": """# 异步编程基础

Python 的 `async/await` 语法让异步编程变得直观。

## 什么是协程

```python
import asyncio

async def fetch_data(url):
    print(f"开始请求 {url}")
    await asyncio.sleep(1)
    return f"来自 {url} 的数据"

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

## FastAPI 中的异步

FastAPI 原生支持异步视图函数，在处理 I/O 密集型任务时性能显著提升。

| 场景 | 同步 | 异步 |
| --- | --- | --- |
| 数据库查询 | 阻塞 | await |
| HTTP 请求 | requests | httpx |
| 文件读写 | 阻塞 | aiofiles |

> 注意：不是所有场景都需要异步——CPU 密集型任务用 multiprocessing 更合适。
""",
    },
    {
        "title": "Nginx 反向代理配置实战",
        "slug": "nginx-reverse-proxy",
        "category": "deploy",
        "tags": ["docker", "nginx"],
        "author": "运维小张",
        "featured": False,
        "sort_weight": 8,
        "summary": "手把手教你配置 Nginx 反向代理，实现负载均衡与静态资源托管。",
        "content": """# Nginx 反向代理

Nginx 是高性能的 Web 服务器和反向代理工具。

## 基本配置

```nginx
server {
    listen 80;
    server_name blog.example.com;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }
}
```

## 负载均衡

```nginx
upstream backend_servers {
    server backend1:8000 weight=3;
    server backend2:8000 weight=1;
}

server {
    location /api/ {
        proxy_pass http://backend_servers;
    }
}
```

## 常见优化

- 开启 gzip 压缩
- 配置静态资源缓存
- 限制请求频率防爆破
""",
    },
    {
        "title": "SQLite 性能优化指南",
        "slug": "sqlite-performance",
        "category": "database",
        "tags": ["sqlite", "python", "architecture", "redis"],
        "author": "站长",
        "featured": False,
        "sort_weight": 5,
        "summary": "SQLite 虽轻量，但用好索引和查询优化同样能支撑可观的数据量。",
        "content": """# SQLite 优化技巧

SQLite 是世界上使用最广泛的数据库引擎。

## 索引优化

```sql
-- 慢查询
SELECT * FROM posts WHERE status = 'published';

-- 加索引后
CREATE INDEX idx_posts_status ON posts(status);
```

## 查询优化

- 使用 `EXPLAIN QUERY PLAN` 分析查询
- 避免 `SELECT *`，只取所需字段
- 分页时用 `LIMIT + OFFSET`

## WAL 模式

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

> WAL 模式在读多写少的场景下能显著提升并发性能。

| 优化项 | 效果 |
| --- | --- |
| 建立索引 | 查询提速 10-100 倍 |
| WAL 模式 | 读写并发提升 |
| 批量插入 | 事务合并减少 I/O |
""",
    },
    {
        "title": "Pinia vs Vuex：新一代状态管理选型",
        "slug": "pinia-vs-vuex",
        "category": "vue-ecosystem",
        "tags": ["vue", "typescript"],
        "author": "前端小陈",
        "featured": True,
        "sort_weight": 18,
        "summary": "对比 Pinia 和 Vuex 的用法差异与设计理念，帮你做出选择。",
        "content": """# Pinia vs Vuex

Vue 官方现已推荐 Pinia 作为状态管理方案。

## 语法对比

```js
// Vuex
this.$store.commit('increment')
this.$store.dispatch('fetchUser')

// Pinia
store.increment()
await store.fetchUser()
```

## 核心差异

- **TypeScript 支持**：Pinia 原生支持，类型推断无需额外声明
- **模块化**：Pinia 每个 store 独立，无需嵌套 modules
- **体积**：Pinia ~1KB，Vuex ~4KB

## 迁移建议

> 新项目推荐直接使用 Pinia，老项目视工作量逐步迁移。

```js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const double = computed(() => count.value * 2)
  function increment() { count.value++ }
  return { count, double, increment }
})
```
""",
    },
    {
        "title": "我的年度技术书单推荐",
        "slug": "tech-book-list",
        "category": "notes",
        "tags": ["notes", "architecture"],
        "author": "站长",
        "featured": False,
        "sort_weight": 3,
        "summary": "过去一年读过的好书推荐，涵盖编程、架构与思维方式。",
        "content": """# 年度书单

## 《深入理解计算机系统》
> 每个程序员都应该读一遍的经典之作。

## 《设计数据密集型应用》
> DDIA 帮你理解分布式系统的核心原理。

## 《重构：改善既有代码的设计》
> 保持代码整洁的实战指南。

### 阅读建议

1. 不要贪多，一次专注读一本
2. 读完后动手实践比只读更有价值
3. 做笔记，写博客，分享你的理解

> 读书是性价比最高的成长方式。
""",
    },
    {
        "title": "Docker Compose 多环境配置最佳实践",
        "slug": "docker-compose-multi-env",
        "category": "deploy",
        "tags": ["docker", "nginx"],
        "author": "运维小张",
        "featured": False,
        "sort_weight": 0,
        "summary": "使用 Docker Compose 管理开发、测试、生产环境的配置差异。",
        "content": """# 多环境 Docker Compose

使用 `docker-compose.override.yml` 实现环境差异配置。

## 基础文件

```yaml
# docker-compose.yml
services:
  backend:
    image: backend:latest
    ports:
      - "8000"
```

## 开发环境覆盖

```yaml
# docker-compose.override.yml
services:
  backend:
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
```

## 生产环境

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

> 核心原则：基础配置通⽤，差异文件覆盖。
""",
    },
    {
        "title": "【草稿】Vue 3 组件设计模式",
        "slug": "vue-component-patterns-draft",
        "category": "vue-ecosystem",
        "tags": ["vue"],
        "status": "draft",
        "author": "前端小陈",
        "featured": False,
        "sort_weight": 0,
        "summary": "这篇还是草稿，记录一下 Vue 3 常见的组件设计模式。",
        "content": "# Vue 3 组件设计模式\n\n还在撰写中，敬请期待。\n",
    },
]

DEMO_FRIEND_LINKS = [
    {
        "name": "Vue 官方文档",
        "url": "https://vuejs.org",
        "description": "渐进式 JavaScript 框架",
        "sort_order": 1,
    },
    {
        "name": "FastAPI 文档",
        "url": "https://fastapi.tiangolo.com",
        "description": "现代高性能 Web 框架",
        "sort_order": 2,
    },
    {
        "name": "Element Plus",
        "url": "https://element-plus.org",
        "description": "Vue 3 组件库",
        "sort_order": 3,
    },
]


DEFAULT_MENU_ROWS = [
    {"label": "文章", "path": "/posts", "icon": "Document", "sort_order": 1},
    {"label": "标签", "path": "/tags", "icon": "PriceTag", "sort_order": 2},
    {"label": "友链", "path": "/friends", "icon": "Link", "sort_order": 3},
    {"label": "关于", "path": "/about", "icon": "InfoFilled", "sort_order": 4},
]


async def _seed_default_menus(db: AsyncSession) -> None:
    """把原先硬编码的默认导航落成可管理的表行（每个安装仅一次）。"""
    # 用配置标记 menus_seeded 保证只播种一次；用户之后删除菜单也不会被重新播种
    marker = await site_crud.get_config(db, "menus_seeded")
    if marker is not None:
        return
    count = (await db.execute(select(func.count(MenuItem.id)))).scalar_one()
    if count == 0:
        for row in DEFAULT_MENU_ROWS:
            db.add(MenuItem(**row))
        logger.info("Seeded default navigation menus into menu_items")
    await site_crud.set_config(db, "menus_seeded", "true")
    await db.commit()


async def _add_archive_menu(db: AsyncSession) -> None:
    """一次性：给已经播种过的菜单表追加"归档"项（幂等）。"""
    # 归档功能上线前就装好的站点菜单表里没有归档项，这里用标记只补一次；
    # 若用户已手动加过 /archive 则跳过，避免重复
    if await site_crud.get_config(db, "archive_menu_added") is not None:
        return
    exists = (
        await db.execute(select(func.count(MenuItem.id)).where(MenuItem.path == "/archive"))
    ).scalar_one()
    if exists == 0:
        max_order = (
            await db.execute(select(func.coalesce(func.max(MenuItem.sort_order), 0)))
        ).scalar_one()
        db.add(
            MenuItem(label="归档", path="/archive", icon="FolderOpened", sort_order=max_order + 1)
        )
        logger.info("Appended archive nav menu item")
    await site_crud.set_config(db, "archive_menu_added", "true")
    await db.commit()


async def _migrate_menus(db: AsyncSession) -> None:
    """把旧的 site_menus JSON 配置迁移进 menu_items 表（一次性、幂等）。"""
    count = (await db.execute(select(func.count(MenuItem.id)))).scalar_one()
    if count > 0:
        return
    item = await site_crud.get_config(db, "site_menus")
    if item is None or not item.value.strip():
        return
    try:
        data = json.loads(item.value)
    except json.JSONDecodeError:
        # 配置是用户手改过的，可能是坏 JSON；跳过并告警，而不是让启动失败
        logger.warning("Skip site_menus migration: invalid JSON")
        return
    if not isinstance(data, list) or not data:
        return

    for order, entry in enumerate(data, start=1):
        if not isinstance(entry, dict) or not entry.get("label"):
            continue
        if entry.get("type") == "category":
            db.add(MenuItem(label=str(entry["label"]), type="category", sort_order=order))
            continue
        path = entry.get("path")
        if not path:
            continue
        parent = MenuItem(label=str(entry["label"]), path=str(path), sort_order=order)
        db.add(parent)
        await db.flush()
        children = entry.get("children")
        if isinstance(children, list):
            for child_order, child in enumerate(children, start=1):
                if not isinstance(child, dict) or not child.get("label") or not child.get("path"):
                    continue
                db.add(
                    MenuItem(
                        label=str(child["label"]),
                        path=str(child["path"]),
                        parent_id=parent.id,
                        sort_order=child_order,
                    )
                )
    await db.commit()
    logger.info("Migrated legacy site_menus JSON into menu_items")


def _legacy_visible(entry: dict) -> bool:
    value = entry.get("visible", True)
    if isinstance(value, str):
        return value.lower() not in ("false", "0")
    return bool(value)


async def _migrate_social_links(db: AsyncSession) -> None:
    """把旧的 profile_links JSON 配置迁入 social_links 表（幂等）。"""
    count = (await db.execute(select(func.count(SocialLink.id)))).scalar_one()
    if count > 0:
        return
    item = await site_crud.get_config(db, "profile_links")
    if item is None or not item.value.strip():
        return
    try:
        data = json.loads(item.value)
    except json.JSONDecodeError:
        logger.warning("Skip profile_links migration: invalid JSON")
        return
    if not isinstance(data, list) or not data:
        return

    for order, entry in enumerate(data, start=1):
        if not isinstance(entry, dict) or not entry.get("platform") or not entry.get("url"):
            continue
        db.add(
            SocialLink(
                platform=str(entry["platform"]),
                label=entry.get("label"),
                url=str(entry["url"]),
                visible=_legacy_visible(entry),
                sort_order=order,
            )
        )
    await db.commit()
    logger.info("Migrated legacy profile_links JSON into social_links")


async def _migrate_notice(db: AsyncSession) -> None:
    """把旧的 notice_text/enabled/version 三个配置合并为一条 banner 公告（幂等）。"""
    count = (await db.execute(select(func.count(Notice.id)))).scalar_one()
    if count > 0:
        return
    item = await site_crud.get_config(db, "notice_text")
    if item is None or not item.value.strip():
        return
    version_item = await site_crud.get_config(db, "notice_version")
    enabled_item = await site_crud.get_config(db, "notice_enabled")
    try:
        version = max(1, int(version_item.value)) if version_item and version_item.value else 1
    except ValueError:
        version = 1
    db.add(
        Notice(
            title="网站公告",
            content=item.value,
            type="banner",
            enabled=_legacy_visible({"visible": enabled_item.value if enabled_item else True}),
            version=version,
            sort_order=1,
        )
    )
    await db.commit()
    logger.info("Migrated legacy notice config into notices")


async def seed_default_data() -> None:
    async with AsyncSessionLocal() as db:
        user = await user_crud.get_by_username(db, settings.init_admin_username)
        if user is None:
            user = await user_crud.create(
                db, settings.init_admin_username, hash_password(settings.init_admin_password)
            )
            logger.info("Created initial admin user: %s", user.username)

        existing = (await db.execute(select(SiteConfig))).scalars().all()
        existing_keys = {item.key for item in existing}
        for key, value in DEFAULT_SITE_CONFIG.items():
            if key not in existing_keys:
                await site_crud.set_config(db, key, value)
        await db.commit()

        await _migrate_menus(db)
        await _seed_default_menus(db)
        await _add_archive_menu(db)
        await _migrate_social_links(db)
        await _migrate_notice(db)
        await sweep_existing_uploads(db)


async def seed_demo_data() -> None:
    """仅当数据库尚无文章时才播种演示内容。"""
    async with AsyncSessionLocal() as db:
        # 以 posts 表是否为空作为判断：已有数据说明是正式使用，绝不覆盖/重复播种
        post_count = (await db.execute(select(func.count(Post.id)))).scalar_one()
        if post_count > 0:
            return

        category_map = {}
        for item in DEMO_CATEGORIES:
            category = Category(
                name=item["name"],
                slug=item["slug"],
                sort_order=item["sort_order"],
                color=item.get("color"),
            )
            db.add(category)
            category_map[item["slug"]] = category

        for item in DEMO_CATEGORIES:
            parent_slug = item.get("parent")
            if parent_slug:
                category_map[item["slug"]].parent = category_map[parent_slug]

        tag_map = {}
        for item in DEMO_TAGS:
            tag = Tag(**item)
            db.add(tag)
            tag_map[item["slug"]] = tag

        for item in DEMO_BANNERS:
            db.add(Banner(**item))

        now = datetime.now(UTC)
        for i, item in enumerate(DEMO_POSTS):
            post_status = item.get("status", "published")
            post = Post(
                title=item["title"],
                slug=item["slug"],
                summary=item["summary"],
                content=item["content"],
                status=post_status,
                is_top=item.get("featured", False),
                is_featured=item.get("featured", False),
                sort_weight=item.get("sort_weight", 0),
                author=item.get("author"),
                category=category_map[item["category"]],
                tags=[tag_map[slug] for slug in item.get("tags", [])],
                published_at=now - timedelta(days=i) if post_status == "published" else None,
                view_count=50 + i * 23,
            )
            db.add(post)

        for item in DEMO_FRIEND_LINKS:
            db.add(FriendLink(**item))

        await db.commit()
        logger.info(
            "Seeded demo data: %d categories, %d tags, %d posts, %d friend links, %d banners",
            len(DEMO_CATEGORIES),
            len(DEMO_TAGS),
            len(DEMO_POSTS),
            len(DEMO_FRIEND_LINKS),
            len(DEMO_BANNERS),
        )


async def main() -> None:
    from app.core.logging import setup_logging

    setup_logging(True)
    from app.core.database import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_data()
    await seed_demo_data()
    logger.info("Seed completed.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


async def sweep_existing_uploads(db: AsyncSession) -> None:
    """把媒体库建立前已落盘的上传文件登记入库（一次性、幂等）。"""
    # 已有任何媒体记录说明此前已扫描过，跳过；目录不存在也直接返回
    count = (await db.execute(select(func.count(MediaAsset.id)))).scalar_one()
    if count > 0:
        return
    root = settings.upload_path
    if not root.exists():
        return
    known: set[str] = set()
    added = 0
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or path.name.startswith(".")
            or path.suffix.lower()
            not in {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".svg",
            }
        ):
            continue
        stored = path.name
        if stored in known:
            continue
        known.add(stored)
        rel = path.relative_to(root)
        stat = path.stat()
        db.add(
            MediaAsset(
                name=path.name,
                stored_name=stored,
                rel_path=str(rel),
                url=f"/uploads/{rel}",
                ext=path.suffix.lower(),
                mime=None,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC).replace(tzinfo=None),
            )
        )
        added += 1
    if added:
        await db.commit()
        logger.info("Registered %d legacy upload files into media library", added)
