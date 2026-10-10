# 后台配置体系重构 设计文档

日期：2026-10-08 · 状态：已确认 · 目标版本：0.8.0

## 1. 背景与目标

当前后台站点配置是"一张大表单 + 两个裸 JSON 字段（`site_menus`、`profile_links`）"，存在误修改风险，且导航/社交链接/公告无法结构化管控。本次将其升级为**结构化、分类拆分、带校验与默认回退**的配置体系。

成功标准：

1. 顶部导航可在后台增删改（两级、排序、显隐、前置 el-icon 图标、外链开关），"首页"固定首位不可动，"栏目"动态下拉类型保留。
2. 简介卡片社交链接为结构化列表（平台/URL/显隐/排序），可增减。
3. 公告支持多条并存、三种尺寸：横幅（小）/弹窗（中）/单页（大）。
4. 配置页按 Tab 分组；删除 `site_menus`、`profile_links` 两个 JSON 字段；后端对已知配置键做白名单校验；所有公开读取处保留默认值回退（配置损坏前台不白屏）。
5. 旧数据（`site_menus`/`profile_links` JSON、旧公告三键）启动时自动迁移，幂等。

## 2. 架构选型

- 导航、社交链接、公告使用**独立表 + CRUD API**（对齐 Banner/FriendLink 既有模式），而非结构化 JSON 塞回 site_config：天然支持校验、排序、部分更新。
- 标量配置拆分 = ConfigManage 单页 Tab 分组；列表型资源 = 独立管理页（菜单、公告）。

## 3. 数据模型

### 3.1 `menu_items`（新表）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| label | String(50) | 导航文字 |
| path | String(500), nullable | type=link 必填；type=category 忽略 |
| icon | String(50), nullable | Element Plus 图标组件名（预置清单） |
| type | String(20), default 'link' | `link` / `category` |
| is_external | bool, default False | 外链（新开窗口） |
| parent_id | FK menu_items.id, nullable | 仅两级（代码校验） |
| sort_order | int, default 0 | |
| visible | bool, default True | |

约束（应用层）：子项不得再有子项；`category` 类型不允许子项；link 的 path 必须 `/` 开头，外链必须 `is_external=True` 且 http(s):// 开头。

"首页"不落库：公开接口总是首位拼入固定项 `{label:'首页', path:'/', icon:'HomeFilled'}`，不可删/改/挪。

### 3.2 `social_links`（新表）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| platform | String(30) | 预置键（github/juejin/zhihu/csdn/x/email/wechat/bilibili）或 `custom` |
| label | String(50), nullable | custom 时用于展示名 |
| url | String(500) | http(s):// 或 mailto: |
| visible | bool, default True | |
| sort_order | int, default 0 | |

### 3.3 `notices`（新表）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int PK | |
| title | String(200) | |
| content | Text | banner=纯文本；dialog/page=Markdown |
| type | String(20) | `banner` / `dialog` / `page` |
| enabled | bool, default True | |
| version | int, default 1 | 内容更新时后端自动 +1（重新推送记忆） |
| sort_order | int, default 0 | |
| created_at / updated_at | datetime | |

展示规则：横幅 = 同类型中 `sort_order` 最小且 enabled 的一条；弹窗 = 最新一条用户未关闭的 dialog（localStorage `blog_notice_dismissed:{id}` 存 version）；单页 = 前端路由 `/notice/:id` 渲染 Markdown，入口由用户在菜单管理中自行添加菜单项。

### 3.4 数据迁移（启动时，幂等）

`seed.py` 新增迁移函数（参照现有 key 幂等风格）：

- `menu_items` 表为空且 `site_menus` JSON 合法非空 → 转入（`type:'category'` 保留类型；其余为 link）。
- `social_links` 表为空且 `profile_links` JSON 合法非空 → 转入（platform/url）。
- `notices` 表为空且 `notice_text` 非空 → 建一条 banner（content=notice_text，version=旧 notice_version 非法则 1；`notice_enabled=false` 则 enabled=False）。

迁移完成后旧三键/两 JSON 键不再出现在默认配置与管理表单（DB 中残留无害）。`DEFAULT_SITE_CONFIG` 移除 `site_menus`、`profile_links`、`notice_text`、`notice_enabled`、`notice_version`。

## 4. API 设计（全部走 `{code,message,data}` 信封）

| 方法/路径 | 鉴权 | 说明 |
| --- | --- | --- |
| GET /menus | 公开 | 树形（两级），仅 visible，拼接固定首页项，表空回退默认菜单 |
| GET /admin/menus | 管理员 | 完整树（含隐藏） |
| POST /admin/menus | 管理员 | 创建（校验两级/类型/URL） |
| PUT /admin/menus/{id} | 管理员 | 更新（含排序/父级/显隐） |
| DELETE /admin/menus/{id} | 管理员 | 删除（有子项时连带删除或 409——采用连带删除子项，前端二次确认） |
| GET /social-links | 公开 | 仅 visible，按 sort_order |
| POST/PUT/DELETE /admin/social-links[/{id}] | 管理员 | CRUD |
| GET /notices | 公开 | enabled 列表（page 类型仅返回 id/title/updated_at 摘要） |
| GET /notices/{id} | 公开 | 单条（含 content），仅 enabled |
| POST/PUT/DELETE /admin/notices[/{id}] | 管理员 | CRUD；PUT 内容变更自动 version+1 |

