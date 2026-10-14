"""异步引擎、会话工厂与声明式基类。

集中管理数据库连接：提供全局异步 engine、session 工厂与所有 ORM 模型共享的
``Base`` 基类。应用启动建表、各类增删改查都经由这里的会话进行。
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import BASE_DIR, DATA_DIR, settings


def _resolve_sqlite_url(url: str) -> str:
    # .env 里默认是相对路径 sqlite+aiosqlite:///./data/blog.db；若不做重写，路径会
    # 随进程 cwd 变化而漂移。这里将其重写为基于 backend/ 的绝对路径，使数据库
    # 位置与运行目录无关（保证稳定定位、便于 Docker 卷挂载）。
    if url.startswith("sqlite+aiosqlite:///./"):
        rel = url[len("sqlite+aiosqlite:///./") :]
        db_path = BASE_DIR / rel
        return f"sqlite+aiosqlite:///{db_path}"
    return url


DATABASE_URL = _resolve_sqlite_url(settings.database_url)

if DATABASE_URL.startswith("sqlite"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
