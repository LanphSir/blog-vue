"""通用 Pydantic 模型：统一响应信封与分页。

所有接口都返回 {code, message, data} 信封；PageData 承载分页列表；ok/fail 是
构造成功/失败响应的便捷函数，供各端点统一使用。
"""

from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    code: int = 0
    message: str = "success"
    data: T | None = None


class PageData[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


def ok[T](data: T | None = None, message: str = "success") -> ApiResponse[T]:
    return ApiResponse(code=0, message=message, data=data)


def fail(code: int, message: str) -> ApiResponse[None]:
    return ApiResponse(code=code, message=message, data=None)
