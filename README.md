# 个人博客系统

基于前后端分离架构的个人博客，前台展示 + 后台管理，前台内容全部由后台数据动态控制。

## 功能特性

- 前台内容后台动态驱动：文章、分类、标签、友链、轮播图、站点配置
- 多级分类（两级父子栏目）+ 分类树归档页；首页栏目 Tab 切换 + 子栏目钻取 + 面包屑
- 首页 Hero 轮播 + 入场动画 + 数据统计条 + 栏目分区；首页栏目 Tab 与导航菜单路由联动（选中态同步）
- 统一文章卡片：封面缩略图、作者、彩色可点标签、置顶/推荐徽章
- 侧边卡片系统（后台可配显隐）：个人简介卡（头像+平台链接图标）、标签云、最近发布
- 全站搜索面板（Ctrl/Cmd+K 唤起 + 关键词高亮）
- 网站公告（可关闭、版本化重推）
- 分类/标签独立配色（后台色板可设）、可见性开关与排序控制（文章置顶/推荐/权重）
- 主题强调色、站点作者、首页栏目数后台可配
- Markdown 渲染（md-editor-v3：后台 MdEditor 编辑器 + 前台 MdPreview/MdCatalog 目录，代码高亮、粘贴插图）
- 后台管理：仪表盘、文章（Markdown 实时预览编辑器 + 封面上传）、分类/标签（模态框快速新增）、轮播图、友链、站点配置
- 页脚友链横排展示；JWT 登录鉴权、暗色主题、代码复制、回到顶部

## 技术栈

| 端 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios |
| 后端 | Python + FastAPI + SQLAlchemy 2.0 + SQLite |
| 认证 | JWT（PyJWT） |
| 日志 | logging + RotatingFileHandler（按天轮转） |
| 质量 | ruff / pytest（后端）、ESLint / Prettier（前端） |

## 目录结构

```
blog/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口、CORS、日志中间件、异常处理
│   │   ├── core/            # 配置、日志、安全、数据库
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── schemas/         # Pydantic 校验模型
│   │   ├── api/             # 路由（deps、v1 端点）
│   │   ├── crud/            # 数据访问层
│   │   └── seed.py          # 初始化数据（管理员、站点配置）
│   ├── tests/               # pytest 测试
│   ├── data/                # SQLite 数据库文件
│   └── logs/                # 运行日志
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── api/             # axios 封装 + 接口模块
│       ├── stores/          # Pinia 状态（auth/config/theme）
│       ├── router/          # 路由 + 登录守卫
│       ├── layouts/         # 前台 / 后台布局
│       ├── views/
│       │   ├── front/       # 前台页面
│       │   └── admin/       # 后台管理页面
│       └── styles/          # 全局样式
└── docs/                    # 项目文档
```

## 快速开始

### 后端

```bash
cd backend
cp .env.example .env          # 按需修改配置（数据库、密钥、初始管理员）
uv sync                       # 安装依赖
uv run uvicorn app.main:app --reload --port 8000
```

- 启动时自动创建数据表并初始化管理员账号与默认站点配置。
- 接口文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

- 开发服务器：http://localhost:5173（已配置 `/api` 代理到后端 8000 端口）

### 测试与代码检查

```bash
cd backend && uv run pytest && uv run ruff check app
cd frontend && npm run build
```

### 数据库迁移（Alembic）

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"   # 生成新迁移
uv run alembic upgrade head                        # 应用迁移
```

### Docker 部署

```bash
docker compose up -d --build
# 前端: http://localhost:8080 （nginx 托管并反代 /api、/uploads 到后端）
```

## 默认账号

- 用户名：`admin`
- 密码：`admin123`（由 `.env` 中 `BLOG_INIT_ADMIN_*` 控制）

## 文档

- [架构设计](./docs/architecture.md)
- [API 接口规范](./docs/api.md)
- [开发日志](./CHANGELOG.md)