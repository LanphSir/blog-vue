# 开发日志 / 更新记录

本文件记录项目各阶段的功能开发与变更，按时间倒序排列。

## [0.9.0] - 2026-10-10

### 图片上传统一管理（媒体库）

- **存储规则升级**：上传图片按 `uploads/年/月/日/` 三级目录 归档，文件名 `{YYYYMMDDHHMMSS}_{SHA-256前8位}{ext}`（时间戳+内容哈希，杜绝冲突与路径穿越；原文件名保留入库展示）
- **新表 `media_assets`**（迁移 `af5b7e9d2c31`）：登记全部图片（原名/存储名/相对路径/url/扩展名/mime/大小/时间）；首次启动自动**盘点** uploads 目录下既有图片入库（幂等，含旧平铺文件）；迁移对 `create_all` 已建表的库自动跳过
- **安全校验**：扩展名白名单（jpg/jpeg/png/gif/webp/svg）基础上增加 **magic-bytes 文件头嗅探**，伪装扩展名一律 400；空文件拒绝；大小限制沿用 `BLOG_MAX_UPLOAD_SIZE_MB`（上传接口返回结构不变，旧调用零改动兼容）
- **媒体库端点**：`GET /admin/media`（page/page_size 分页，`dir=2026/10` 前缀过滤、`dir=root` 筛根目录散落文件）；`GET /admin/media/folders` 按存储目录聚合计数供层级浏览；`DELETE /admin/media/{id}` 默认带**引用保护**（LIKE 扫描文章内容/封面、轮播图、友链图标、站点配置，命中返回 409 与引用方计数），`?force=true` 强制删除并清理磁盘文件
- **统一 MediaPicker 组件**（分段切换「本地上传 / 媒体库选取」+ 预览/更换/移除）全面替换旧的各写各上传：文章封面、轮播图、友链图标、站点配置的头像与 Logo（后两者原来只能手填 URL）；共享 `MediaLibraryGrid` 缩略图网格（懒加载+分页）
- **MarkdownEditor 新工具「从图库插入」**：弹窗选图后在光标处插入图片 Markdown（编辑器实例 insert API，无实例时追加兜底）；粘贴/工具栏上传自动进媒体库
- Bug 修复：选图弹窗的目录级联此前只能按"年"筛选——子级面板在 `checkStrictly` 下需点箭头才展开（改为 hover 展开），且选中月/日后把整条路径 `/` 拼接当作目录过滤导致查不到数据（改为取最深一级值）
- **媒体库管理页**（侧栏新入口）：**左侧年→月→日目录树（含计数）+ 右侧分页表格**（预览/原名/存储名/所在目录/大小/时间）、上传、复制链接、删除（409 时二次确认可强删）；MediaPicker 弹窗内置目录级联筛选，选图可按层级缩小范围
- 测试：后端 47 用例全绿（新增媒体库 7 用例：哈希命名/假扩展名/未知格式/分页/引用保护删除/盘点幂等；测试期上传目录自动隔离到临时目录）；`npm run build` 通过

## [0.8.1] - 2026-10-10

### 0.8.0 收尾调整：数据归一 / 编辑器统一 / 配置分区 / 导航溢出

- **默认导航入表**：原前端硬编码的默认菜单（文章/标签/友链/关于）改为首次启动种入 `menu_items` 表成为**可管理数据**（`seed.py::_seed_default_menus`，配置标记 `menus_seeded` 保证只种一次，用户删空后重启不再回填；旧 `site_menus` JSON 迁移优先于种子）；"首页"仍由 `GET /menus` 固定拼接不落库；新增 3 个种子用例
- **公告编辑器统一**：`NoticeManage.vue` 弹窗/单页内容编辑器由裸 `MdEditor` 改为复用与文章编辑一致的 `MarkdownEditor.vue`（导入 .md、粘贴上传、字数统计）；横幅公告保持纯文本输入
- **侧边栏配置分区**：站点配置"侧边栏" Tab 由平铺字段重组为三个功能卡片——简介卡片（开关 + 头像/简介/社交链接，关闭自动折叠）、标签云（开关 + 数量）、最近发布（仅开关），带 `el-collapse-transition` 过渡
- **移除死配置 `homepage_section_count`**：该键在首页栏目 Tab 改版后已无任何消费方，从默认配置、白名单校验、后台外观 Tab 中全部移除（数据库残留行无害，保存时透传）
- **前台导航溢出折叠**：窗口过窄放不下全部菜单时，多余项自动收进 `···`（`MoreFilled`）下拉（click 触发，外链新窗口/栏目跳首页/子菜单跳首个子项）；新增 `composables/useNavOverflow.js`：克隆真实导航 DOM 量宽（含图标/下拉箭头/内外宽边距），按项 key 缓存进 localStorage（`blog_nav_item_widths`）避免回访闪烁，`ResizeObserver` 响应窗口变化，字体就绪后重测一次，**首项"首页"永不折叠**
- **导航溢出修复**：全部菜单放得下时不再错误显示 `···` 触发器（原逻辑对可容纳宽度仍强制至少折叠一项）
- **友链管理重做**：内联工具栏表单改为**模态框**新增/编辑（名称/地址/描述/排序/图标全字段可编辑，地址须 http(s)，编辑不再丢失描述与排序字段）；新增 `icon` 字段（迁移 `8a2f1c3d4b5e`），图标经 `/admin/upload` 上传、可更换/移除，管理表格与前台（友链页卡片、页脚）均在名称**前**展示图标
- **友链显示/隐藏**：新增 `visible` 字段（迁移 `9c4e2f6a1d7b`）；`GET /friends` 公开列表仅返回显示中的友链，新端点 `GET /admin/friends` 返回全部；管理表格内开关即时切换
- **顶栏导航居中**：`.nav` 增加 `justify-content: center`
- **页面标题**：新增 `utils/pageTitle.js`，路由 `meta.title` + `afterEach` 统一设置 `document.title = 页面 · 站点名称`（站点名取后台配置，加载后自动刷新当前标题）；文章详情与公告单页加载后使用自身标题；无标题页面仅显示站点名
- 测试：后端 41 用例全绿（新增友链图标 CRUD 与显隐过滤用例）；`npm run build` 通过

