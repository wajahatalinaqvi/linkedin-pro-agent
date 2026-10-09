"""Free-tier topic -> LinkedIn draft. No LinkedIn calls, publishing or paid APIs.

Uses Gemini URL context on ONE user-supplied official source. A human must review
accuracy and design before using the separate Publish action.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from carousel.render_pdf import render_carousel_pdf
from post_store import ROOT, LATEST, create_draft, draft_path, load_json, save_json

REQUEST_DIR = ROOT / "queue" / "topic_requests"
MODEL = "gemini-2.5-flash"
LAYOUTS = ["cover", "cards", "comparison", "cards", "timeline", "closing"]


def is_primary_source(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    source_config = load_json(ROOT / "config" / "official_sources.json", {})
    hosts = [urlparse(x["url"]).hostname or "" for x in source_config.get("sources", [])]
    host = parsed.hostname.lower()
    return any(host == h or host.endswith("." + h) for h in hosts)


def response_text(payload: dict) -> str:
    for candidate in payload.get("candidates", []):
        text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", []))
        if text.strip():
            return text.strip()
    raise ValueError("Gemini returned no text; do not create an unreviewed post.")


def gemini(prompt: str, *, source_url: str = "") -> dict:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is missing. Create a free Google AI Studio key.")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 6000}}
    if source_url:
        body["tools"] = [{"urlContext": {}}]
    else:
        body["generationConfig"]["responseMimeType"] = "application/json"
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
    reply = requests.post(url, headers={"x-goog-api-key": key}, json=body, timeout=180)
    if not reply.ok:
        raise ValueError(f"Gemini returned HTTP {reply.status_code}. Check free-tier access and quota.")
    return reply.json()


def verified_facts(source: str, topic: str, notes: str) -> str:
    prompt = ("Read this official webpage using URL context: " + source + "\n"
              "Requested topic: " + topic + "\nUser angle (unverified): " + notes + "\n"
              "Return a concise factual briefing: what it does, real availability, "
              "features verifiable from the page, implications for developers, and caveats. "
              "Treat the user's claims as unverified. No inventions or unsourced stats.")
    payload = gemini(prompt, source_url=source)
    metadata = [x for c in payload.get("candidates", [])
                for x in c.get("urlContextMetadata", {}).get("urlMetadata", [])]
    successful = [x for x in metadata if x.get("urlRetrievalStatus") == "URL_RETRIEVAL_STATUS_SUCCESS"]
    requested_host = urlparse(source).hostname
    if not any(urlparse(x.get("retrievedUrl", "")).hostname == requested_host for x in successful):
        raise ValueError("Gemini could not retrieve the official URL; requires manual research.")
    return response_text(payload)


def generate_post(req: dict, post_id: str) -> dict:
    source = req["source_url"].strip()
    facts = verified_facts(source, req["topic"], req.get("notes", ""))
    instructions = (
        "You are preparing an editorial LinkedIn post. Use ONLY verified facts below. "
        "Return a single JSON object with keys topic, category, caption, slides. "
        "Write a natural punchy caption with 3-4 relevant hashtags. "
        "Create exactly 6 slide objects in this order: cover, cards, comparison, cards, timeline, closing. "
        "Every slide needs type, eyebrow and short title. Cover has subtitle. "
        "Each cards slide has three cards as arrays [number,title,body]. "
        "Comparison has left and right objects with label, title, items (list of 3 short strings). "
        "Timeline has events list of 3 [number,title,body] arrays. "
        "Closing has subtitle and source. Keep headings readable on a phone. "
        "Do not include literal backslash-n or fictitious benchmarks, dates or quotations."
    )
    payload = gemini(instructions + "\nSOURCE: " + source +
                     "\nUSER TOPIC: " + req["topic"] + "\nVERIFIED FACTS:\n" + facts)
    generated = json.loads(response_text(payload))
    slides = generated.get("slides")
    caption = generated.get("caption")
    if not isinstance(slides, list) or len(slides) != 6:
        raise ValueError("Model did not return exactly six slides.")
    for index, (slide, layout) in enumerate(zip(slides, LAYOUTS), 1):
        if not isinstance(slide, dict) or slide.get("type") != layout:
            raise ValueError(f"Slide {index}: expected {layout} layout.")
        if not isinstance(slide.get("title"), str) or not 4 <= len(slide["title"]) <= 105:
            raise ValueError(f"Slide {index} heading is missing or too long.")
    if not isinstance(caption, str) or not 100 <= len(caption) <= 2900:
        raise ValueError("Draft caption is missing or too long.")
    topic = str(generated.get("topic") or req["topic"])[:160]
    category = str(generated.get("category") or "Developer Tools")[:80]
    theme = ("claude" if "claude" in (topic + category).lower() else
             "shopify" if "shopify" in (topic + category).lower() else
             "openai" if "openai" in (topic + category).lower() else "developer")
    return {
        "id": post_id, "status": "ready", "topic": topic, "category": category,
        "format": "document", "caption": caption.strip(), "source_url": source,
        "sources": [source], "created_at": datetime.now(timezone.utc).isoformat(),
        "origin_request": f"queue/topic_requests/{post_id}.json",
        "document": {"title": topic, "renderer": "v3", "carousel": {
            "topic": topic, "theme": theme,
            "brand": {"name": "WAJAHAT NAQVI", "subtitle": "Shopify · Full-stack · AI"},
            "slides": slides,
        }},
    }


def prepare(request_name: str) -> tuple[str, str]:
    request_path = (ROOT / request_name).resolve()
    if request_path.parent != REQUEST_DIR.resolve() or not request_path.is_file():
        raise ValueError("Provide an existing request path inside queue/topic_requests/.")
    req = load_json(request_path, {})
    post_id = request_path.stem
    if req.get("status") == "ready" and draft_path(post_id).is_file():
        return post_id, ""
    if draft_path(post_id).is_file():
        raise ValueError("A saved draft already exists; refusing to overwrite.")
    if req.get("status") not in {"pending_research", "needs_review", "needs_source", "needs_configuration"}:
        raise ValueError("Request cannot be prepared from its current state.")
    if not req.get("source_url"):
        req.update(status="needs_source", message="An official source URL is required in free automatic mode.")
        save_json(request_path, req)
        return "", ""
    if not is_primary_source(req["source_url"]):
        req.update(status="needs_review", message="Official source domain not approved in config/official_sources.json.")
        save_json(request_path, req)
        return "", ""
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        req.update(status="needs_configuration", message="Add free-tier GEMINI_API_KEY in GitHub Actions secrets.")
        save_json(request_path, req)
        return "", ""
    try:
        post = generate_post(req, post_id)
        history = load_json(ROOT / "data" / "history.json", []) or []
        if any(x.get("id") == post_id or x.get("source_url") == post["source_url"] for x in history):
            raise ValueError("Story already published. No duplicate draft created.")
        destination = ROOT / "generated" / f"{post_id}.pdf"
        render_carousel_pdf(post["document"]["carousel"], destination)
        latest = load_json(LATEST, {}) or {}
        select = latest.get("status") != "ready"
        create_draft(post, select=select)
        req.update(status="ready", draft_id=post_id, selected_as_latest=select)
        req.pop("message", None)
        save_json(request_path, req)
        print(f"DRAFT READY: {post_id} — preview PDF generated; NOT published.")
        return post_id, destination.relative_to(ROOT).as_posix()
    except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
        req.update(status="needs_review", message=str(exc)[:360])
        save_json(request_path, req)
        print("NEEDS REVIEW: " + req["message"])
        return "", ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--github-output", default=os.getenv("GITHUB_OUTPUT", ""))
    args = parser.parse_args()
    post_id, pdf = prepare(args.request)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.write(f"post_id={post_id}\npdf_path={pdf}\n")


if __name__ == "__main__":
    main()
