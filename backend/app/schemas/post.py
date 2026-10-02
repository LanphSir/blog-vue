from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.category import CategoryOut, TagOut


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    cover_image: str | None = None
    summary: str | None = None
    content: str = ""
    status: str = "draft"
    is_top: bool = False
    is_featured: bool = False
    sort_weight: int = 0
    author: str | None = None
    category_id: int | None = None
    tag_ids: list[int] = []


class PostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    cover_image: str | None = None
    summary: str | None = None
    content: str | None = None
    status: str | None = None
    is_top: bool | None = None
    is_featured: bool | None = None
    sort_weight: int | None = None
    author: str | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None


class PostOut(BaseModel):
    id: int
    title: str
    slug: str
    cover_image: str | None
    summary: str | None
    status: str
    view_count: int
    is_top: bool
    is_featured: bool
    sort_weight: int
    author: str | None
    category_id: int | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    model_config = {"from_attributes": True}


class PostDetailOut(PostOut):
    content: str
    tags: list[TagOut] = []


class PostListOut(PostOut):
    category: CategoryOut | None = None
    tags: list[TagOut] = []


class PostNeighbor(BaseModel):
    id: int
    title: str
    slug: str

    model_config = {"from_attributes": True}


class PostNeighborsOut(BaseModel):
    previous: PostNeighbor | None = None
    next: PostNeighbor | None = None