## [0.8.0] - 2026-10-09

### 后台配置体系重构 · 一：导航菜单管理

- Bug 修复：站点配置页开关（简介卡片/标签云/最近发布/公告）显示状态不正确——后端布尔配置为字符串 `"true"/"false"`，`el-switch` 默认按布尔严格比较恒显示"关"；改为字符串 `active-value/inactive-value`
- 新表 `menu_items`（Alembic 迁移 `37d8cc4547f9`，同批建 `social_links`/`notices` 供后续任务使用）：两级树形导航，字段含图标名/外链/排序/显隐
- 后端：`GET /menus` 公开树（首位拼接**固定"首页"**项、仅 visible、隐藏父连子剔除、**表空回退默认菜单**）；`/admin/menus` CRUD（校验：两级上限、外链必须 http(s)、栏目类型必须顶级、防自环/防三级）；删除父项连带子项
- 旧 `site_menus` JSON 配置启动时自动迁移入库（解析失败仅告警、幂等）；默认配置键删除
- 前端：新管理页 **导航菜单**（`MenuManage.vue`：树表格 + 对话框：内部/外部/栏目下拉 + 32 个预置 el-icon 图标网格选择器 + 显隐/排序行内直改）
- 顶栏渲染升级：菜单图标（`utils/navIcons.js` 注册表，未知图标名安全降级无图标）、外链新窗口 + 角标、store 改读结构化 `/menus`（接口失败回退内置默认菜单）
- 新增 `utils/config.js` 布尔/数字配置解析 helper，侧边栏显隐与标签云数量逻辑统一走该 helper
- 测试：新增 8 个菜单用例（共 22 个通过）；配置键迁移函数直测

### 后台配置体系重构 · 二：简介卡片社交链接

- 新表 `social_links`：`platform`（8 个预置平台或 `custom`+显示名）/ `url` / `visible` / `sort_order`
- 后端：`GET /social-links` 公开（仅 visible，按排序）；`/admin/social-links` CRUD；URL 必须 `http(s)://` 或 `mailto:`（422）
- 旧 `profile_links` JSON 启动自动迁移（缺字段项跳过、非法 JSON 仅告警、幂等）；默认配置键删除
- 站点配置页改造：拆为 **基础信息 / 外观 / 侧边栏 / 公告** 四个 Tab；侧边栏 Tab 内“社交链接”行编辑（平台下拉 + 自定义显示名 + URL + 显隐开关 + 排序，点“保存配置”统一增删改，本地先校验 URL）
- `ProfileCard.vue` 改读结构化接口（经 config store 并行拉取，接口失败回退空列表）；custom 平台显示自定义名首字；平台元数据抽到 `utils/platforms.js` 三处共用
- 测试：新增 4 个用例（CRUD/显隐过滤/URL 校验/迁移幂等，共 26 个通过）；实机验证旧 JSON 迁移与可见性过滤

### 后台配置体系重构 · 三：多尺寸公告

