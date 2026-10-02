# 开发日志 / 更新记录

本文件记录项目各阶段的功能开发与变更，按时间倒序排列。

## [0.5.0] - 2026-09-16

### 导航联动、侧边卡片、全站搜索、公告与编辑器升级

- 导航与首页栏目**路由联动**：
  - 首页栏目 Tab 改为由 `route.query.category_id` 驱动（切换 Tab 即写路由），导航栏与首页选中态彻底双向同步，后退/分享链接保持栏目状态
  - 导航菜单项支持 `{ type: 'category' }`：自动拉取分类树渲染栏目下拉，父菜单命中子项即高亮
- 侧边卡片系统（后台可配显隐）：
  - 新组件 `ProfileCard.vue`：头像 + 昵称 + 简介 + 平台链接图标（GitHub/掘金/知乎/邮箱/CSDN/X 等预设，未匹配显示通用图标）
  - 新组件 `HomeSidebar.vue`：按 `profile_visible` / `sidebar_tags_visible` / `sidebar_recent_visible` 渲染 简介卡 / 标签云 / 最近发布；首页与文章列表页共用
  - 新增配置：`site_avatar`、`site_bio`、`profile_links`(JSON)、三个侧边卡片显隐开关
- 全站搜索面板 `GlobalSearch.vue`：
  - 顶栏放大镜按钮 + `Ctrl/Cmd + K` 唤起，Esc/点击外部关闭
  - 输入即时搜索（防抖 250ms），结果列表标题/摘要**关键词高亮**，Enter 进详情，可跳转搜索页
- 网站公告 `NoticeBar.vue`：站点顶部横幅，可关闭（`localStorage` 按 `notice_version` 记忆，改版本号可重新推送）
- 编辑器升级 `MarkdownEditor.vue`：**导入 .md 文件**（FileReader 填充正文，二次确认覆盖）、字数统计、全屏编辑、`Ctrl+S` 保存（PostEdit 已接）
- 站点配置页扩展：头像/简介/平台链接/公告/侧边显隐等新字段
- 种子数据补充新配置项默认值；无数据表变更（全部走 SiteConfig）
- 全量验证：13 个 pytest 用例通过、ruff 全绿、前端构建通过、live 冒烟（配置返回/栏目树/搜索）正常

## [0.4.0] - 2026-09-16

### 内容展示与交互升级

- Bug 修复：`useReveal` 滚动浮现动画不再忽略异步渲染的元素（`MutationObserver` 自动观察新增 `.reveal`），首页栏目区、分类页恢复可见
- 统一文章卡片 `PostCard.vue`：
  - 封面缩略图（有图显示，无图纯文字）+ 置顶/推荐徽章 + 分类名
  - 作者显示（`post.author` 覆盖站点作者 `site_author`，头像圆点）
  - 多标签彩色可点击（跳转标签筛选，阻止卡片冒泡）
  - 首页/文章列表/分类页统一复用
- 首页栏目交互：
  - 文章区改为"栏目 Tab"切换（全部 + 顶级分类），**选中态高亮**
  - 选中父栏目显示子分类 chips 钻取 + 面包屑路径
  - 栏目数量由后台 `homepage_section_count` 控制，顺序由 `sort_order` 控制
- 友链移至页脚横排展示（保留 `/friends` 卡片页）
- 文章列表页：分类层级钻取（全部 → 父栏目 → 子栏目）+ 面包屑 + 标签筛选指示
- 数据模型：
  - `posts` 新增 `is_featured`（推荐）、`author`、`sort_weight`（手动排序权重）
  - `categories` 新增 `visible`；`tags` 新增 `visible`、`sort_order`
  - `site_configs` 新增 `site_author`、`homepage_section_count`
  - 排序规则：置顶 → 排序权重 → 发布时间倒序；Alembic 迁移 `f49a3390e39a`
- 后台管理：
  - 分类/标签新增/编辑改为**模态框**，支持"保存并继续"快速连续新增
  - 分类/标签表格内联可见性开关 + 排序输入
  - 文章管理表格新增置顶/推荐开关、排序权重输入（行内直改）
  - 文章编辑表单补作者/推荐/权重；站点配置补站点作者、首页栏目数
- 文章详情页：作者信息 + 复制链接按钮
- 测试：新增排序权重、可见性、作者等用例，共 13 个全部通过

## [0.3.0] - 2026-09-16

### 内容层级与首页视觉升级

- 多层分类：
  - `Category` 增加 `parent_id` 自关联，支持两级栏目/分类层级
  - 新增 `GET /categories/tree` 返回分类树（`post_count` 聚合子分类）
  - `GET /posts` 的 `category_id` 支持父分类过滤：自动包含其子分类下的文章
  - 删除含子分类的父分类返回 409 拒绝
  - 后台分类管理改为树形表格（父分类选择 + 颜色选择器）
- 首页视觉升级：
  - 新增 `Banner` 模型与 `GET /banners`（仅启用），后台新增轮播图管理页
  - 首页重构为 Hero 轮播 + 入场动画（标题/副标题/CTA 分阶段浮现）+ 数据统计条 + 按顶级分类分区展示 + 保留侧边栏
  - 站点配置扩展：`site_slogan`、`site_accent_color`（主题强调色，前端动态切换 CSS 变量）、`site_menus`（导航菜单 JSON，前台多级下拉）
  - 新增 `GET /site/stats`（文章/分类/标签数、总阅读量、运行天数）
  - 新增"分类"归档页 `GET /categories/tree` 驱动
