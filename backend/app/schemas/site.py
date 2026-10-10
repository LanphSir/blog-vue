from datetime import datetime

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
    icon: str | None = None
    visible: bool = True
    sort_order: int = 0


class FriendLinkUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    icon: str | None = None
    visible: bool | None = None
    sort_order: int | None = None


class FriendLinkOut(BaseModel):
    id: int
    name: str
    url: str
    description: str | None
    icon: str | None
    visible: bool
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


class MenuItemCreate(BaseModel):
    label: str
    path: str | None = None
    icon: str | None = None
    type: str = "link"
    is_external: bool = False
    parent_id: int | None = None
    sort_order: int = 0
    visible: bool = True


class MenuItemUpdate(BaseModel):
    label: str | None = None
    path: str | None = None
    icon: str | None = None
    type: str | None = None
    is_external: bool | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    visible: bool | None = None


class MenuItemOut(BaseModel):
    id: int
    label: str
    path: str | None
    icon: str | None
    type: str
    is_external: bool
    parent_id: int | None
    sort_order: int
    visible: bool

    model_config = {"from_attributes": True}


class NoticeCreate(BaseModel):
    title: str
    content: str = ""
    type: str = "banner"
    enabled: bool = True
    sort_order: int = 0


class NoticeUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    type: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class NoticeOut(BaseModel):
    id: int
    title: str
    content: str | None
    type: str
    enabled: bool
    version: int
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SocialLinkCreate(BaseModel):
    platform: str
    label: str | None = None
    url: str
    visible: bool = True
    sort_order: int = 0


class SocialLinkUpdate(BaseModel):
    platform: str | None = None
    label: str | None = None
    url: str | None = None
    visible: bool | None = None
    sort_order: int | None = None


class SocialLinkOut(BaseModel):
    id: int
    platform: str
    label: str | None
    url: str
    visible: bool
    sort_order: int

    model_config = {"from_attributes": True}


class MenuNodeOut(BaseModel):
    label: str
    path: str | None
    icon: str | None
    type: str
    is_external: bool
    children: list["MenuNodeOut"] = []
