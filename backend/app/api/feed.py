"""RSS 2.0 订阅源，挂载在根路径（/api/v1 之外）。

RSS 由手拼 XML 字符串生成，不依赖第三方库（如 feedgen），避免额外依赖；
并通过 ``xml.sax.saxutils.escape`` 对站点名、标题等内容做 XML 转义，防止注入。
该路由会同时挂载在根路径（阅读器直接访问）与 /api/v1 下（Vite/nginx 代理可达）。
"""

from datetime import UTC, datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Request
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import DbDep
from app.crud import post as post_crud
from app.models.site import SiteConfig

router = APIRouter()


def _rfc822(moment: datetime) -> str:
    # RSS pubDate 规范要求 RFC 822 格式且带时区；无时区的本地时间先补 UTC，避免输出非法
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return format_datetime(moment, usegmt=True)


@router.get("/feed.xml", include_in_schema=False)
async def feed(request: Request, db: DbDep) -> Response:
    posts, _ = await post_crud.list_posts(db, page=1, page_size=20, status="published")
    configs = {item.key: item.value for item in (await db.execute(select(SiteConfig))).scalars()}
    base = str(request.base_url).rstrip("/")
    site_name = escape(configs.get("site_name") or "Blog")
    description = escape(configs.get("site_description") or "")
    author = escape(configs.get("site_author") or "")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        f"<title>{site_name}</title>",
        f"<link>{base}/</link>",
        f"<description>{description}</description>",
    ]
    if author:
        parts.append(f"<managingEditor>{author}</managingEditor>")
    for post in posts:
        # category 是懒加载关系，列表查询未随查随取；逐篇刷新该属性才能拿到分类名
        await db.refresh(post, attribute_names=["category"])
        moment = post.published_at or post.created_at
        link = f"{base}/post/{post.slug}"
        parts.append("<item>")
        parts.append(f"<title>{escape(post.title)}</title>")
        parts.append(f"<link>{link}</link>")
        parts.append(f'<guid isPermaLink="true">{link}</guid>')
        if moment is not None:
            parts.append(f"<pubDate>{_rfc822(moment)}</pubDate>")
        if post.category and post.category.name:
            parts.append(f"<category>{escape(post.category.name)}</category>")
        parts.append(f"<description>{escape((post.summary or '')[:500])}</description>")
        parts.append("</item>")
    parts += ["</channel>", "</rss>"]
    return Response("\n".join(parts), media_type="application/rss+xml; charset=utf-8")
