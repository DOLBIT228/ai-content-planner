from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

import certifi
from dotenv import load_dotenv

from .models import Campaign, CampaignChannel, ContentEntry, ContentFormat, ContentGoal, EntryStatus

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_MODEL = "openai/gpt-4.1-mini"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_BRIEF = "Use premium luxury marketing tone"


def build_knowledge_base(documents: Iterable[str] | None, campaign: Campaign) -> str:
    parts = [doc.strip() for doc in documents or [] if doc and doc.strip()]
    parts.append((campaign.brief or DEFAULT_BRIEF).strip())
    return "\n\n---\n\n".join(parts)


class AIConfigurationError(RuntimeError):
    pass


class AIResponseError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "AI Content Planner")

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        if not self.api_key:
            raise AIConfigurationError("OPENROUTER_API_KEY is required to generate campaigns with OpenRouter.")
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }
        request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.app_name,
            },
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            with urllib.request.urlopen(request, timeout=90, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise AIResponseError(f"OpenRouter returned {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AIResponseError(f"OpenRouter request failed: {exc}") from exc
        try:
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIResponseError("OpenRouter returned an invalid JSON response") from exc


class AIPlanner:
    """Creates a dated, ready-to-review content plan with final content text."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()

    def plan(self, campaign: Campaign, channels: list[CampaignChannel], knowledge_base: str) -> list[ContentEntry]:
        total_needed = sum(channel.total_entries for channel in channels)
        if total_needed == 0:
            return []
        response = self.client.complete_json(self._system_prompt(), self._user_prompt(campaign, channels, knowledge_base))
        items = response.get("entries", [])
        if not isinstance(items, list):
            raise AIResponseError("AI response must contain an entries array")
        return [self._entry_from_item(item, campaign, channels, index) for index, item in enumerate(items[:total_needed])]

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a senior content strategist for Ukrainian marketers. Return only valid JSON. "
            "Create exact campaign content units that are ready for marketer review."
        )

    @staticmethod
    def _user_prompt(campaign: Campaign, channels: list[CampaignChannel], knowledge_base: str) -> str:
        channel_payload = [
            {
                "id": channel.id,
                "channel_name": channel.channel_name,
                "formats": {"Post": channel.post_count, "Carousel": channel.carousel_count, "Reel": channel.reel_count, "Stories": channel.stories_count},
            }
            for channel in channels
        ]
        return json.dumps({
            "task": "Generate a content calendar. Return JSON with key entries. Each entry needs channel_id, publish_date YYYY-MM-DD, format, topic, goal (Sales/Image/Engagement), angle, short_description, post_text.",
            "campaign": {"title": campaign.title, "brief": campaign.brief, "start_date": campaign.start_date.isoformat(), "end_date": campaign.end_date.isoformat(), "sales_percentage": campaign.sales_percentage, "image_percentage": campaign.image_percentage},
            "channels": channel_payload,
            "knowledge_base": knowledge_base[:18000],
        }, ensure_ascii=False)

    def _entry_from_item(self, item: dict[str, Any], campaign: Campaign, channels: list[CampaignChannel], index: int) -> ContentEntry:
        channel = next((ch for ch in channels if ch.id == int(item.get("channel_id", 0) or 0)), channels[0])
        return ContentEntry(
            campaign_id=campaign.id,
            channel_id=channel.id,
            publish_date=self._parse_date(str(item.get("publish_date", "")), campaign, index),
            format=self._parse_format(str(item.get("format", "Post"))),
            topic=str(item.get("topic") or f"{channel.channel_name} content #{index + 1}"),
            short_description=str(item.get("short_description") or "AI-generated campaign content unit."),
            goal=self._parse_goal(str(item.get("goal", "Engagement"))),
            angle=str(item.get("angle") or "Brand-relevant content angle"),
            status=EntryStatus.GENERATED,
            post_text=str(item.get("post_text") or ""),
            ai_score=0.9,
        )

    @staticmethod
    def _parse_date(value: str, campaign: Campaign, index: int) -> date:
        try:
            parsed = date.fromisoformat(value)
            if campaign.start_date <= parsed <= campaign.end_date:
                return parsed
        except ValueError:
            pass
        days = max((campaign.end_date - campaign.start_date).days + 1, 1)
        return campaign.start_date + timedelta(days=index % days)

    @staticmethod
    def _parse_format(value: str) -> ContentFormat:
        normalized = value.lower()
        for fmt in ContentFormat:
            if fmt.value.lower() == normalized:
                return fmt
        return ContentFormat.POST

    @staticmethod
    def _parse_goal(value: str) -> ContentGoal:
        normalized = value.lower()
        for goal in ContentGoal:
            if goal.value.lower() == normalized:
                return goal
        return ContentGoal.ENGAGEMENT


class AIWriter:
    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()

    def write(self, entry: ContentEntry, campaign: Campaign, knowledge_base: str) -> tuple[str, float]:
        response = self.client.complete_json("Return only JSON.", json.dumps({"task": "Write final post_text for this content entry", "campaign": campaign.title, "entry": entry.post_text or entry.short_description, "knowledge_base": knowledge_base[:12000]}, ensure_ascii=False))
        return str(response.get("post_text", entry.post_text or "")), 0.92


class AIRewriter:
    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()

    def rewrite(self, entry: ContentEntry, campaign: Campaign, feedback: str, knowledge_base: str) -> tuple[str, float]:
        response = self.client.complete_json("Return only JSON.", json.dumps({"task": "Rewrite post_text using feedback", "feedback": feedback, "current_text": entry.post_text, "campaign": campaign.title, "knowledge_base": knowledge_base[:12000]}, ensure_ascii=False))
        return str(response.get("post_text", entry.post_text or "")), 0.95


class DeterministicAIClient:
    """Test-only client that mimics OpenRouter JSON without network calls."""

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        payload = json.loads(user)
        if payload.get("task", "").startswith("Generate"):
            campaign = payload["campaign"]
            channels = payload["channels"]
            entries: list[dict[str, Any]] = []
            total = sum(sum(channel["formats"].values()) for channel in channels)
            sales_quota = round(total * campaign["sales_percentage"] / 100)
            image_quota = round(total * campaign["image_percentage"] / 100)
            dates = self._dates(campaign["start_date"], campaign["end_date"])
            index = 0
            for channel in channels:
                for fmt, count in channel["formats"].items():
                    for _ in range(count):
                        goal = "Sales" if index < sales_quota else "Image" if index < sales_quota + image_quota else "Engagement"
                        entries.append({"channel_id": channel["id"], "publish_date": dates[index % len(dates)], "format": fmt, "topic": f"{channel['channel_name']} {fmt} idea #{index + 1}", "goal": goal, "angle": f"{goal} angle for {fmt}", "short_description": f"Strategic {goal.lower()} concept for {campaign['title']}", "post_text": f"{campaign.get('brief') or DEFAULT_BRIEF}\nContent for {channel['channel_name']} {fmt}."})
                        index += 1
            return {"entries": entries}
        if "Rewrite" in payload.get("task", ""):
            return {"post_text": f"{payload.get('current_text', '')}\nRevision applied: {payload.get('feedback', '')}"}
        return {"post_text": f"Generated content: {payload.get('entry', '')}"}

    @staticmethod
    def _dates(start: str, end: str) -> list[str]:
        start_date = date.fromisoformat(start); end_date = date.fromisoformat(end)
        return [(start_date + timedelta(days=i)).isoformat() for i in range((end_date - start_date).days + 1)]
