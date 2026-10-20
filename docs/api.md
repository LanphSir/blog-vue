# API 接口规范

- 基础路径：`/api/v1`
- 认证方式：`Authorization: Bearer <token>`（仅管理端接口需要）
- 响应统一为 `{ "code": number, "message": string, "data": any }`

## 公开接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/auth/me` | 当前登录用户（需 token） |
| GET | `/site/config` | 站点配置列表 |
| GET | `/site/stats` | 站点统计（文章/分类/标签数、总阅读量、运行天数） |
| GET | `/banners` | 轮播图列表（仅启用） |
| GET | `/friends` | 友链列表（公开，仅 `visible=true`；含 `icon` 图标 URL，可空） |
| GET | `/categories` | 分类列表（含文章数与 color/parent_id） |
| GET | `/categories/tree` | 分类树（post_count 聚合子分类） |
| GET | `/tags` | 标签列表（含文章数与 color） |
| GET | `/posts` | 文章分页列表 |
| GET | `/posts/{slug}` | 文章详情（浏览量 +1；`?count_view=false` 跳过计数） |
| GET | `/posts/archive` | 归档列表：仅已发布，按年/月倒序分组 `[{year, month, posts:[{id, slug, title, published_at}]}]` |
| GET | `/posts/{slug}/neighbors` | 文章上一篇/下一篇 |
| GET | `/menus` | 导航菜单树（两级；首位固定拼接“首页”项；仅 visible，隐藏父连子剔除；表空回退默认菜单；默认菜单首次启动种入表内可后台管理，标记 `menus_seeded` 防重复回填） |
| GET | `/social-links` | 社交链接{id, platform, label, url, sort_order}（仅 visible，按排序） |
| GET | `/notices` | 启用公告列表（banner/dialog 含 content；page 的 content 为 null） |
| GET | `/notices/{id}` | 公告详情（含 content；已停用返回 404） |
| GET | `/comments?slug=&page=&page_size=` | 评论线程（公开）：顶级评论分页，每项内嵌前 3 条回复 + `reply_count`；仅 approved 未删，被删楼有存活回复时以 `content="该评论已被删除"`、`deleted=true` 占位 |
| GET | `/comments/count?slug=` | 评论总数（公开；口径=approved 未删含回复；文章关评论返回 0） |
| GET | `/comments/{id}/replies?page=&page_size=` | 楼中全部回复分页（公开） |
| POST | `/comments` | 发表评论/回复（公开）：`{post_slug, content, nickname, email?, parent_id?, captcha_id, captcha_code}`；captcha_id 非空才校验验证码；IP 限流 30s/条、20/天（超限 429）；审核开关 `site_comment_audit` 决定初始 status |
| GET | `/feed.xml` | RSS 2.0 订阅（最新 20 篇；纯 XML 非信封；同路径另挂 `/api/v1/feed.xml` 供开发代理/nginx 转发） |

### 文章列表参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| page | number | 页码，默认 1 |
| page_size | number | 每页条数，默认 10，最大 50 |
| category_id | number | 按分类筛选（父分类自动包含子分类） |
| tag_id | number | 按标签筛选 |
| keyword | string | 按标题模糊搜索 |

## 认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/login` | 登录，body `{username, password}`，返回 `{access_token, token_type}` |

## 管理接口（需 JWT）

