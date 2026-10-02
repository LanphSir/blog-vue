from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, posts, site, uploads

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="", tags=["posts"])
api_router.include_router(categories.router, prefix="", tags=["categories"])
api_router.include_router(site.router, prefix="", tags=["site"])
api_router.include_router(uploads.router, prefix="", tags=["uploads"])