- 彩色标签：
  - `Category`、`Tag` 增加 `color` 字段；后台用 `el-color-picker` + 预设色板
  - 前端新增 `ColoredTag.vue` 组件（亮/暗模式自适应），文章列表/详情/首页/侧边栏统一使用
- 性能优化：
  - Vite 手动分包：`element-plus`、`vue` 全家桶、`marked+highlight` 独立 chunk；`marked`/`highlight.js` 改为动态 import（仅文章详情与编辑器页加载）
  - 主入口 chunk 由约 949KB 降至约 6KB
  - 代码块复制按钮、回到顶部按钮、首页滚动浮现动画（`useReveal`，尊重 `prefers-reduced-motion`）
- 数据模型：新增 Banner 表 + `categories.parent_id/color`、`tags.color` 字段，Alembic 迁移 `43f81752c57c`（SQLite 需 batch 模式重建表）
- 测试：新增分类树/父过滤/彩色字段、轮播与站点统计等用例，共 11 个全部通过

## [0.2.0] - 2026-09-13

### 内容生产与阅读体验

- 封面上传：
  - 后端 `POST /api/v1/admin/upload`（JWT 保护），扩展名白名单 + 大小限制（`BLOG_MAX_UPLOAD_SIZE_MB`），随机文件名存 `backend/uploads/`
  - 挂载 `/uploads` 静态文件服务；`PostEdit.vue` 封面改用 `el-upload`（选图/预览/移除）
- Markdown 编辑器：
  - 抽取 `src/composables/useMarkdown.js`（marked + highlight.js 渲染，前台详情页与后台编辑器共用）
  - 新增 `MarkdownEditor.vue`（编辑/预览 Tab + 分栏开关，v-model 双向绑定），`PostEdit.vue` 正文接入
- 标签后台管理：
  - 后端新增 tags 的 admin CRUD 路由（创建/更新/删除）
  - 前端新增 `TagManage.vue` 页面并注册路由与侧边菜单
- 阅读体验增强：
  - 后端 `GET /api/v1/posts/{slug}/neighbors` 返回上一篇/下一篇
  - 文章详情页新增自动目录 TOC（滚动高亮）与上一篇/下一篇导航
  - 首页改双栏布局：文章列表 + 侧边栏（分类/标签/最近发布）；文章列表页支持 `category_id`/`tag_id` 查询联动
- 工程化：
  - 引入 Alembic 迁移（`migrations/`），已生成 baseline 迁移并验证 `upgrade head`
  - 新增 Docker 部署：`backend/Dockerfile`（uv 镜像）、`frontend/Dockerfile`（构建 → nginx 托管 + 反向代理）、`docker-compose.yml`
  - 测试新增 3 个用例（neighbors、tags CRUD、上传鉴权与类型校验），共 8 个用例全部通过
- 演示数据：
  - 启动时若 `posts` 表为空则自动写入演示内容（3 分类、5 标签、4 篇带代码/目录的 Markdown 文章、3 个友链），幂等可重复执行，方便联调

## [0.1.0] - 2026-09-13

### 基础框架搭建

- 初始化 Git 仓库与项目目录骨架（`backend/`、`frontend/`、`docs/`）。
- 后端：
  - 基于 uv 管理 Python 依赖（pyproject.toml），提供 `blog-server` 入口脚本。
  - FastAPI 应用骨架：CORS、请求日志中间件、统一响应格式、全局异常处理。
  - 配置中心：环境变量前缀 `BLOG_`，支持 `.env` 文件（见 `.env.example`）。
  - 日志系统：`logs/app.log` 按天轮转、保留 7 天。
  - 数据层：SQLAlchemy 2.0 异步引擎 + aiosqlite。
  - ORM 模型：用户、文章、分类、标签、站点配置、友链。
  - JWT 认证：登录签发 token，管理端接口统一鉴权（HTTPBearer）。
  - 种子数据：启动自动建表，初始化管理员账号与默认站点配置。
  - 接口：登录/当前用户、文章公开列表与详情、管理端文章 CRUD、分类/标签、站点配置、友链。
  - 测试：pytest + pytest-asyncio，覆盖登录、鉴权、文章发布流程（4 个用例）。
  - 代码检查：ruff 全部通过。
- 前端：
  - Vite + Vue 3 + Element Plus（中文语言包）+ Pinia + Vue Router + Axios。
  - 目录分层：`api/`、`stores/`、`router/`、`layouts/`、`views/`、`styles/`。
  - 请求层：axios 拦截器（token 注入、统一解包、401 跳转登录）。
  - 状态：认证、站点配置、暗色主题三个 Pinia store。
  - 路由：前台路由组、后台路由组（认证守卫）、懒加载页面。
  - 页面：前台首页/文章列表/文章详情（Markdown + 代码高亮）/友链/关于；
          后台登录/仪表盘/文章管理/文章编辑/分类管理/站点配置/友链管理。
- 文档：README（项目说明与启动方式）、`docs/architecture.md`（架构设计）、
        `docs/api.md`（接口规范）、本文件（开发日志）。

### 待办

- [ ] 封面图上传接口与后台上传组件
- [ ] 后台文章编辑的 Markdown 实时预览
- [ ] 文章上一篇/下一篇导航与目录 TOC
- [ ] Alembic 迁移初始版本
- [ ] Docker 部署配置
- [ ] 评论接入（Giscus 等第三方）