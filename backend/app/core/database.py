"""Async engine, session factory and declarative base."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import BASE_DIR, DATA_DIR, settings


def _resolve_sqlite_url(url: str) -> str:
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
