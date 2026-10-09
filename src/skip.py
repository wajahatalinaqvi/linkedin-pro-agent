from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from post_store import load_post, save_post

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "queue" / "latest.json"
SKIPPED_PATH = ROOT / "data" / "skipped.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Skip the current ready post without publishing it.")
    parser.add_argument("--post-id", default="", help="Optional draft ID.")
    parser.add_argument("--confirm", required=True, help="Must be SKIP")
    args = parser.parse_args()

    if args.confirm != "SKIP":
        raise SystemExit("Confirmation failed. Re-run with --confirm SKIP.")

    queue, selected_path = load_post(args.post_id)
    status = str(queue.get("status", "")).strip().lower()
    if status != "ready":
        print(f"NOOP: queue status is {status!r}; expected 'ready'.")
        return 0

    skipped = load_json(SKIPPED_PATH, [])
    if not isinstance(skipped, list):
        raise ValueError("data/skipped.json must contain a JSON array.")

    entry = {
        "id": queue.get("id", ""),
        "topic": queue.get("topic", ""),
        "category": queue.get("category", ""),
        "source_url": queue.get("source_url", ""),
        "sources": queue.get("sources") or [],
        "priority_score": queue.get("priority_score", ""),
        "skipped_at": datetime.now(timezone.utc).isoformat(),
    }

    existing_ids = {str(item.get("id", "")) for item in skipped if isinstance(item, dict)}
    if entry["id"] and entry["id"] not in existing_ids:
        skipped.append(entry)
        save_json(SKIPPED_PATH, skipped)

    queue["status"] = "skipped"
    queue["skipped_at"] = entry["skipped_at"]
    save_post(queue, selected_path)

    print(f"SKIPPED: {entry['id']} — {entry['topic']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
