"""认证相关的请求/响应模型。

LoginRequest 的 captcha_id/captcha_code 用于验证码校验（为空则后端跳过校验）；
TokenResponse 承载登录签发的 JWT；UserOut 为公开的用户信息。
"""

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str = ""
    captcha_code: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
