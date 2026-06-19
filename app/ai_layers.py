from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Iterable, List

from .models import Campaign, CampaignChannel, CampaignStatus, ContentEntry, ContentFormat, ContentGoal, EntryStatus

DEFAULT_BRIEF = "Use premium luxury marketing tone"


def build_knowledge_base(documents: Iterable[str] | None, campaign: Campaign) -> str:
    parts = [doc.strip() for doc in documents or [] if doc and doc.strip()]
    parts.append((campaign.brief or DEFAULT_BRIEF).strip())
    return "\n\n".join(parts)


class AIPlanner:
    """Strategic layer: creates structured ContentEntry drafts and never writes post_text."""

    def plan(self, campaign: Campaign, channels: list[CampaignChannel], knowledge_base: str) -> list[ContentEntry]:
        entries: list[ContentEntry] = []
        total_needed = sum(channel.total_entries for channel in channels)
        if total_needed == 0:
            return entries

        campaign_days = max((campaign.end_date - campaign.start_date).days + 1, 1)
        sales_quota = round(total_needed * campaign.sales_percentage / 100)
        image_quota = round(total_needed * campaign.image_percentage / 100)

        sequence = 0
        for channel in channels:
            formats = (
                [ContentFormat.POST] * channel.post_count
                + [ContentFormat.CAROUSEL] * channel.carousel_count
                + [ContentFormat.REEL] * channel.reel_count
                + [ContentFormat.STORIES] * channel.stories_count
            )
            for content_format in formats:
                goal = self._goal_for(sequence, sales_quota, image_quota)
                publish_date = campaign.start_date + timedelta(days=sequence % campaign_days)
                entries.append(ContentEntry(
                    campaign_id=campaign.id,
                    channel_id=channel.id,
                    publish_date=publish_date,
                    format=content_format,
                    topic=f"{channel.channel_name} {content_format.value} idea #{sequence + 1}",
                    short_description=self._description(goal, knowledge_base),
                    goal=goal,
                    angle=self._angle(goal, content_format),
                    status=EntryStatus.DRAFT,
                    post_text=None,
                ))
                sequence += 1
        return entries

    @staticmethod
    def _goal_for(index: int, sales_quota: int, image_quota: int) -> ContentGoal:
        if index < sales_quota:
            return ContentGoal.SALES
        if index < sales_quota + image_quota:
            return ContentGoal.IMAGE
        return ContentGoal.ENGAGEMENT

    @staticmethod
    def _description(goal: ContentGoal, knowledge_base: str) -> str:
        context = knowledge_base[:120].replace("\n", " ")
        return f"Strategic {goal.value.lower()} content concept informed by: {context}"

    @staticmethod
    def _angle(goal: ContentGoal, content_format: ContentFormat) -> str:
        return f"{goal.value} angle optimized for {content_format.value}"


class AIWriter:
    """Copywriting layer: turns one approved plan item into post text."""

    def write(self, entry: ContentEntry, campaign: Campaign, knowledge_base: str) -> tuple[str, float]:
        voice = campaign.brief or DEFAULT_BRIEF
        text = (
            f"{entry.topic}\n\n"
            f"Angle: {entry.angle}.\n"
            f"Goal: {entry.goal.value}. Format: {entry.format.value}.\n"
            f"{entry.short_description}\n\n"
            f"Brand voice: {voice}\n"
            f"Context: {knowledge_base[:280]}"
        )
        return text, 0.92


class AIRewriter:
    """Feedback loop layer: improves existing generated text while preserving voice."""

    def rewrite(self, entry: ContentEntry, campaign: Campaign, feedback: str, knowledge_base: str) -> tuple[str, float]:
        base = entry.post_text or ""
        voice = campaign.brief or DEFAULT_BRIEF
        improved = (
            f"{base}\n\n"
            f"Revision applied: {feedback}\n"
            f"Keep voice consistent: {voice}\n"
            f"Reference context: {knowledge_base[:180]}"
        ).strip()
        return improved, 0.95
