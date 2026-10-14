"""应用配置，统一从环境变量加载。

所有配置项都以 ``BLOG_`` 前缀从环境读取（例如 ``BLOG_SECRET_KEY``），并支持
从 backend/.env 文件加载。集中在此处取值可避免各模块各自散落魔法配置，
并方便通过 ``@lru_cache`` 缓存单例 Settings。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
UPLOAD_DIR = BASE_DIR / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BLOG_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "个人博客"
    debug: bool = True

    secret_key: str = "change-me-to-a-random-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # .env 中可覆盖为相对路径 sqlite+aiosqlite:///./data/blog.db，启动时会被
    # database.py 的 _resolve_sqlite_url 重写为 backend/ 下的绝对路径。
    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'blog.db'}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5

    init_admin_username: str = "admin"
    init_admin_password: str = "admin123"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
