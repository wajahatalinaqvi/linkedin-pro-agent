from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from linkedin import LinkedInClient, LinkedInError

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "queue" / "latest.json"
HISTORY_PATH = ROOT / "data" / "history.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temporary.replace(path)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def validate_queue(post: dict) -> None:
    if post.get("status") != "ready":
        raise ValueError(
            f"Queue status is {post.get('status')!r}; nothing is ready to publish."
        )

    for field in ("id", "caption", "source_url"):
        if not str(post.get(field, "")).strip():
            raise ValueError(f"Missing required queue field: {field}")

    if len(post["caption"]) > 3000:
        raise ValueError("Caption exceeds the 3000-character limit used by this agent.")


def duplicate_reason(post: dict, history: list[dict]) -> str | None:
    post_id = str(post.get("id", "")).strip()
    source_url = str(post.get("source_url", "")).strip()

    for item in history:
        if post_id and item.get("id") == post_id:
            return f"id {post_id!r} is already in history"
        if source_url and item.get("source_url") == source_url:
            return f"source_url {source_url!r} is already in history"

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish queue/latest.json to LinkedIn."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Publish even when AUTO_PUBLISH=false. "
            "Does not bypass validation or duplicate checks."
        ),
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    post = load_json(QUEUE_PATH, {})
    history = load_json(HISTORY_PATH, [])
    validate_queue(post)

    reason = duplicate_reason(post, history)
    if reason:
        print(f"SKIP: {reason}")
        return 0

    auto_publish = env_bool("AUTO_PUBLISH", False)
    if not auto_publish and not args.force:
        print("DRY RUN: queue is valid and not previously published.")
        print(f"Topic: {post.get('topic', '')}")
        print(f"Source: {post['source_url']}")
        print("Set AUTO_PUBLISH=true or run with --force to publish.")
        return 0

    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    author = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    version = os.getenv("LINKEDIN_VERSION", "202607").strip()

    if not token or not author:
        raise ValueError(
            "LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN are required."
        )

    client = LinkedInClient(token, author, version)

    image_urn = None
    image_url = str(post.get("image_url", "")).strip()
    if image_url:
        print("Uploading image to LinkedIn...")
        image_urn = client.upload_image_from_url(image_url)

    print("Publishing LinkedIn post...")
    linkedin_post_id = client.create_post(
        caption=post["caption"],
        image_urn=image_urn,
        image_alt=str(post.get("image_alt", "")).strip(),
    )

    published_at = datetime.now(timezone.utc).isoformat()

    history.append(
        {
            "id": post["id"],
            "topic": post.get("topic", ""),
            "source_url": post["source_url"],
            "linkedin_post_id": linkedin_post_id,
            "published_at": published_at,
        }
    )
    save_json(HISTORY_PATH, history)

    post["status"] = "published"
    post["linkedin_post_id"] = linkedin_post_id
    post["published_at"] = published_at
    save_json(QUEUE_PATH, post)

    print(f"SUCCESS: {linkedin_post_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, LinkedInError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
