"""API v1 路由汇总。

将各功能子路由按前缀与标签统一挂载到 api_router 上，最终由 main.py 以 /api/v1
前缀挂载。posts 等子路由因内部已含 /admin/ 前缀，这里用空前缀平铺挂载。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    categories,
    comments,
    menus,
    notices,
    posts,
    site,
    social,
    uploads,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="", tags=["posts"])
api_router.include_router(categories.router, prefix="", tags=["categories"])
api_router.include_router(comments.router, prefix="", tags=["comments"])
api_router.include_router(site.router, prefix="", tags=["site"])
api_router.include_router(menus.router, prefix="", tags=["menus"])
api_router.include_router(social.router, prefix="", tags=["social"])
api_router.include_router(notices.router, prefix="", tags=["notices"])
api_router.include_router(uploads.router, prefix="", tags=["uploads"])
