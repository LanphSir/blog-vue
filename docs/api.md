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
| GET | `/friends` | 友链列表 |
| GET | `/categories` | 分类列表（含文章数与 color/parent_id） |
| GET | `/categories/tree` | 分类树（post_count 聚合子分类） |
| GET | `/tags` | 标签列表（含文章数与 color） |
| GET | `/posts` | 文章分页列表 |
| GET | `/posts/{slug}` | 文章详情（浏览量 +1） |
| GET | `/posts/{slug}/neighbors` | 文章上一篇/下一篇 |

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
| POST | `/admin/friends` | 创建友链 |
| PUT | `/admin/friends/{id}` | 更新友链 |
| DELETE | `/admin/friends/{id}` | 删除友链 |
| GET | `/admin/banners` | 轮播图管理列表（含禁用） |
| POST | `/admin/banners` | 创建轮播图 |
| PUT | `/admin/banners/{id}` | 更新轮播图 |
| DELETE | `/admin/banners/{id}` | 删除轮播图 |
| POST | `/admin/upload` | 上传图片（封面/轮播图），返回 `/uploads/...` 路径 |

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