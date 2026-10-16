"""媒体库模型：MediaAssetOut 由 ORM 实例序列化，供媒体库列表/详情展示。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaAssetOut(BaseModel):
    id: int
    name: str
    stored_name: str
    rel_path: str
    url: str
    ext: str
    mime: str | None
    size: int
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
