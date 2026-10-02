from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=100)
    sort_order: int = 0
    color: str | None = None
    parent_id: int | None = None
    visible: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    color: str | None = None
    parent_id: int | None = None
    visible: bool | None = None


class CategoryOut(CategoryBase):
    id: int
    post_count: int = 0

    model_config = {"from_attributes": True}


class CategoryTreeOut(CategoryOut):
    children: list["CategoryTreeOut"] = []


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=100)
    color: str | None = None
    visible: bool = True
    sort_order: int = 0


class TagUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    color: str | None = None
    visible: bool | None = None
    sort_order: int | None = None


class TagOut(BaseModel):
    id: int
    name: str
    slug: str
    color: str | None = None
    visible: bool = True
    sort_order: int = 0
    post_count: int = 0

    model_config = {"from_attributes": True}
