# 后台配置体系重构 实施计划

**Spec:** `docs/superpowers/specs/2026-10-08-admin-config-overhaul-design.md`（先读它，本计划只记录实现决策）

**Goal:** 导航菜单/社交链接/公告结构化 + 配置页 Tab 拆分 + 白名单校验 + 默认回退。

**Architecture:** 三张新表（menu_items/social_links/notices）+ 各自 CRUD 端点（新端点模块 menus.py/social.py/notices.py，在 `api/v1/router.py` 注册）；前端 config store 并行聚合三个公开接口并各自兜底；后台新增 MenuManage/NoticeManage 两页 + ConfigManage 拆 Tab。

**执行方式:** Native（本会话内实现）。测试驱动：后端每任务先写失败测试。提交需用户批准，任务末尾统一 `git status` 检查点，不擅自 commit/push。

## Global Constraints

- 后端命令一律 `uv run ...`，在 `backend/` 下执行；`uv run pytest`、`uv run ruff check app`、`uv run ruff format app`；行宽 100、Python 3.12 类型注解。
- 所有响应走 `ok()` 信封；管理端点加 `_: CurrentUser`。
- 新模型必须 import 进 `app/models/__init__.py`。
- 布尔配置值为字符串 "true"/"false"，前端统一用 helper 解析。
- 前端不新增依赖；plain JS + `<script setup>`；`@/` 别名。
- Alembic：`create_table` 可直接建自引用 FK；本迁移 `down_revision` 以 `uv run alembic heads` 实际输出为准（应为 `ddd6a85857d5`）。
- 每个工作流完成时更新 `CHANGELOG.md`（0.8.0 分节累加）。

## Review Focus（各条已在对应任务钉住测试）

1. 旧 JSON 脏数据（非法 JSON/元素缺字段）→ 启动迁移仅告警跳过，不阻塞、不写入。→ Task A2/B2/C2。
2. 菜单父级隐藏 → 子项一并不可见（公开树整体跳过隐藏父）。→ Task A1。
3. 一次批量配置里一个键非法 → 整批 422 拒绝、其余键也不写入。→ Task D1。
4. DB 中图标名不在前端注册表 → 渲染无图标而非报错。→ Task A3（resolveIcon 返回 null + v-if）。
5. 多条启用弹窗公告 → 仅弹最新一条未关闭者，其余静默。→ Task C3（store 选择逻辑 + 后端排序测试 C1）。

---

### Task A1: 菜单后端（模型/迁移/CRUD/端点/校验）

**Files:**
- Modify: `backend/app/models/site.py`（追加 MenuItem）
- Modify: `backend/app/models/__init__.py`
- Create: `backend/migrations/versions/<rev>_menu_social_notice_tables.py`（一次建三张表，见 B1/C1 字段）
- Modify: `backend/app/schemas/site.py`
- Modify: `backend/app/crud/site.py`
- Create: `backend/app/api/v1/endpoints/menus.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_menus.py`

**Interfaces:**
- Produces：模型 `MenuItem(id, label:str, path:str|None, icon:str|None, type:str, is_external:bool, parent_id:int|None, sort_order:int, visible:bool)`；`crud.site.list_menus(db)`、`get_menu(db, id)`；schema `MenuItemCreate/MenuItemUpdate/MenuItemOut/MenuNodeOut(label, path, icon, type, is_external, children)`；端点 `GET /menus`（公开）、`GET|POST /admin/menus`、`PUT|DELETE /admin/menus/{id}`。
- 公开树规则：首位固定合成 `{"label":"首页","path":"/","icon":"HomeFilled","type":"link","is_external":false,"children":[]}`（不落库）；表空 → 回退默认菜单（首页/文章/posts、标签/tags、友链/friends、关于/about）；仅 visible；父按 `sort_order,id`，隐藏父连子一起剔除。
- 校验（422 detail 中文）：type ∈ {link,category}；link 非外链 path 必填且 `/` 开头；is_external 时 path 必须 http(s):// 开头；category 必须 parent_id=None 且忽略 path；parent 必须存在、是顶级、且非 category；更新设 parent_id 时自身若有子级拒绝（防三级）；parent_id 不得为自身。
- DELETE：连带删除直接子项。

- [ ] Step1 写失败测试 `test_menus.py`：公开树含固定首页且表空回退默认；创建 link/category/子项；隐藏父+显示子 → 公开不可见；三层/外链非法/category 带父/外链缺 http → 422；删除父连带子；更新 version 无关。
- [ ] Step2 `uv run pytest tests/test_menus.py -v` 确认失败。
- [ ] Step3 实现模型+schemas+crud+menus.py 端点+router 注册；生成 alembic 迁移（三表一次建），`uv run alembic upgrade head` 通过。
- [ ] Step4 `uv run pytest -v` 全绿；`uv run ruff check app && uv run ruff format app`。
- [ ] Step5 检查点：`git status` 复核改动范围。

