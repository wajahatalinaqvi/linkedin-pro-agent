"""Broad web discovery for LinkedIn Pro Agent.

Find news across multiple search indexes, not just organization RSS feeds.
Discovery is NOT verification: only a direct HTTPS link to an allowlisted
primary-source publisher can enter the writing pipeline. Gemini URL context
must independently verify that source before draft creation.

Default index sources: Bing News RSS and Google News RSS.
Optional full-web index: Brave Web Search API (BRAVE_SEARCH_API_KEY).
Google News often returns opaque Google links, which are deliberately NOT
used as primary sources. Such results remain research leads, not drafts.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urlparse, parse_qs
import re
import xml.etree.ElementTree as ET
import os

import requests

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def is_primary_source(url: str) -> bool:
    """Reuse the same official host allowlist without importing PDF tooling."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    config = json.loads((ROOT / "config/official_sources.json").read_text(encoding="utf-8"))
    hosts = [urlparse(x["url"]).hostname or "" for x in config.get("sources", [])]
    host = parsed.hostname.lower()
    return any(host == h or host.endswith("." + h) for h in hosts)


MAX_AGE = timedelta(days=3)
QUERIES = (
    ("AI & coding agents", "AI coding agents developer tools new release"),
    ("AI developer tools", "OpenAI Codex Anthropic Claude Code Gemini API developers"),
    ("Shopify engineering", "Shopify developers APIs checkout apps update"),
    ("Frontend engineering", "React Next.js TypeScript frontend performance release"),
    ("Agent security", "AI agent tool access sandbox permissions engineering"),
    ("Ecommerce development", "commerce AI developer integration automation API"),
    ("Web development", "Vercel Next.js deployment web developers updates"),
    ("OpenAI & Anthropic", "latest OpenAI Anthropic new models coding developers"),
)
# More focused primary-source queries to find originals without fabricating URLs.
OFFICIAL_SEARCHES = (
    ("OpenAI engineering", "site:openai.com AI agents developers"),
    ("Anthropic engineering", "site:anthropic.com Claude Code developers"),
    ("Shopify engineering", "site:shopify.dev/changelog API developers"),
    ("Frontend engineering", "site:vercel.com/blog Next.js React"),
)
REQUEST_HEADERS = {"User-Agent": "LinkedInProAgent/2.0 (+public-news-discovery)"}
RSS_TIMEOUT = 14


def _date(raw: str) -> datetime | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        result = parsedate_to_datetime(value)
    except (ValueError, TypeError, IndexError):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _recent(published: datetime | None, now: datetime) -> bool:
    return bool(published and now - MAX_AGE <= published <= now + timedelta(hours=2))


def _canonical_bing_url(url: str) -> str:
    """Bing RSS often wraps the real publisher URL inside ?url=."""
    parsed = urlparse(url)
    if parsed.hostname in {"bing.com", "www.bing.com"} and parsed.path.lower().endswith("/apiclick.aspx"):
        url = (parse_qs(parsed.query).get("url") or [""])[0]
    return url


def _source_url(link: str, *, provider: str) -> str:
    """Only real allowlisted official HTTPS URLs, never search-engine wrappers."""
    url = _canonical_bing_url(link) if provider == "bing" else link
    parsed = urlparse(url)
    if not url or parsed.scheme != "https" or parsed.username or parsed.password:
        return ""
    if parsed.hostname in {"news.google.com", "www.google.com", "bing.com", "www.bing.com"}:
        return ""
    return url if is_primary_source(url) else ""


def parse_news_rss(xml: bytes, category: str, provider: str, now: datetime) -> tuple[list[dict], int]:
    root = ET.fromstring(xml)
    results = []
    leads = 0
    for item in root.findall(".//item")[:25]:
        title = re.sub(r"\s+", " ", (item.findtext("title") or "")).strip()
        published = _date(item.findtext("pubDate") or "")
        if not title or not _recent(published, now):
            continue
        link = (item.findtext("link") or "").strip()
        official = _source_url(link, provider=provider)
        if official:
            results.append({
                "topic": title,
                "source_url": official,
                "category": category,
                "published": published,
                "discovered_via": provider + "-news",
            })
        else:
            leads += 1
    return results, leads


