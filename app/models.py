from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Optional


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    COMPLETED = "completed"


class ContentFormat(StrEnum):
    POST = "Post"
    CAROUSEL = "Carousel"
    REEL = "Reel"
    STORIES = "Stories"


class ContentGoal(StrEnum):
    SALES = "Sales"
    IMAGE = "Image"
    ENGAGEMENT = "Engagement"


class EntryStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATING = "regenerating"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Campaign:
    title: str
    start_date: date
    end_date: date
    sales_percentage: int
    image_percentage: int
    brief: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    id: int = 0
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class CampaignChannel:
    campaign_id: int
    channel_name: str
    post_count: int = 0
    carousel_count: int = 0
    reel_count: int = 0
    stories_count: int = 0
    id: int = 0

    @property
    def total_entries(self) -> int:
        return self.post_count + self.carousel_count + self.reel_count + self.stories_count


@dataclass(slots=True)
class ContentEntry:
    campaign_id: int
    channel_id: int
    publish_date: date
    format: ContentFormat
    topic: str
    short_description: str
    goal: ContentGoal
    angle: str
    status: EntryStatus = EntryStatus.DRAFT
    post_text: Optional[str] = None
    ai_score: Optional[float] = None
    feedback: Optional[str] = None
    id: int = 0
    created_at: datetime = field(default_factory=utcnow)
