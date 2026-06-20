from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable, List

from .models import Campaign, CampaignChannel, ContentEntry, KnowledgeDocument


class NotFoundError(KeyError):
    pass


class InMemoryRepository:
    """Small repository abstraction; replace with SQL persistence without changing AI layers."""

    def __init__(self) -> None:
        self._campaigns: Dict[int, Campaign] = {}
        self._channels: Dict[int, CampaignChannel] = {}
        self._entries: Dict[int, ContentEntry] = {}
        self._campaign_seq = 1
        self._channel_seq = 1
        self._entry_seq = 1
        self._documents: Dict[int, KnowledgeDocument] = {}
        self._document_seq = 1

    def create_campaign(self, campaign: Campaign, channels: Iterable[CampaignChannel]) -> Campaign:
        campaign = replace(campaign, id=self._campaign_seq)
        self._campaign_seq += 1
        self._campaigns[campaign.id] = campaign
        for channel in channels:
            self.create_channel(replace(channel, campaign_id=campaign.id))
        return campaign

    def list_campaigns(self) -> List[Campaign]:
        return list(self._campaigns.values())

    def get_campaign(self, campaign_id: int) -> Campaign:
        try:
            return self._campaigns[campaign_id]
        except KeyError as exc:
            raise NotFoundError(f"Campaign {campaign_id} not found") from exc

    def update_campaign(self, campaign: Campaign) -> Campaign:
        self.get_campaign(campaign.id)
        self._campaigns[campaign.id] = campaign
        return campaign

    def delete_campaign(self, campaign_id: int) -> None:
        self.get_campaign(campaign_id)
        del self._campaigns[campaign_id]
        for channel_id in [c.id for c in self.list_channels(campaign_id)]:
            del self._channels[channel_id]
        for entry_id in [e.id for e in self.list_entries(campaign_id)]:
            del self._entries[entry_id]

    def create_channel(self, channel: CampaignChannel) -> CampaignChannel:
        self.get_campaign(channel.campaign_id)
        channel = replace(channel, id=self._channel_seq)
        self._channel_seq += 1
        self._channels[channel.id] = channel
        return channel

    def list_channels(self, campaign_id: int) -> List[CampaignChannel]:
        return [c for c in self._channels.values() if c.campaign_id == campaign_id]

    def create_entry(self, entry: ContentEntry) -> ContentEntry:
        self.get_campaign(entry.campaign_id)
        if entry.channel_id not in self._channels:
            raise NotFoundError(f"Channel {entry.channel_id} not found")
        entry = replace(entry, id=self._entry_seq)
        self._entry_seq += 1
        self._entries[entry.id] = entry
        return entry

    def get_entry(self, entry_id: int) -> ContentEntry:
        try:
            return self._entries[entry_id]
        except KeyError as exc:
            raise NotFoundError(f"Content entry {entry_id} not found") from exc

    def list_entries(self, campaign_id: int) -> List[ContentEntry]:
        return [e for e in self._entries.values() if e.campaign_id == campaign_id]

    def update_entry(self, entry: ContentEntry) -> ContentEntry:
        self.get_entry(entry.id)
        self._entries[entry.id] = entry
        return entry

    def delete_entry(self, entry_id: int) -> None:
        self.get_entry(entry_id)
        del self._entries[entry_id]


    def create_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        document = replace(document, id=self._document_seq)
        self._document_seq += 1
        self._documents[document.id] = document
        return document

    def list_documents(self) -> List[KnowledgeDocument]:
        return list(self._documents.values())

    def delete_document(self, document_id: int) -> None:
        if document_id not in self._documents:
            raise NotFoundError(f"Knowledge document {document_id} not found")
        del self._documents[document_id]
