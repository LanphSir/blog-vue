"""FastAPI 应用入口。

初始化日志、CORS、请求日志中间件、统一异常处理器与 API 路由。启动时创建表并
写入默认/演示数据（见 seed.py）。所有响应统一走 {code, message, data} 信封。
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.feed import router as feed_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.models import post as post_model  # noqa: F401  (register tables)
from app.models import site as site_model  # noqa: F401
from app.models import user as user_model  # noqa: F401
from app.seed import seed_default_data, seed_demo_data

logger = logging.getLogger("blog")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)
    logger.info("Starting %s (debug=%s)", settings.app_name, settings.debug)
    # StaticFiles(directory=...) 会在导入时因目录不存在而抛错，所以必须在挂载前先建目录
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_data()
    await seed_demo_data()
    logger.info("Database initialized")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="个人博客后端 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "请求参数校验失败", "data": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


app.include_router(api_router, prefix="/api/v1")
# feed 同时挂载在根路径（阅读器直接抓取）与 /api/v1 下（开发/nginx 代理走这里）
app.include_router(feed_router)
app.include_router(feed_router, prefix="/api/v1")
# 挂载前再次确保目录存在（此处为模块级执行，同样满足 StaticFiles 的目录前提）
settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/health", tags=["system"], summary="健康检查")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
