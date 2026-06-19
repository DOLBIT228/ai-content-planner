from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


@dataclass(slots=True)
class ChannelCreate:
    channel_name: str
    post_count: int = 0
    carousel_count: int = 0
    reel_count: int = 0
    stories_count: int = 0

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CampaignCreate:
    title: str
    start_date: date
    end_date: date
    sales_percentage: int
    image_percentage: int
    brief: Optional[str] = None
    channels: list[ChannelCreate] = field(default_factory=list)


@dataclass(slots=True)
class RegenerateRequest:
    feedback: str


def serialize(value: Any) -> Any:
    if is_dataclass(value):
        return serialize(asdict(value))
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
