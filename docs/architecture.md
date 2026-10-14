# 架构设计

## 1. 整体架构

前后端分离架构，前端 SPA 通过 HTTP 调用后端 REST API，前端所有展示内容均由后台管理数据动态控制。

```
浏览器 (Vue3 SPA)
   │  HTTP / JSON
   ▼
FastAPI (Uvicorn)
   │  SQLAlchemy (async)
   ▼
SQLite
```

- **前端**：Vite 开发服务器代理 `/api` 请求到后端，避免开发期跨域问题。
- **后端**：FastAPI 应用提供 REST 接口，启动时自动建表并写入种子数据。
- **认证**：登录签发 JWT，前端存储于 `localStorage`，axios 拦截器自动附带 `Authorization` 头。

## 2. 分层设计（后端）

| 层 | 目录 | 职责 |
| --- | --- | --- |
| 入口层 | `app/main.py` | 应用装配、CORS、请求日志中间件、全局异常处理、生命周期 |
| 配置层 | `app/core/config.py` | 读取环境变量（前缀 `BLOG_`） |
| 安全层 | `app/core/security.py` | 密码哈希（bcrypt）、JWT 签发与解析 |
| 日志层 | `app/core/logging.py` | 控制台 + 文件轮转日志 |
| 数据层 | `app/core/database.py` | 异步引擎、会话工厂、`get_db` 依赖 |
| 模型层 | `app/models/` | SQLAlchemy ORM 模型 |
| 校验层 | `app/schemas/` | Pydantic 请求/响应模型 |
| 路由层 | `app/api/` | API 路由，`deps.py` 提供认证依赖 |
| 数据访问层 | `app/crud/` | 数据库操作封装，供路由调用 |
| 初始化 | `app/seed.py` | 管理员账号与默认站点配置 |

## 3. 数据模型

- `users`：管理员账号（密码以 bcrypt 哈希存储）
- `posts`：文章（标题、Slug、封面、正文 Markdown、摘要、状态、浏览量、置顶、分类、发布时间）
- `categories`：分类（名称、Slug、排序）
- `tags`：标签（名称、Slug），与文章多对多
- `site_configs`：键值型站点配置（站点名、描述、Logo（设置后展示于导航栏左侧，空则回退站点名）、备案（页脚链接至工信部备案系统）、页脚、关于我介绍 Markdown（`site_about_markdown`，About 页 MdPreview 渲染）、背景方案（`site_background` 枚举）等标量配置；布尔值以字符串 "true"/"false" 存储）
- `friend_links`：友链（名称、地址、描述、图标 URL（可空，经 `/admin/upload` 上传）、`visible` 显隐（公开列表过滤，管理端可见全部）、排序；迁移 `8a2f1c3d4b5e`/`9c4e2f6a1d7b`）
- `menu_items`：导航菜单（label/path/icon/type[link|category]/is_external/parent_id 两级/sort_order/visible；“首页”项由接口固定拼接不落库；默认 4 项首次启动种入一次，配置标记 `menus_seeded` 防删空后回填）
- `media_assets`：媒体库（上传图片登记：原名/存储名 `时间戳_哈希前8位`/相对路径 `年/月/日/文件`/url/mime/大小/时间；上传按此规则落盘并可被列表/引用保护删除；首次启动盘点 uploads 既有文件；迁移 `af5b7e9d2c31`）
- `social_links`：社交链接（platform 预置或 custom+label/url/visible/sort_order，驱动简介卡片图标）
- `notices`：公告（title/content/type[banner|dialog|page]/enabled/version/sort_order；内容变更自动升版本触发重推）
- 数据迁移：旧 `site_menus`/`profile_links` JSON 配置与旧公告三键在启动时一次性迁移入对应表（解析失败仅告警，幂等）；迁移后旧键不再出现在默认配置与管理表单

## 4. 统一响应格式

成功：`{ "code": 0, "message": "success", "data": ... }`
失败：`{ "code": <http状态码>, "message": "错误信息", "data": null }`

## 5. 认证与权限

- `POST /api/v1/auth/login` 校验用户名密码，返回 JWT。
- 管理端接口通过 `CurrentUser` 依赖（HTTPBearer）强制鉴权，无/无效 token 返回 401。
- 前端路由守卫拦截未登录访问 `/admin` 下的页面。

## 6. 日志设计

- `logs/app.log` 按天轮转，保留 7 天。
- 中间件记录每个请求：方法、路径、状态码、耗时。
- 全局异常处理器记录未捕获异常的堆栈。

## 7. 前端状态与路由

- **Pinia**：`auth`（登录态/用户）、`config`（站点配置 + 并行聚合 /menus、/social-links、/notices，各自失败独立回退：默认菜单/空列表）、`theme`（暗色模式）。
- **健壮性防线**：所有公网读取处均有默认值回退（菜单表空→内置默认菜单、颜色非法→主题蓝、布尔字符串统一 `utils/config.js` 解析）；图标名不在 `utils/navIcons.js` 注册表时不渲染图标而非报错；配置更新后端白名单校验 + 前端同规则预校验。
- **路由**：`/` 前台（FrontLayout 包裹），`/admin` 后台（AdminLayout 包裹 + 认证守卫），`/admin/login` 登录页。
- **Axios**：请求拦截附带 token，响应拦截统一解包 `{code,message,data}` 并处理 401 跳转登录。

## 8. RSS 订阅与归档（0.12.0）

- `GET /feed.xml`（同时挂载于 `/api/v1/feed.xml`，便于 Vite/nginx 代理）：RSS 2.0，最新 20 篇已发布文章，标题/链接/摘要/正文/分类/发布时间，站点名/描述/作者取站点配置；纯 XML 不走统一信封；前端 `index.html` 以 `<link rel="alternate">` 自动发现。
- `GET /posts/archive`：仅已发布，按年/月倒序分组返回 `[{year, month, posts[]}]`；路由声明须在 `/posts/{slug}` 之前避免被通配捕获。
- 浏览量去重：`GET /posts/{slug}?count_view=false` 不自增；详情页以 localStorage `blog_viewed:{slug}` 做 5 分钟节流。
