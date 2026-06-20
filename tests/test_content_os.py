from datetime import date
import unittest

from app.ai_layers import DeterministicAIClient
from app.models import EntryStatus
from app.repository import InMemoryRepository
from app.schemas import CampaignCreate, ChannelCreate
from app.services import ContentOSService


class ContentOSTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryRepository()
        self.service = ContentOSService(self.repo, DeterministicAIClient())
        self.campaign = self.service.create_campaign(CampaignCreate(
            title="Luxury launch",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 7),
            brief="Premium skincare for busy founders. Elegant, concise, confident.",
            sales_percentage=50,
            image_percentage=25,
            channels=[ChannelCreate(channel_name="Instagram", post_count=1, carousel_count=1, reel_count=1, stories_count=1)],
        ))

    def test_planning_creates_generated_entries_with_post_text(self):
        entries = self.service.generate_plan(self.campaign.id)
        self.assertEqual(len(entries), 4)
        self.assertTrue(all(entry.status == EntryStatus.GENERATED for entry in entries))
        self.assertTrue(all(entry.post_text for entry in entries))

    def test_generate_then_review_feedback_flow(self):
        entry = self.service.generate_plan(self.campaign.id)[0]
        generated = self.service.generate_entry(entry.id)
        self.assertEqual(generated.status, EntryStatus.GENERATED)
        self.assertIn("Premium skincare", generated.post_text)
        regenerated = self.service.regenerate_entry(entry.id, "make it more premium, less text")
        self.assertEqual(regenerated.status, EntryStatus.GENERATED)
        self.assertIn("make it more premium", regenerated.post_text)
        approved = self.service.approve_entry(entry.id)
        self.assertEqual(approved.status, EntryStatus.APPROVED)

    def test_empty_brief_uses_luxury_fallback(self):
        campaign = self.service.create_campaign(CampaignCreate(
            title="No brief",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
            sales_percentage=0,
            image_percentage=100,
            channels=[ChannelCreate(channel_name="TikTok", reel_count=1)],
        ))
        entry = self.service.generate_plan(campaign.id)[0]
        generated = self.service.generate_entry(entry.id)
        self.assertIn("Use premium luxury marketing tone", generated.post_text)


if __name__ == "__main__":
    unittest.main()