> 列表批量操作（0.13.0）不新增 bulk 端点：前端逐条循环调用下表中的单条接口（PUT/DELETE 等），语义与单条完全一致。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/admin/posts` | 文章管理列表（含草稿，支持 status/keyword 筛选） |
| GET | `/admin/posts/{id}` | 文章管理详情 |
| POST | `/admin/posts` | 创建文章 |
| PUT | `/admin/posts/{id}` | 更新文章 |
| DELETE | `/admin/posts/{id}` | 删除文章 |
| POST | `/admin/categories` | 创建分类 |
| PUT | `/admin/categories/{id}` | 更新分类 |
| DELETE | `/admin/categories/{id}` | 删除分类 |
| PUT | `/admin/site/config` | 批量更新站点配置，body 为 `[{key, value}]` |

> 配置枚举：`site_background` ∈ none/grid/aurora/dots/topo/geek/line；`site_loading` ∈ none/spinner/progress/bar（页面加载动画，0.14.0）；`site_comment_audit` ∈ "true"/"false"（评论先审后发开关，0.16.0）。
| GET | `/admin/friends` | 友链管理列表（含隐藏项） |
| POST | `/admin/friends` | 创建友链（name/url 必填，可选 description/icon/visible/sort_order） |
| PUT | `/admin/friends/{id}` | 更新友链 |
| DELETE | `/admin/friends/{id}` | 删除友链 |
| GET | `/admin/banners` | 轮播图管理列表（含禁用） |
| POST | `/admin/banners` | 创建轮播图 |
| PUT | `/admin/banners/{id}` | 更新轮播图 |
| DELETE | `/admin/banners/{id}` | 删除轮播图 |
| POST | `/admin/upload` | 上传图片（multipart `file`；jpg/png/gif/webp/svg，≤5MB；magic-bytes 文件头校验，伪装扩展名 400）。按 `uploads/年/月/日/` 归档，文件名=`时间戳_哈希前8位`，自动登记媒体库，返回 URL |
| GET | `/admin/media` | 媒体库分页列表（`page`/`page_size`，返回 items/total/page/page_size；`dir=年/月[/日]` 前缀过滤，`dir=root` 筛根目录旧文件；`deleted=true` 只看回收站，默认排除已删） |
| GET | `/admin/media/folders` | 各存储目录文件数聚合（`[{dir, count}]`，dir=`年/月/日` 或 `root`），供前端目录树 |
| DELETE | `/admin/media/{id}` | 删除图片=软删移入回收站（文件保留、引用不失效） |
| POST | `/admin/media/{id}/restore` | 从回收站恢复（磁盘文件已丢失返回 409） |
| DELETE | `/admin/media/{id}/permanent` | 彻底删除：物理删文件与记录；默认引用保护（被引用 409），`?force=true` 强删 |
| GET | `/admin/menus` | 菜单管理列表（平铺，含隐藏） |
| POST | `/admin/menus` | 创建菜单（校验：两级上限；link 路径须 `/` 开头；外链须 http(s)；category 必须顶级） |
| PUT | `/admin/menus/{id}` | 更新菜单（删除父项会连带删除子项） |
| DELETE | `/admin/menus/{id}` | 删除菜单（连带子项） |
| GET | `/admin/social-links` | 社交链接管理列表（含隐藏） |
| POST | `/admin/social-links` | 创建社交链接（url 须 http(s):// 或 mailto:；可选 icon_url 自定义图标、color 徽章色，非 #hex 422） |
| PUT | `/admin/social-links/{id}` | 更新社交链接 |
| DELETE | `/admin/social-links/{id}` | 删除社交链接 |
| GET | `/admin/notices` | 公告管理列表（含停用与全文） |
| POST | `/admin/notices` | 创建公告（type: banner/dialog/page） |
| PUT | `/admin/notices/{id}` | 更新公告（title/content 变化自动 version+1） |
| DELETE | `/admin/notices/{id}` | 删除公告 |
| GET | `/admin/comments` | 评论管理列表（`status`/`post_id`/`keyword` 筛选，`deleted=true` 回收站；返回 post_title/post_slug 便于跳转） |
| GET | `/admin/comments/pending-count` | 待审评论数（侧栏红点） |
| POST | `/admin/comments/{id}/approve` | 通过（pending/hidden → approved；已删 409） |
| POST | `/admin/comments/{id}/hide` | 隐藏（→ hidden，数据保留可恢复；已删 409） |
| DELETE | `/admin/comments/{id}` | 删除=软删 is_deleted（前台若有存活回复显示占位） |
| POST | `/admin/comments/{id}/restore` | 从回收站恢复（回原 status） |

> 配置键白名单校验：`PUT /admin/site/config` 对 `site_accent_color`（#RGB/#RRGGBB）、`sidebar_tag_count`（1-30）校验，任一非法整批 422 且不写入；未知键放行。

## 文章对象字段

```json
{
  "id": 1,
  "title": "标题",
  "slug": "url-alias",
  "cover_image": null,
  "summary": "摘要",
  "content": "Markdown 正文（仅详情接口返回）",
  "status": "published | draft",
  "view_count": 100,
  "is_top": false,
  "is_featured": false,
  "sort_weight": 0,
  "author": "站长",
  "comments_enabled": true,
  "category_id": 1,
  "tags": [{ "id": 1, "name": "Vue", "slug": "vue", "color": "#16A34A" }],
  "created_at": "2026-09-13T00:00:00",
  "updated_at": "2026-09-13T00:00:00",
  "published_at": "2026-09-13T00:00:00"
}
```

> 文章列表按 `置顶 → sort_weight → published_at` 倒序；分类/标签含 `visible` 与 `sort_order` 字段。

## 分页响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 10
  }
}
```