def _rss_search(category: str, query: str, provider: str, now: datetime) -> tuple[list[dict], int]:
    if provider == "bing":
        url = "https://www.bing.com/news/search?" + urlencode({"q": query, "format": "rss"})
    else:
        url = "https://news.google.com/rss/search?" + urlencode({
            "q": query + " when:3d", "hl": "en-US", "gl": "US", "ceid": "US:en",
        })
    response = requests.get(url, timeout=RSS_TIMEOUT, headers=REQUEST_HEADERS)
    response.raise_for_status()
    return parse_news_rss(response.content, category, provider, now)


def _brave_date(row: dict, now: datetime) -> datetime | None:
    parsed = _date(row.get("page_age") or row.get("page_fetched") or "")
    if parsed:
        return parsed
    age = str(row.get("age") or "").lower()
    units = {"minute": 60, "hour": 3600, "day": 86400}
    for word, seconds in units.items():
        match = re.search(r"(\d+)\s+" + word + r"s?\s+ago", age)
        if match:
            return now - timedelta(seconds=int(match.group(1)) * seconds)
    return None


def _brave_search(category: str, query: str, now: datetime, key: str) -> tuple[list[dict], int]:
    reply = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": 12, "freshness": "pw", "search_lang": "en"},
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
        timeout=RSS_TIMEOUT,
    )
    reply.raise_for_status()
    output = []
    leads = 0
    for row in reply.json().get("web", {}).get("results", []):
        published = _brave_date(row, now)
        if not _recent(published, now):
            continue
        link = str(row.get("url") or "")
        official = _source_url(link, provider="brave")
        title = re.sub(r"\s+", " ", str(row.get("title") or "")).strip()
        if not title:
            continue
        if official:
            output.append({
                "topic": title, "source_url": official, "category": category,
                "published": published, "discovered_via": "brave-web",
            })
        else:
            leads += 1
    return output, leads


def discover_web_stories(now: datetime) -> tuple[list[dict], dict]:
    """Search across indexes, keeping only verifiable original-source candidates.

    The report makes source outages and unresolved press links visible. It is
    intentionally NOT a claim of exhaustive internet coverage.
    """
    key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    tasks = []
    for category, query in (*QUERIES, *OFFICIAL_SEARCHES):
        tasks.append(("bing", category, query))
    for category, query in QUERIES:
        tasks.append(("google", category, query))
    if key:
        # No unexpected bill: maximum four queries each daily invocation.
        for category, query in QUERIES[:4]:
            tasks.append(("brave", category, query))

    stats = {"queries": len(tasks), "successful_queries": 0,
             "unresolved_leads": 0, "official_candidates": 0,
             "provider_errors": [], "brave_enabled": bool(key)}
    candidates: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for provider, category, query in tasks:
            if provider == "brave":
                future = pool.submit(_brave_search, category, query, now, key)
            else:
                future = pool.submit(_rss_search, category, query, provider, now)
            futures[future] = (provider, category)
        for future in as_completed(futures):
            provider, category = futures[future]
            try:
                matches, unresolved = future.result()
                stats["successful_queries"] += 1
                stats["unresolved_leads"] += unresolved
                for item in matches:
                    link = item["source_url"].split("#", 1)[0].rstrip("/")
                    if link not in candidates or item["published"] > candidates[link]["published"]:
                        candidates[link] = item
            except (requests.RequestException, ET.ParseError, ValueError, KeyError, TypeError) as exc:
                stats["provider_errors"].append(f"{provider}/{category}: {type(exc).__name__}")
    stats["official_candidates"] = len(candidates)
    return list(candidates.values()), stats
