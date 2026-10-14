"""共享 API 依赖：数据库会话与当前用户解析。

``DbDep`` 供所有端点取会话；``CurrentUser`` 则解析 Bearer 令牌、加载对应用户并
做鉴权，未登录或令牌无效统一抛 401。管理员路由通过声明 ``CurrentUser`` 参数
来获得鉴权与当前用户对象。
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.crud import user as user_crud
from app.models.user import User

# auto_error=False：无凭证时由下方手动统一抛 401，便于所有异常走同一响应体
bearer_scheme = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或过期的登录凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exc
    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[settings.algorithm]
        )
    except JWTError:
        raise credentials_exc from None
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exc
    user = await user_crud.get_by_id(db, int(user_id))
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
