from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .ai_layers import AIPlanner, AIRewriter, AIWriter, OpenRouterClient, build_knowledge_base
from .models import Campaign, CampaignChannel, CampaignStatus, EntryStatus, KnowledgeDocument
from .repository import InMemoryRepository
from .schemas import CampaignCreate


class ContentOSService:
    def __init__(self, repo: InMemoryRepository, ai_client: OpenRouterClient | None = None) -> None:
        self.repo = repo
        self.planner = AIPlanner(ai_client)
        self.writer = AIWriter(ai_client)
        self.rewriter = AIRewriter(ai_client)

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
        knowledge_base = build_knowledge_base(documents or self._knowledge_documents(), campaign)
        planned_entries = self.planner.plan(campaign, channels, knowledge_base)
        entries = [self.repo.create_entry(entry) for entry in planned_entries]
        self.repo.update_campaign(replace(campaign, status=CampaignStatus.READY))
        return entries

    def generate_entry(self, entry_id: int, documents: Iterable[str] | None = None):
        entry = self.repo.get_entry(entry_id)
        campaign = self.repo.get_campaign(entry.campaign_id)
        knowledge_base = build_knowledge_base(documents or self._knowledge_documents(), campaign)
        post_text, ai_score = self.writer.write(entry, campaign, knowledge_base)
        return self.repo.update_entry(replace(entry, post_text=post_text, ai_score=ai_score, status=EntryStatus.GENERATED))

    def regenerate_entry(self, entry_id: int, feedback: str, documents: Iterable[str] | None = None):
        entry = self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.REGENERATING, feedback=feedback))
        campaign = self.repo.get_campaign(entry.campaign_id)
        knowledge_base = build_knowledge_base(documents or self._knowledge_documents(), campaign)
        post_text, ai_score = self.rewriter.rewrite(entry, campaign, feedback, knowledge_base)
        return self.repo.update_entry(replace(entry, post_text=post_text, ai_score=ai_score, status=EntryStatus.GENERATED))

    def approve_entry(self, entry_id: int):
        return self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.APPROVED))

    def reject_entry(self, entry_id: int):
        return self.repo.update_entry(replace(self.repo.get_entry(entry_id), status=EntryStatus.REJECTED))


    def add_knowledge_document(self, filename: str, content_type: str, data: bytes) -> KnowledgeDocument:
        text = self._extract_text(filename, data)
        return self.repo.create_document(KnowledgeDocument(filename=filename, content_type=content_type, text=text))

    def _knowledge_documents(self) -> list[str]:
        return [document.text for document in self.repo.list_documents()]

    @staticmethod
    def _extract_text(filename: str, data: bytes) -> str:
        suffix = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
        if suffix in {'txt', 'md', 'csv', 'json', 'html', 'xml'}:
            return data.decode('utf-8', errors='ignore')
        return data.decode('utf-8', errors='ignore') or f'Uploaded file {filename} could not be decoded as text.'
