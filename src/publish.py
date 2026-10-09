from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from linkedin import LinkedInClient, LinkedInError
from slides import SlideRenderError, render_document
from carousel.render_pdf import render_carousel_pdf
from post_store import load_post, save_post

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "queue" / "latest.json"
HISTORY_PATH = ROOT / "data" / "history.json"
GENERATED_DIR = ROOT / "generated"
SUPPORTED_FORMATS = {"text", "image", "document"}
NOOP_STATUSES = {"idle", "published", "skipped"}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def validate_queue(post: dict) -> str:
    status = str(post.get("status", "idle")).strip().lower()
    if status in NOOP_STATUSES:
        return status
    if status != "ready":
        raise ValueError(f"Unsupported queue status: {status!r}")

    for field in ("id", "caption", "source_url"):
        if not str(post.get(field, "")).strip():
            raise ValueError(f"Missing required queue field: {field}")

    post_format = str(post.get("format", "text")).strip().lower()
    if post_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {post_format}")
    if len(post["caption"]) > 3000:
        raise ValueError("Caption exceeds the 3000-character safety limit used by this agent.")
    if post_format == "image" and not str(post.get("image_url", "")).strip():
        raise ValueError("Image format requires image_url.")
    if post_format == "document":
        document = post.get("document") or {}
        has_path = bool(str(document.get("path", "")).strip())
        has_legacy_slides = bool(document.get("slides") or [])
        uses_v3 = str(document.get("renderer", "")).strip().lower() == "v3"
        has_v3_carousel = uses_v3 and bool(document.get("carousel") or {})
        if not (has_path or has_legacy_slides or has_v3_carousel):
            raise ValueError(
                "Document format requires document.path, document.slides, "
                'or renderer="v3" with document.carousel.'
            )
    return status


def all_source_urls(post: dict) -> set[str]:
    urls = {str(post.get("source_url", "")).strip()}
    for item in post.get("sources") or []:
        if isinstance(item, str):
            urls.add(item.strip())
        elif isinstance(item, dict):
            urls.add(str(item.get("url", "")).strip())
    return {u for u in urls if u}


def duplicate_reason(post: dict, history: list[dict]) -> str | None:
    post_id = str(post.get("id", "")).strip()
    source_urls = all_source_urls(post)
    for item in history:
        if post_id and item.get("id") == post_id:
            return f"id {post_id!r} is already in history"
        historical = {str(item.get("source_url", "")).strip()}
        historical.update(str(url).strip() for url in item.get("sources", []) or [])
        if source_urls.intersection({u for u in historical if u}):
            return "one of this post's source URLs is already in history"
    return None


def prepare_document(post: dict):
    document = post.get("document") or {}

    title = str(
        document.get("title")
        or post.get("topic")
        or "Tech update"
    ).strip()

    configured = str(
        document.get("path", "")
    ).strip()

    if configured:
        path = ROOT / configured

        if not path.exists():
            raise ValueError(
                f"Configured document.path does not exist: {path}"
            )

        return path, title

    output = GENERATED_DIR / f"{post['id']}.pdf"

    renderer = str(
        document.get("renderer", "legacy")
    ).strip().lower()

    if renderer == "v3" and document.get("carousel"):
        carousel = document.get("carousel") or {}
        rendered = render_carousel_pdf(
            carousel,
            output,
        )

        return rendered, title

    return render_document(
        post,
        output,
    ), title


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish queue/latest.json to LinkedIn.")
    parser.add_argument("--post-id", default="", help="Saved draft ID to publish instead of latest.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    post, selected_path = load_post(args.post_id)
    history = load_json(HISTORY_PATH, [])
    status = validate_queue(post)
    if status in NOOP_STATUSES:
        print(f"NOOP: queue status is {status!r}.")
        return 0

    reason = duplicate_reason(post, history)
    if reason:
        print(f"SKIP: {reason}")
        return 0

    post_format = str(post.get("format", "text")).lower()
    if args.render_only:
        if post_format != "document":
            print("NOOP: --render-only only applies to document posts.")
            return 0
        path, _ = prepare_document(post)
        print(f"RENDERED: {path}")
        return 0

    if not env_bool("AUTO_PUBLISH", False) and not args.force:
        print(f"DRY RUN: valid {post_format} post ready: {post.get('topic', '')}")
        return 0

    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    author = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    version = os.getenv("LINKEDIN_VERSION", "202609").strip()
    if not token or not author:
        raise ValueError("LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN are required.")

    client = LinkedInClient(token, author, version)
    image_urn = document_urn = None
    document_title = ""

    if post_format == "image":
        image_urn = client.upload_image_from_url(post["image_url"])
    elif post_format == "document":
        path, document_title = prepare_document(post)
        document_urn = client.upload_document(path)

    linkedin_post_id = client.create_post(
        caption=post["caption"],
        image_urn=image_urn,
        image_alt=str(post.get("image_alt", "")).strip(),
        document_urn=document_urn,
        document_title=document_title,
    )

    published_at = datetime.now(timezone.utc).isoformat()
    history.append({
        "id": post["id"],
        "topic": post.get("topic", ""),
        "category": post.get("category", ""),
        "format": post_format,
        "priority_score": post.get("priority_score", 0),
        "source_url": post["source_url"],
        "sources": sorted(all_source_urls(post)),
        "linkedin_post_id": linkedin_post_id,
        "published_at": published_at,
    })
    save_json(HISTORY_PATH, history)
    post["status"] = "published"
    post["linkedin_post_id"] = linkedin_post_id
    post["published_at"] = published_at
    save_post(post, selected_path)
    print(f"SUCCESS: {linkedin_post_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, LinkedInError, SlideRenderError, json.JSONDecodeError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
