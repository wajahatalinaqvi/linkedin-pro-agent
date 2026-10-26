"""Prepare one fresh, verified automatic LinkedIn draft from official feeds.

No LinkedIn publication. A user request on today's Pakistan date always wins.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import requests

from post_store import ROOT, LATEST, load_json, create_draft, select_draft
from content_priority import today_local, manual_requests_on_day, automatic_ready_on_day
from free_prepare import generate_post, is_primary_source
from editorial import ranked_candidates, editorial_score
from carousel.art_direction import set_art_direction
from carousel.visual_storytelling import apply_visual_storytelling
from carousel.render_pdf import render_carousel_pdf

FEEDS = [
    ("Shopify", "https://shopify.dev/changelog/feed.xml"),
    ("GitHub developer tools", "https://github.blog/changelog/feed/"),
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("OpenAI Engineering", "https://openai.com/news/engineering/rss.xml"),
]
ATOM = "{http://www.w3.org/2005/Atom}"


def candidates_from_feed(feed_url: str, category: str, now: datetime) -> list[dict]:
    response = requests.get(feed_url, timeout=20, headers={"User-Agent": "LinkedInProAgent/1.0"})
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall(".//item")[:25]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        date = (item.findtext("pubDate") or "").strip()
        try:
            published = parsedate_to_datetime(date).astimezone(timezone.utc)
        except (ValueError, TypeError, IndexError):
            continue
        if not title or not is_primary_source(link) or not now - timedelta(days=3) <= published <= now + timedelta(hours=2):
            continue
        items.append({"topic": title, "source_url": link, "category": category, "published": published})
    for item in root.findall(f"{ATOM}entry")[:25]:
        title = (item.findtext(f"{ATOM}title") or "").strip()
        link_item = next((x for x in item.findall(f"{ATOM}link") if x.get("rel", "alternate") == "alternate"), None)
        link = link_item.get("href", "") if link_item is not None else ""
        date = (item.findtext(f"{ATOM}published") or item.findtext(f"{ATOM}updated") or "").strip()
        try:
            published = datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue
        if title and is_primary_source(link) and now - timedelta(days=3) <= published <= now + timedelta(hours=2):
            items.append({"topic": title, "source_url": link, "category": category, "published": published})
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", default=os.getenv("GITHUB_OUTPUT", ""))
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    day = today_local(now)
    requests_today = manual_requests_on_day(ROOT / "queue/topic_requests", day)
    if requests_today:
        print(f"MANUAL PRIORITY: {len(requests_today)} requested topic(s) on {day}; no automatic post selected.")
        return
    if automatic_ready_on_day(ROOT / "queue/drafts", day):
        print("ALREADY PREPARED: one automatic draft exists for today.")
        return
    if not os.getenv("GEMINI_API_KEY"):
        print("NEEDS CONFIGURATION: GEMINI_API_KEY secret is missing.")
        return

    history = load_json(ROOT / "data/history.json", []) or []
    skipped = load_json(ROOT / "data/skipped.json", []) or []
    drafts = [load_json(p, {}) for p in (ROOT / "queue/drafts").glob("*.json")]
    known_urls = {x.get("source_url", "").rstrip("/") for x in [*history, *skipped, *drafts]}
    known_topics = {re.sub(r"\W+", " ", str(x.get("topic", "")).lower()).strip() for x in [*history, *skipped, *drafts]}
    stories = []
    for category, feed in FEEDS:
        try:
            stories.extend(candidates_from_feed(feed, category, now))
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            print(f"SOURCE UNAVAILABLE ({category}): {type(exc).__name__}")
    stories = ranked_candidates(stories, now)
    if not stories:
        print("NO EDITORIALLY STRONG STORY: available feed entries are too minor for a useful LinkedIn post.")
        return
    print("EDITORIAL CANDIDATES: " + ", ".join(
        f"{s['editorial_score']}/100 {s['topic'][:52]}" for s in stories[:5]))

    for story in stories:
        if story["source_url"].rstrip("/") in known_urls:
            continue
        if re.sub(r"\W+", " ", story["topic"].lower()).strip() in known_topics:
            continue
        fingerprint = hashlib.sha256(story["source_url"].encode()).hexdigest()[:12]
        post_id = f"auto-{day}-{fingerprint}"
        if (ROOT / "queue/drafts" / f"{post_id}.json").exists():
            continue
        try:
            post = generate_post({"topic": story["topic"], "source_url": story["source_url"], "notes": "Write for Shopify app, React/Next.js and AI tooling developers. Prioritize practical implementation implications, thoughtful tradeoffs and source-backed caveats; do not manufacture debate or pretend first-hand experience."}, post_id)
            post["origin"] = "automatic"
            post["priority_score"] = story["editorial_score"]
            post["editorial_review"]["news_selection_score"] = story["editorial_score"]
            post["source_published_at"] = story["published"].isoformat()
            set_art_direction(post["document"]["carousel"], post_id, ROOT / "queue/drafts")
            post["editorial_review"]["visual_treatments"] = apply_visual_storytelling(post["document"]["carousel"])
            pdf = ROOT / "generated" / f"{post_id}.pdf"
            render_carousel_pdf(post["document"]["carousel"], pdf)
            create_draft(post, select=False)
            # Do not displace a currently ready human-requested post.
            current = load_json(LATEST, {}) or {}
            if current.get("status") != "ready" or current.get("origin") == "automatic":
                select_draft(post_id)
            if args.github_output:
                with Path(args.github_output).open("a", encoding="utf-8") as handle:
                    handle.write(f"post_id={post_id}\npdf_path={pdf.relative_to(ROOT).as_posix()}\n")
            print(f"AUTOMATIC DRAFT READY: {post_id} — {story['topic']}. NOT PUBLISHED.")
            return
        except (ValueError, requests.RequestException) as exc:
            print(f"SKIPPED CANDIDATE: {story['topic']}: {str(exc)[:160]}")
    print("NO VERIFIED NEW STORY: no automatic draft generated. No filler was created.")


if __name__ == "__main__":
    main()
