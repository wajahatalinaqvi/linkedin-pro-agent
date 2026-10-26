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
# Pick meaningful developer news over routine product/business announcements.
MINIMUM_EDITORIAL_SCORE = 60
CORE_DEVELOPER = (
    "shopify", "react", "next.js", "nextjs", "typescript", "javascript",
    "frontend", "liquid", "graphql", "laravel", "api", "sdk", "webhook",
    "coding agent", "coding agents", "codex", "claude code", "developer",
    "agent tool", "tool calling", "agentic", "mcp", "cursor",
)
AI_ENGINEERING = ("agent", "agents", "model", "inference", "reasoning",
                  "openai", "anthropic", "claude", "gemini", "ai")
PRACTICAL_CHANGES = ("migrat", "deprecat", "security", "vulnerab", "auth",
                     "shipping", "checkout", "deploy", "release",
                     "preview", "app", "commerce", "integration", "rate limit")
DISCUSSION_TERMS = ("permission", "access", "privacy", "security",
                    "open source", "cost", "pricing", "performance",
                    "speed", "automation", "risk", "breaking")
LOW_AUDIENCE_FIT = (
    "quarterly results", "earnings", "funding round", "investor",
    "board of directors", "executive appointment", "office opening",
    "partnership announcement", "customer success story",
    "enterprise alert management", "public monitoring",
)


def _has(text: str, word: str) -> bool:
    if word.endswith(("uc", "if")):
        return word in text
    return bool(re.search(r"(?<![a-z])" + re.escape(word) + r"[a-z]*(?![a-z])", text))


def _matches(text: str, phrases: tuple[str, ...]) -> int:
    return sum(phrase in text for phrase in phrases)


def editorial_score(story: dict, now: datetime) -> int:
    """Practical developer value + novelty + discussion potential, not a viral prediction."""
    title = str(story.get("topic") or "").lower()
    category = str(story.get("category") or "").lower()
    published = story.get("published")
    freshness = 0
    if isinstance(published, datetime):
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age = max(0, (now - published).total_seconds() / 3600)
        freshness = 20 if age <= 24 else 14 if age <= 48 else 8 if age <= 72 else 0

    core = _matches(title, CORE_DEVELOPER)
    ai = _matches(title, AI_ENGINEERING)
    practical = _matches(title, PRACTICAL_CHANGES)
    discussion = _matches(title, DISCUSSION_TERMS)
    change = sum(_has(title, word) for word in CHANGE)

    score = (
        8 + freshness
        + min(28, core * 16)
        + min(16, ai * 8)
        + min(14, practical * 7)
        + min(9, discussion * 5)
        + min(10, change * 5)
        + (7 if category in {"shopify", "openai engineering"} else 0)
    )
    if any(phrase in title for phrase in LOW_AUDIENCE_FIT):
        score -= 38
    if any(phrase in title for phrase in LOW_VALUE):
        score -= 45
    # A generic announcement with no specific engineering connection is not
    # worth forcing into a daily LinkedIn post, even from a prestigious brand.
    if core == 0 and ai == 0:
        score = min(score, 32)
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
