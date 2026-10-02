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
- `site_configs`：键值型站点配置（站点名、描述、Logo、备案、页脚）
- `friend_links`：友链（名称、地址、描述、排序）

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

- **Pinia**：`auth`（登录态/用户）、`config`（站点配置）、`theme`（暗色模式）。
- **路由**：`/` 前台（FrontLayout 包裹），`/admin` 后台（AdminLayout 包裹 + 认证守卫），`/admin/login` 登录页。
- **Axios**：请求拦截附带 token，响应拦截统一解包 `{code,message,data}` 并处理 401 跳转登录。