- 新表 `notices`：多条公告并存，`type` 三档——**小·横幅**（顶部，同类型按排序取第一条）/ **中·弹窗**（Markdown，用户级“不再提示”）/ **大·单页**（`/notice/:id` 独立页面）
- 后端：公开 `GET /notices`（仅启用；单页列表不返回正文防大文本拖累）、`GET /notices/{id}`（停用 404）；管理 CRUD；**title/content 变更自动 version+1**（启停/排序不加）
- 前端：新管理页 **公告管理**（`NoticeManage.vue`：类型单选，横幅纯文本、弹窗/单页走 MdEditor）；`NoticeBar` 改读公告表（关闭记忆升级为按 `公告ID+版本`）；新组件 `NoticeDialog`（最新未读弹窗公告自动弹出一次）；新页面 `NoticePage`（MdPreview 渲染，公告不存在显示空态回首页）
- 旧 `notice_text/notice_enabled/notice_version` 三键启动自动迁移为一条横幅公告（版本号继承，非法则 1，`notice_enabled=false` 映射停用）；默认配置键与配置页公告 Tab 删除
- 测试：新增 6 个用例（三形态规则/版本自增/类型校验/404/迁移幂等，共 32 个通过）；实机验证旧三键迁移与公开列表 content 隐藏

### 后台配置体系重构 · 四：配置校验与收尾

- 后端新增 `core/config_validation.py`：`PUT /admin/site/config` 按白名单校验 `site_accent_color`（#RGB/#RRGGBB）、`homepage_section_count`（1-8）、`sidebar_tag_count`（1-30），**任一非法整批 422 且零写入**；未知键放行保证可扩展
- 配置页保存前同规则预校验并自动跳到出错 Tab
- 全站兜底审计：菜单/社交链接/公告接口失败各自独立回退；`el-switch` 布尔字符串统一处理；未知图标名安全降级
- 文档：`docs/api.md`（14 个新端点+校验规则）、`docs/architecture.md`（3 张新表/迁移/健壮性防线）、README 功能清单、AGENTS.md（两级限制、固定首页项、注册表约定、**文档义务条款**）
- 全量验证：36 个 pytest 通过、ruff 全绿、`npm run build` 通过、实机冒烟（菜单/链接/公告/校验四类端点）正常

## [0.7.0] - 2026-10-06

### 仪表盘修正与文章软删除

- 后台仪表盘 `Dashboard.vue`：
  - 统计数据改用真实 `GET /site/stats`（文章总数/分类数/标签数/总阅读量），此前从"最近 5 篇"误算
  - 新增"刷新"按钮，随时拉取最新数据
- 文章**软删除（回收站）**：
  - `posts` 新增 `deleted_at` 字段（Alembic 迁移 `ddd6a85857d5`）
  - 删除改为软删除：`POST/DELETE /admin/posts/{id}` 置 `deleted_at`，可 `POST /{id}/restore` 恢复，`DELETE /{id}/permanent` 彻底删除
  - `GET /admin/posts?deleted=true` 查看回收站
  - 前台公开列表/详情/上一篇下一篇、分类标签计数、站点统计均排除已删文章
- 后台文章管理 `PostManage.vue`：新增"文章列表/回收站"切换，回收站支持恢复、彻底删除、清空（危险操作二次确认）
- 测试：新增软删除全流程用例，共 14 个全部通过

## [0.6.0] - 2026-10-02

### 编辑器升级：集成 md-editor-v3

- 后台文章编辑器 `MarkdownEditor.vue` 重写为 `md-editor-v3`（`MdEditor`）：
  - **完整工具栏**（不再 `toolbarsExclude`）：加粗/标题/列表/代码/表格、图片裁剪、Mermaid、KaTeX、prettier 格式化、github、catalog、htmlPreview、保存、**内置全屏（页面全屏 + 浏览器全屏）**
  - 全屏改用库内置实现（此前自定义全屏容器无法正确铺满）；`fullscreen` 依赖的 `screenfull` 已本地注册
  - 代码高亮使用本地 `highlight.js/lib/common` 实例（离线可用，体积更小）
  - 注册 `markdown-it-mark`：支持 `==高亮文字==` 语法（编辑器预览与前台文章页均生效，配套 `mark` 主题样式）
  - **粘贴/拖拽/裁剪插图**：`onUploadImg` 接入现有 `POST /admin/upload`
  - `onSave`（Ctrl+S）→ 保存；`onError` 上报扩展加载失败；保留"导入 .md 文件"与字数统计
  - 主题随全站 `themeStore` 切换，预览主题 github、代码主题 atom、语言 zh-CN
- 前台文章页 `PostDetail.vue` 改为 `MdPreview` + `MdCatalog`：
  - 全站渲染统一（markdown-it），内置目录滚动高亮替代手写 TOC，代码块复制使用库内置能力
- 新增 `composables/useMdEditor.js`：懒加载并注册 md-editor-v3 + highlight.js + screenfull 实例，供编辑器与预览复用
- 依赖调整：新增 `md-editor-v3`、`screenfull`、`highlight.js`；移除 `marked`、`useMarkdown.js`
- Vite 分包：`md-editor-v3` 独立 `vendor-md-editor` chunk（仅编辑页/详情页懒加载）
- 全量验证：前端构建通过；后端未改动（pytest/ruff 回归通过）

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