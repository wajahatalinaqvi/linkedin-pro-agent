"""Save user-priority research requests; never assumes claims are verified."""
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from post_store import ROOT, save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a manual priority LinkedIn topic.")
    parser.add_argument("--github-output", default="")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    topic = args.topic.strip()
    if not 3 <= len(topic) <= 180:
        raise ValueError("Topic must contain 3 to 180 characters.")
    source = args.source_url.strip()
    if source and (urlparse(source).scheme not in {"http", "https"} or not urlparse(source).netloc):
        raise ValueError("Source must be an HTTP(S) URL.")
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "topic"
    path = ROOT / "queue" / "topic_requests" / f"{stamp}-{slug}.json"
    save_json(path, {
        "topic": topic, "source_url": source, "notes": args.notes.strip(),
        "requested_at": now.isoformat(), "priority": "user_requested",
        "status": "pending_research",
    })
    print(f"REQUEST SAVED: {path.relative_to(ROOT).as_posix()}")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as handle:
            handle.write(f"request_path={path.relative_to(ROOT).as_posix()}\n")
    print("This is a research request, not a publishable draft. Verify source claims before creating a post.")


if __name__ == "__main__":
    main()
