from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .ai_layers import AIPlanner, AIRewriter, AIWriter, build_knowledge_base
from .models import Campaign, CampaignChannel, CampaignStatus, EntryStatus
from .repository import InMemoryRepository
from .schemas import CampaignCreate


class ContentOSService:
    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo
        self.planner = AIPlanner()
        self.writer = AIWriter()
        self.rewriter = AIRewriter()

    def create_campaign(self, payload: CampaignCreate) -> Campaign:
        campaign = Campaign(
            title=payload.title,
            start_date=payload.start_date,
            end_date=payload.end_date,
            brief=payload.brief,
            sales_percentage=payload.sales_percentage,
            image_percentage=payload.image_percentage,
        )
        channels = [CampaignChannel(campaign_id=0, **channel.model_dump()) for channel in payload.channels]
        return self.repo.create_campaign(campaign, channels)

    def generate_plan(self, campaign_id: int, documents: Iterable[str] | None = None):
        campaign = self.repo.update_campaign(replace(self.repo.get_campaign(campaign_id), status=CampaignStatus.PROCESSING))
        channels = self.repo.list_channels(campaign_id)
        knowledge_base = build_knowledge_base(documents, campaign)
        planned_entries = self.planner.plan(campaign, channels, knowledge_base)
        entries = [self.repo.create_entry(entry) for entry in planned_entries]
        self.repo.update_campaign(replace(campaign, status=CampaignStatus.READY))
        return entries

    def generate_entry(self, entry_id: int, documents: Iterable[str] | None = None):
        entry = self.repo.get_entry(entry_id)
        campaign = self.repo.get_campaign(entry.campaign_id)
        knowledge_base = build_knowledge_base(documents, campaign)
        post_text, ai_score = self.writer.write(entry, campaign, knowledge_base)
        return self.repo.update_entry(replace(entry, post_text=post_text, ai_score=ai_score, status=EntryStatus.GENERATED))

    def regenerate_entry(self, entry_id: int, feedback: str, documents: Iterable[str] | None = None):
        entry = self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.REGENERATING, feedback=feedback))
        campaign = self.repo.get_campaign(entry.campaign_id)
        knowledge_base = build_knowledge_base(documents, campaign)
        post_text, ai_score = self.rewriter.rewrite(entry, campaign, feedback, knowledge_base)
        return self.repo.update_entry(replace(entry, post_text=post_text, ai_score=ai_score, status=EntryStatus.GENERATED))

    def approve_entry(self, entry_id: int):
        return self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.APPROVED))

    def reject_entry(self, entry_id: int):
        return self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.REJECTED))
