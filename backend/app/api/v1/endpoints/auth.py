"""认证端点：验证码、登录与当前用户。

登录需携带 captcha_id + captcha_code 通过验证码校验；当 captcha_id 为空时跳过
校验（向后兼容测试等场景，见 AGENTS.md）。登录成功签发 JWT，后续鉴权走
Authorization: Bearer。
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbDep
from app.core.captcha import create as captcha_create
from app.core.captcha import verify as captcha_verify
from app.core.captcha_img import generate as captcha_img_generate
from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.schemas.common import ApiResponse, ok

router = APIRouter()


@router.get("/captcha", summary="获取验证码图片")
async def captcha():
    code, img_bytes = captcha_img_generate()
    cid = captcha_create(code)
    return Response(content=img_bytes, media_type="image/png", headers={"X-Captcha-Id": cid})


@router.post("/login", summary="管理员登录")
async def login(payload: LoginRequest, db: DbDep) -> ApiResponse[TokenResponse]:
    if payload.captcha_id and not captcha_verify(payload.captcha_id, payload.captcha_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    user = await user_crud.get_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return ok(TokenResponse(access_token=create_access_token(str(user.id))))


@router.get("/me", summary="当前登录用户")
async def me(current_user: CurrentUser) -> ApiResponse[UserOut]:
    return ok(UserOut.model_validate(current_user))
