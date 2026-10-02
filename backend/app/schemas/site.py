from pydantic import BaseModel


class ConfigItem(BaseModel):
    key: str
    value: str


class ConfigOut(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class FriendLinkCreate(BaseModel):
    name: str
    url: str
    description: str | None = None
    sort_order: int = 0


class FriendLinkUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    sort_order: int | None = None


class FriendLinkOut(BaseModel):
    id: int
    name: str
    url: str
    description: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class BannerCreate(BaseModel):
    title: str
    subtitle: str | None = None
    image: str | None = None
    link: str | None = None
    sort_order: int = 0
    enabled: bool = True


class BannerUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    image: str | None = None
    link: str | None = None
    sort_order: int | None = None
    enabled: bool | None = None


class BannerOut(BaseModel):
    id: int
    title: str
    subtitle: str | None
    image: str | None
    link: str | None
    sort_order: int
    enabled: bool

    model_config = {"from_attributes": True}


class SiteStats(BaseModel):
    post_count: int
    category_count: int
    tag_count: int
    total_views: int
    days_since_launch: int
