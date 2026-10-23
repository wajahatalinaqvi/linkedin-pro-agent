"""Rank official news for *reader relevance*, not promised viral reach.

Heuristics only: source verification still belongs to Gemini URL context
and human review. An eligible story may still be rejected by the writing gate.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

IMPACT = (
    "breaking", "security", "vulnerability", "deprecated", "deprecation",
    "sunset", "removed", "migration", "migrate", "required", "requirement",
    "checkout", "payments", "billing", "pricing", "permission", "privacy",
    "automation", "agents", "agent", "ai", "model", "webhook", "cart",
    "storefront", "search", "inventory", "orders", "authentication",
)
PRACTICAL = (
    "developer", "api", "sdk", "app", "tool", "feature", "shopify",
    "github", "workflow", "store", "merchant", "retail", "commerce",
    "integration", "deploy", "release", "location", "customer",
)
CHANGE = (
    "new", "now", "launch", "launched", "introduc", "support", "enable",
    "add", "available", "update", "improve", "change", "discover",
    "simplif", "expand", "release", "faster", "limit", "replace",
)
LOW_VALUE = (
    "typo", "documentation correction", "minor fix", "minor update",
    "chore", "routine maintenance", "formatting", "bugfix",
)
MINIMUM_EDITORIAL_SCORE = 56


def _has(text: str, word: str) -> bool:
    if word.endswith(("uc", "if")):
        return word in text
    return bool(re.search(r"(?<![a-z])" + re.escape(word) + r"[a-z]*(?![a-z])", text))


def editorial_score(story: dict, now: datetime) -> int:
    """Transparent 0-100 ordering based on recency, change, and niche relevance."""
    title = str(story.get("topic") or "").lower()
    category = str(story.get("category") or "").lower()
    published = story.get("published")
    freshness = 0
    if isinstance(published, datetime):
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age_hours = max(0, (now - published).total_seconds() / 3600)
        freshness = 20 if age_hours <= 24 else 14 if age_hours <= 48 else 8 if age_hours <= 72 else 0
    impact = sum(_has(title, word) for word in IMPACT)
    practical = sum(_has(title, word) for word in PRACTICAL)
    change = sum(_has(title, word) for word in CHANGE)
    score = (12 + freshness + min(30, impact * 12)
             + min(18, practical * 6) + min(12, change * 6)
             + (6 if "shopify" in category or "github" in category else 0))
    if any(bad in title for bad in LOW_VALUE):
        score -= 30
    return max(0, min(100, score))


def ranked_candidates(stories: list[dict], now: datetime, *, minimum: int = MINIMUM_EDITORIAL_SCORE) -> list[dict]:
    eligible = []
    for item in stories:
        result = dict(item)
        result["editorial_score"] = editorial_score(item, now)
        if result["editorial_score"] >= minimum:
            eligible.append(result)
    return sorted(
        eligible,
        key=lambda story: (story["editorial_score"], story["published"].timestamp()),
        reverse=True,
    )