### Task A2: 旧 site_menus JSON 启动迁移

**Files:**
- Modify: `backend/app/seed.py`（`DEFAULT_SITE_CONFIG` 移除 `site_menus`；新增 `_migrate_menus(db)`，在 `seed_default_data` 末尾调用）
- Test: `backend/tests/test_menus.py`（追加）

**Interfaces:**
- Consumes: MenuItem（A1）。Produces: 迁移语义 —— `menu_items` 表为空且配置 `site_menus` 值可解析为非空数组才迁移；元素 `{label,path,type?,children?}`：type=='category'→category 顶级项，其余 link；children 仅取一层；解析失败/形状异常 → `logger.warning` 跳过。幂等（表非空即返回）。

- [ ] Step1 失败测试：预置 site_menus JSON → 重启语义（直接调 `seed_default_data`）后菜单入表且二次调用不重复；脏 JSON 不抛错。
- [ ] Step2 确认失败 → Step3 实现 → Step4 全量 pytest+ruff 绿 → Step5 git status。

### Task A3: 前端导航（图标注册表/store/顶栏/MenuManage）+ 文档

**Files:**
- Create: `frontend/src/utils/navIcons.js`（约 30 个 el-icon 名→组件 map + `resolveIcon(name)`，未知名返回 null）
- Create: `frontend/src/utils/config.js`（`isEnabled(v)`、`toNumber(v, fallback)`）
- Modify: `frontend/src/api/site.js`（getMenus/adminGetMenus/adminCreateMenu/adminUpdateMenu/adminDeleteMenu）
- Modify: `frontend/src/stores/config.js`（`menus` ref；`fetchConfig` 内并行 `getMenus()`，失败回退本地 DEFAULT_MENUS；`siteMenus()` 返回 menus.value；`hasCategoryMenu()` 同步；删除 site_menus JSON 解析）
- Modify: `frontend/src/layouts/FrontLayout.vue`（图标 `<component :is>`；is_external → `<a target=_blank rel=noopener>`；子项图标；key 用 id）
- Modify: `frontend/src/components/HomeSidebar.vue`、`NoticeBar.vue`（改用 utils/config.js）
- Create: `frontend/src/views/admin/MenuManage.vue`（el-table 树形 + 对话框表单：label/type(link|external|category)/path/父级下拉(仅顶级非 category)/图标网格选择器(NAV_ICONS)/visible/sort_order；external 即 is_external=true 且 URL 校验）
- Modify: `frontend/src/router/index.js`、`frontend/src/layouts/AdminLayout.vue`（+/admin/menus 路由与"导航菜单"菜单项）
- Modify: `CHANGELOG.md`（0.8.0 起头：导航管理 + 上一会话 el-switch 修复）

- [ ] Step1 实现 utils + api + store（siteMenus 行为测试点：接口失败回退默认）。
- [ ] Step2 FrontLayout 渲染改造；MenuManage 页 + 路由/侧边栏。
- [ ] Step3 `npm run build` 通过；起前后端 curl 冒烟（公开 /menus 形状）。
- [ ] Step4 更新 CHANGELOG.md 条目；git status 检查点。

### Task B1: 社交链接后端

**Files:** Modify: `models/site.py`（表已建，加模型 `SocialLink`）、`models/__init__.py`、`schemas/site.py`、`crud/site.py`、Create: `endpoints/social.py`、Modify: `router.py`；Test: `backend/tests/test_social.py`

**Interfaces:** `SocialLink(id, platform:str, label:str|None, url:str, visible:bool, sort_order:int)`；`GET /social-links` 仅 visible 按 sort_order；`POST|PUT|DELETE /admin/social-links[/{id}]`；校验：platform 非空；url 必须 http(s):// 或 mailto: 开头（422）。

- [ ] Step1 失败测试（CRUD、visible 过滤、url 校验）→ Step2 红 → Step3 实现 → Step4 全绿+ruff → Step5 git status。

### Task B2: profile_links JSON 迁移

Modify: `seed.py`（移除 `profile_links` 默认键；`_migrate_social_links(db)`：表空且旧值可解析时逐项写 platform/url，缺字段项跳过）；Test: `test_social.py` 追加。步骤同 A2。

### Task B3: 前端社交链接（侧边栏 Tab 行编辑 + ProfileCard）

Modify: `api/site.js`、`stores/config.js`（`socialLinks` ref + 并行拉取，失败回退 []；`profileLinks()` 改读 ref）、`views/admin/ConfigManage.vue`（拆 el-tabs：基础信息/外观/侧边栏；侧边栏 Tab = profile_visible/头像/简介 + 社交链接行编辑：平台下拉(预置+custom→显示 label 输入)/URL/visible/排序，"保存配置"成功后统一增量调 CRUD：无 id 新行 POST、有变更 PUT、删除即 DELETE）、`components/ProfileCard.vue`（custom 平台字母= label 首字符大写）。CHANGELOG 追加。