配置批量更新 `PUT /admin/site/config` 增加**已知键白名单校验**：`site_accent_color` 必须 `#RGB/#RRGGBB`；`homepage_section_count` 1–8；`sidebar_tag_count` 1–30；非法值 422（整批拒绝，先校验后写入）。

## 5. 前端

### 5.1 状态与容错

- `stores/config.js` 扩展：并行拉取 `/menus`、`/social-links`、`/notices`，任一失败使用兜底（默认菜单/空链接/空公告），`siteMenus()`、`profileLinks()` 改为读结构化数据，删除 JSON 解析路径。
- 统一布尔解析 helper（`isEnabled` 式，兼容 "true"/"1"/true），前端所有读取处使用。
- 图标渲染：预置约 30 个常用 `@element-plus/icons-vue` 图标名注册表（管理端选择器与前台渲染共用一份清单，新文件 `composables/useNavIcons.js` 或 `utils/navIcons.js`），`<component :is>` 动态渲染。

### 5.2 后台

- 新页 `MenuManage.vue`（路由 `/admin/menus`，侧边栏入口"导航菜单"）：el-table 树形展示；对话框表单：文字、类型（内部链接/外部链接/栏目下拉）、路径/URL、父级下拉（仅顶级、栏目不可选为父）、图标网格选择器、显示开关、排序。
- 新页 `NoticeManage.vue`（`/admin/notices`，"公告管理"）：列表（标题/类型/状态/版本/更新时间）+ 表单：类型单选；banner=纯文本 textarea；dialog/page=MdEditor（复用 `useMdEditor` 懒加载）。
- `ConfigManage.vue` 拆 Tab：**基础信息**（名称/描述/副标题/作者/Logo/ICP/页脚）、**外观**（强调色/首页栏目数）、**侧边栏**（简介卡片开关/头像/简介 + 社交链接行编辑：平台下拉+URL+显隐+排序，即时 CRUD）、**页脚**。移除 `site_menus`、`profile_links`、旧公告三键表单项。
- AdminLayout 侧边菜单同步添加两项。

### 5.3 前台

- `FrontLayout.vue`：菜单数据改自 store 结构化 menus；图标渲染；外链 `<a target=_blank rel=noopener>`；栏目下拉逻辑保留。
- `NoticeBar.vue`：改读 store 中 banner 公告（规则见 3.3），关闭记忆 key 升级为含 id+version。
- 新组件 `NoticeDialog.vue`：挂载于 FrontLayout；弹窗展示 dialog 公告（MdPreview），按 `blog_notice_dismissed:{id}` = version 判断是否弹过。
- 新页面 `views/front/NoticePage.vue`：路由 `/notice/:id`，MdPreview 渲染，404 兜底回首页。
- `ProfileCard.vue`：链接数据改读 `GET /social-links`（经 store），custom 平台显示 label 首字，预置平台保留配色/字母映射。

## 6. 测试策略

- pytest（in-memory SQLite，新种子进 `db_session` fixture）：
  - 菜单：创建/两级限制（三层拒绝）、外链与 path 校验、category 约束、公开接口拼接首页+过滤隐藏、表空回退默认、删除连带子项、JSON 迁移幂等。
  - 社交链接：CRUD、公开仅 visible、JSON 迁移幂等。
  - 公告：CRUD、内容变更 version 自增、公开摘要不含 content（列表）、enabled 过滤、旧公告迁移、404。
  - 配置校验：非法颜色/越界数字 → 422 且不写入。
- 前端：`npm run build` 通过；手动冒烟：菜单管理↔顶栏渲染（图标/下拉/外链/首页固定）、公告三形态与关闭记忆、社交链接增删↔简介卡片、配置 Tab 保存。
- Alembic：三张新表一份迁移（自引用 FK 用 `batch_alter_table`），`upgrade head` 验证。

## 7. 文档义务（每个工作流完成时）

- `CHANGELOG.md` 追加条目（0.8.0 分节累加，含此前 el-switch 开关显示修复）。
- `docs/api.md` 增补新端点；`docs/architecture.md` 增补新表与配置结构；`README.md` 若涉及后台功能清单则同步；`AGENTS.md` 更新新约定（两级限制、固定首页项、Tab 结构、图标清单文件）。

## 8. 实施顺序

A 导航 → B 社交链接 → C 公告 → D 配置拆分与校验收尾。每阶段独立可用、可验证。

## 9. 风险与对策

- SQLite 自引用 FK 迁移：batch_alter_table（既有经验，AGENTS.md）。
- 新模型忘在 `app/models/__init__.py` 注册 → 建不出表：作为每个阶段 checklist。
- 旧 JSON 脏数据：迁移解析失败仅告警跳过，不阻塞启动。
- 多弹窗公告刷屏：一次会话只弹最新一条未读 dialog。
- 图标名不在注册表：前台回退无图标渲染，不报错。
