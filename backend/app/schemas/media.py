"""Media library schemas."""

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

    model_config = ConfigDict(from_attributes=True)
