"""Test fixtures: isolated in-memory database per test."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.site import SiteConfig
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def _isolated_upload_dir(tmp_path_factory):
    settings.upload_dir = str(tmp_path_factory.mktemp("uploads"))


DEFAULT_TEST_CONFIG = {
    "site_name": "测试博客",
    "site_description": "测试描述",
    "footer_text": "Powered by test",
}


@pytest.fixture()
async def db_session():
    engine = create_async_engine(TEST_DB_URL, poolclass=StaticPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        session.add(User(username="admin", password_hash=hash_password("admin123")))
        for key, value in DEFAULT_TEST_CONFIG.items():
            session.add(SiteConfig(key=key, value=value))
        await session.commit()

    yield factory
    await engine.dispose()


@pytest.fixture()
def client(db_session):
    async def override_get_db():
        async with db_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
