from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from carousel.render_pdf import render_carousel_pdf

ROOT = Path(__file__).resolve().parents[1]
STRATEGY_PATH = ROOT / "config" / "content_strategy.json"
SOURCES_PATH = ROOT / "config" / "official_sources.json"
HISTORY_PATH = ROOT / "data" / "history.json"
BACKLOG_PATH = ROOT / "data" / "backlog.json"
QUEUE_PATH = ROOT / "queue" / "latest.json"
PREVIEW_DIR = ROOT / "generated" / "previews"

SCORE_LIMITS = {
    "significance": 30,
    "freshness": 20,
    "developer_business_impact": 20,
    "novelty": 15,
    "source_quality": 10,
    "profile_relevance": 5,
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_time(value: str, fallback: datetime) -> datetime:
    if not value:
        return fallback
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_url(value: str) -> str:
    parsed = urlparse(str(value or "").strip())
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower(), path=path, fragment="").geturl()


def story_key(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", str(value or "").lower())
    ignored = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
    return "-".join(word for word in words if word not in ignored)


def score_candidate(candidate: dict) -> int:
    scoring = candidate.get("scoring") or {}
    total = 0
    for field, limit in SCORE_LIMITS.items():
        raw = scoring.get(field, 0)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError(f"Candidate {candidate.get('id')!r}: scoring.{field} must be numeric.")
        if not 0 <= raw <= limit:
            raise ValueError(f"Candidate {candidate.get('id')!r}: scoring.{field} must be 0-{limit}.")
        total += int(raw)
    return total


def official_domains(source_config: dict) -> set[str]:
    return {
        urlparse(item["url"]).netloc.lower().removeprefix("www.")
        for item in source_config.get("sources", [])
        if item.get("url")
    }


def validate_candidate(candidate: dict, source_config: dict) -> None:
    for field in ("id", "category", "topic", "summary", "source_url", "published_at"):
        if not str(candidate.get(field, "")).strip():
            raise ValueError(f"Candidate is missing required field: {field}")
    parsed = urlparse(candidate["source_url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Candidate {candidate['id']!r} has an invalid source_url.")
    if candidate.get("source_kind") == "official":
        domain = parsed.netloc.lower().removeprefix("www.")
        if not any(domain == official or domain.endswith("." + official) for official in official_domains(source_config)):
            raise ValueError(f"Candidate {candidate['id']!r} marks an unregistered domain as official: {domain}")
    score_candidate(candidate)


def category_priority(candidate: dict, strategy: dict) -> int:
    category = str(candidate.get("category", "")).lower()
    for item in strategy.get("priorities", []):
        if any(keyword.lower() in category for keyword in item.get("keywords", [])):
            return int(item["rank"])
    return 99


def historical_keys(history: list[dict]) -> tuple[set[str], set[str], set[str]]:
    ids, urls, stories = set(), set(), set()
    for item in history:
        ids.add(str(item.get("id", "")).strip())
        for url in [item.get("source_url"), *(item.get("sources") or [])]:
            if isinstance(url, str) and url.strip():
                urls.add(normalize_url(url))
        stories.add(story_key(item.get("story_key") or item.get("topic")))
    return ids, urls, stories


def is_duplicate(candidate: dict, history: list[dict]) -> bool:
    ids, urls, stories = historical_keys(history)
    candidate_urls = {normalize_url(candidate.get("source_url", ""))}
    candidate_urls.update(normalize_url(url) for url in candidate.get("sources", []) if isinstance(url, str))
    key = story_key(candidate.get("story_key") or candidate.get("topic"))
    return candidate.get("id") in ids or bool(candidate_urls & urls) or (bool(key) and key in stories)


def expire_backlog(backlog: list[dict], now: datetime, strategy: dict) -> list[dict]:
    default_days = int(strategy.get("backlog_max_age_days", 3))
    evergreen_days = int(strategy.get("evergreen_backlog_max_age_days", 30))
    kept = []
    for candidate in backlog:
        age_days = evergreen_days if category_priority(candidate, strategy) == 7 else default_days
        added = parse_time(candidate.get("backlog_added_at") or candidate.get("published_at", ""), now)
        if now - added <= timedelta(days=age_days):
            kept.append(candidate)
    return kept


def choose_format(score: int, candidate: dict) -> str:
    if score >= 90:
        return "document"
    if score >= 75:
        return "image" if candidate.get("image_url") else "document"
    if score >= 60:
        return "image" if candidate.get("image_url") else "text"
    return "skip"


def theme_for(candidate: dict) -> str:
    category = str(candidate.get("category", "")).lower()
    if "anthropic" in category or "claude" in category:
        return "claude"
    if "shopify" in category or "ecommerce" in category:
        return "shopify"
    if "openai" in category or "agent" in category:
        return "openai"
    return "developer"


def build_caption(candidate: dict) -> str:
    if candidate.get("caption"):
        caption = str(candidate["caption"]).strip()
    else:
        hook = str(candidate.get("hook") or candidate["topic"]).strip()
        summary = str(candidate["summary"]).strip()
        angle = str(candidate.get("developer_business_angle") or candidate.get("developer_angle") or "").strip()
        takeaway = str(candidate.get("takeaway") or "Worth watching because execution details matter more than announcement hype.").strip()
        source_label = str(candidate.get("source_label") or urlparse(candidate["source_url"]).netloc).strip()
        parts = [hook, summary]
        if angle:
            parts.append(angle)
        parts.extend([takeaway, f"Source: {source_label}"])
        hashtags = candidate.get("hashtags") or []
        if hashtags:
            parts.append(" ".join(f"#{str(tag).lstrip('#')}" for tag in hashtags[:4]))
        caption = "\n\n".join(parts)
    if len(caption) > 3000:
        raise ValueError(f"Candidate {candidate['id']!r} produced a caption over 3000 characters.")
    return caption


def build_carousel(candidate: dict) -> dict:
    supplied = candidate.get("carousel")
    if supplied:
        carousel = dict(supplied)
        carousel.setdefault("theme", theme_for(candidate))
        carousel.setdefault("topic", candidate["topic"])
        carousel.setdefault("brand", {"name": "WAJAHAT NAQVI", "subtitle": "Shopify · Full-stack · AI"})
        return carousel

    points = candidate.get("key_points") or [candidate["summary"]]
    implications = candidate.get("implications") or [candidate.get("developer_business_angle") or "Assess the practical workflow impact."]
    watch = candidate.get("watch_items") or ["Verify implementation details in the primary documentation."]
    return {
        "theme": theme_for(candidate),
        "topic": candidate["topic"],
        "brand": {"name": "WAJAHAT NAQVI", "subtitle": "Shopify · Full-stack · AI"},
        "slides": [
            {"type": "cover", "eyebrow": f"{candidate['category']} · VERIFIED STORY", "title": candidate["topic"], "subtitle": candidate["summary"], "footer": "A practical 5-slide briefing →"},
            {"type": "feature_grid", "eyebrow": "WHAT CHANGED", "title": "The signal behind the announcement", "features": [{"number": f"{i:02d}", "title": point, "body": "Verified in the primary source."} for i, point in enumerate(points[:4], 1)]},
            {"type": "cards", "eyebrow": "WHY IT MATTERS", "title": "The developer and business impact", "cards": [{"number": f"{i:02d}", "title": item, "body": "Translate the change into a concrete decision."} for i, item in enumerate(implications[:3], 1)]},
            {"type": "timeline", "eyebrow": "WHAT TO DO NEXT", "title": "A measured response beats a rushed one", "events": [{"number": f"{i:02d}", "title": item, "body": "Use the official documentation as the source of truth."} for i, item in enumerate(watch[:4], 1)]},
            {"type": "closing", "eyebrow": "THE TAKEAWAY", "title": candidate.get("takeaway") or "Focus on the workflow change, not the launch noise.", "subtitle": candidate.get("developer_business_angle") or candidate["summary"], "source": f"Source: {candidate.get('source_label') or candidate['source_url']}"},
        ],
    }


def build_post(candidate: dict, score: int, now: datetime) -> dict:
    post_format = choose_format(score, candidate)
    post = {
        "id": candidate["id"], "status": "ready", "category": candidate["category"],
        "priority_score": score, "format": post_format, "topic": candidate["topic"],
        "caption": build_caption(candidate), "source_url": candidate["source_url"],
        "sources": candidate.get("sources") or [candidate["source_url"]],
        "image_url": candidate.get("image_url", ""), "image_alt": candidate.get("image_alt", ""),
        "created_at": now.isoformat(),
    }
    if post_format == "document":
        post["document"] = {
            "title": candidate.get("document_title") or candidate["topic"],
            "renderer": "v3", "carousel": build_carousel(candidate),
        }
    return post


def prepare(candidates: list[dict], now: datetime) -> dict | None:
    strategy = load_json(STRATEGY_PATH, {})
    sources = load_json(SOURCES_PATH, {})
    history = load_json(HISTORY_PATH, [])
    backlog = expire_backlog(load_json(BACKLOG_PATH, []), now, strategy)

    incoming = []
    for candidate in candidates:
        validate_candidate(candidate, sources)
        enriched = dict(candidate)
        enriched["priority_score"] = score_candidate(candidate)
        if enriched["priority_score"] >= int(strategy.get("min_publish_score", 60)) and not is_duplicate(enriched, history):
            incoming.append(enriched)

    combined = {item["id"]: item for item in [*backlog, *incoming] if not is_duplicate(item, history)}
    eligible = list(combined.values())
    eligible.sort(key=lambda item: (-int(item["priority_score"]), category_priority(item, strategy), -parse_time(item["published_at"], now).timestamp()))

    if not eligible:
        save_json(BACKLOG_PATH, [])
        save_json(QUEUE_PATH, {"status": "idle", "reason": "No non-duplicate candidate scored 60 or higher.", "prepared_at": now.isoformat()})
        return None

    selected = eligible[0]
    secondary = []
    for item in eligible[1:]:
        if int(item["priority_score"]) >= int(strategy.get("backlog_min_score", 75)):
            queued = dict(item)
            queued.setdefault("backlog_added_at", now.isoformat())
            secondary.append(queued)
    save_json(BACKLOG_PATH, secondary[: int(strategy.get("backlog_max_items", 12))])

    post = build_post(selected, int(selected["priority_score"]), now)
    if post["format"] == "document":
        preview = PREVIEW_DIR / f"{post['id']}.pdf"
        render_carousel_pdf(post["document"]["carousel"], preview)
        post["document"]["preview_path"] = str(preview.relative_to(ROOT)).replace("\\", "/")
    save_json(QUEUE_PATH, post)
    return post


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare at most one LinkedIn post. This command never publishes.")
    parser.add_argument("--candidates", required=True, help="JSON file containing a list or {candidates: [...]} payload.")
    parser.add_argument("--as-of", help="Optional ISO timestamp for reproducible preparation tests.")
    args = parser.parse_args()

    path = Path(args.candidates)
    if not path.is_absolute():
        path = ROOT / path
    payload = load_json(path, [])
    candidates = payload.get("candidates", []) if isinstance(payload, dict) else payload
    if not isinstance(candidates, list):
        raise ValueError("Candidate input must be a list or an object with a candidates list.")
    now = parse_time(args.as_of or "", datetime.now(timezone.utc))
    post = prepare(candidates, now)
    if post:
        print(f"READY: {post['id']} ({post['priority_score']}/100, {post['format']})")
        if post.get("document", {}).get("preview_path"):
            print(f"PREVIEW: {ROOT / post['document']['preview_path']}")
    else:
        print("IDLE: no eligible non-duplicate story")
    print("STOP: preparation complete; no LinkedIn action was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
