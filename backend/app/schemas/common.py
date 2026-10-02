"""Common Pydantic schemas: unified API response envelope and pagination."""

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