- [ ] 实现 → `npm run build` → curl 冒烟 → CHANGELOG → git status。

### Task C1: 公告后端

**Files:** Modify: `models/site.py`（`Notice(id, title, content, type, enabled, version=1, sort_order, created_at, updated_at)`，datetime default utcnow）、`models/__init__.py`、`schemas/site.py`（`NoticeCreate/NoticeUpdate/NoticeOut(content 可 None)`）、`crud/site.py`、Create: `endpoints/notices.py`、Modify: `router.py`；Test: `backend/tests/test_notices.py`

**Interfaces:**
- 公开 `GET /notices`：enabled 按 type,sort_order,id 排序；banner/dialog 返回 content，page 类型 content=None。`GET /notices/{id}`：含 content；disabled → 404。
- 管理 `GET|POST|PUT|DELETE /admin/notices[/{id}]`；PUT 中 title 或 content 变化 → `version += 1`；type ∈ {banner,dialog,page}（422）。

- [ ] Step1 失败测试（含 version 自增、page 列表无 content、disabled 详情 404、type 校验、多条 dialog 排序取新）→ Step2 红 → Step3 实现 → Step4 全绿+ruff → Step5 git status。

### Task C2: 旧公告三键迁移

Modify: `seed.py`（移除 `notice_text/notice_enabled/notice_version` 默认键；`_migrate_notice(db)`：表空且 notice_text 非空 → 建 banner，enabled=旧 notice_enabled!="false"，version=旧 notice_version 数字否则 1）；Test 追加。步骤同 A2。

### Task C3: 前端公告三形态 + NoticeManage

Modify: `api/site.js`（getNotices/getNotice/admin*Notice）、`stores/config.js`（`notices` ref 并入 fetchConfig）、`components/NoticeBar.vue`（读 store banner 首条，dismiss key `blog_notice_dismissed:{id}` 存 version）、Create: `components/NoticeDialog.vue`（el-dialog+MdPreview 懒加载；取 dialog 类最新一条 updated_at 未关闭者——仅弹一条；关闭写 localStorage）、挂载于 FrontLayout；Create: `views/front/NoticePage.vue` + 路由 `/notice/:id`（name `notice`，MdPreview，加载失败提示回首页）；Create: `views/admin/NoticeManage.vue`（列表+表单：类型单选 banner→textarea/dialog,page→MdEditor via useMdEditor；enabled/排序）+ 路由与侧边栏"公告管理"。CHANGELOG 追加。

- [ ] 实现 → build → curl 冒烟 → CHANGELOG → git status。

### Task D1: 配置键白名单校验

**Files:** Create: `backend/app/core/config_validation.py`；Modify: `endpoints/site.py`（PUT 批量前先逐键校验，任一非法 → 422 且整批不写）；Test: `backend/tests/test_config_validation.py`

**Interfaces:** `check_config_value(key, value) -> str | None`；规则：`site_accent_color` → `^#([0-9a-fA-F]{3}|{6})$`；`homepage_section_count` int 1–8；`sidebar_tag_count` int 1–30；未知键放行。

- [ ] Step1 失败测试（非法颜色、越界数字、批量含一非法 → 422 且合法键未写入）→ Step2 红 → Step3 实现 → Step4 全绿+ruff → Step5 git status。

### Task D2: ConfigManage 收尾 + 全量验证 + 文档

Modify: `views/admin/ConfigManage.vue`（删除 notice 三键表单项——公告已独立管理；外观 Tab 给 accent color/栏目数/标签数加 el-form rules；确认无 json type 残留）、`views/front/About.vue` 无关联则跳过；`README.md`（后台功能清单）、`docs/api.md`（全部新端点）、`docs/architecture.md`（三张新表/迁移/Tab 结构）、`AGENTS.md`（两级限制、固定首页项、navIcons.js 清单、公告三形态、config_validation）。CHANGELOG 收尾（含 0.8.0 汇总）。

- [ ] Step1 收尾改动 → Step2 后端全量 `uv run pytest` + `ruff check` → Step3 `npm run build` → Step4 起服务 curl 冒烟四类端点 → Step5 文档更新 → Step6 git status，向用户汇报并请示提交。

---

## 验收清单（对照 spec §1）

- [ ] 导航：两级/排序/显隐/图标/外链/首页固定/栏目类型/迁移回退
- [ ] 社交链接：增减/显隐/排序/迁移
- [ ] 公告：三形态/多条/版本重推/单页路由/旧公告迁移
- [ ] 配置：Tab 拆分/JSON 字段删除/白名单校验/默认回退
- [ ] 文档：CHANGELOG/api/architecture/README/AGENTS
