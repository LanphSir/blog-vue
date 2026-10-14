"""用户 CRUD 操作。

目前仅登录、鉴权与初始管理员创建使用：按用户名查询用于登录校验，按 id 查询
用于 JWT 解析后的当前用户加载，create 供启动时播种管理员账户。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def create(db: AsyncSession, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
