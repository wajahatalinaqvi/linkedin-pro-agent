"""Saved LinkedIn draft selection and persistence. No LinkedIn API access."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "queue" / "latest.json"
DRAFTS = ROOT / "queue" / "drafts"
HISTORY = ROOT / "data" / "history.json"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$")


def validate_id(post_id: str) -> str:
    if not isinstance(post_id, str) or post_id in {".", ".."} or not SAFE_ID.fullmatch(post_id):
        raise ValueError("Invalid post ID. Use 1-120 letters, numbers, dots, hyphens or underscores.")
    return post_id


def draft_path(post_id: str) -> Path:
    return DRAFTS / f"{validate_id(post_id)}.json"


def load_json(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_post(post_id: str = "") -> tuple[dict, Path]:
    """Explicit post_id selects a saved draft; blank uses legacy latest.json."""
    if post_id:
        validate_id(post_id)
        path = draft_path(post_id)
        if path.is_file():
            post = load_json(path, {})
            if not isinstance(post, dict) or post.get("id") != post_id:
                raise ValueError(f"Draft ID mismatch: {post_id}")
            return post, path
        latest = load_json(LATEST, {}) or {}
        if latest.get("id") == post_id:
            return latest, LATEST
        raise ValueError(f"Draft '{post_id}' not found. Check queue/drafts.")
    return load_json(LATEST, {}) or {}, LATEST


def save_post(post: dict, path: Path) -> None:
    """Update only the selected draft, mirroring latest if it refers to the same ID."""
    post_id = validate_id(post["id"])
    if path not in {LATEST, draft_path(post_id)}:
        raise ValueError("Refusing to write outside the selected draft.")
    save_json(path, post)
    other = draft_path(post_id) if path == LATEST else LATEST
    existing = load_json(other, {}) or {}
    if isinstance(existing, dict) and existing.get("id") == post_id:
        save_json(other, post)


def create_draft(post: dict, *, select: bool = False) -> Path:
    post_id = validate_id(post["id"])
    if post.get("status") != "ready":
        raise ValueError("A new draft must have status='ready'.")
    if not str(post.get("caption", "")).strip() or not str(post.get("source_url", "")).strip():
        raise ValueError("Draft requires a caption and source URL.")
    existing = load_json(HISTORY, []) or []
    if any(item.get("id") == post_id for item in existing):
        raise ValueError("This story ID was already published.")
    path = draft_path(post_id)
    if path.exists():
        raise ValueError(f"Draft already exists: {post_id}. Edit the saved draft instead.")
    save_json(path, post)
    if select:
        select_draft(post_id)
    return path


def select_draft(post_id: str) -> None:
    """Select a saved post and preserve any displaced active ready post."""
    post, source = load_post(post_id)
    if source == LATEST:
        return
    current = load_json(LATEST, {}) or {}
    if current.get("status") == "ready" and current.get("id") != post_id:
        old_id = validate_id(current["id"])
        previous_path = draft_path(old_id)
        if not previous_path.exists():
            save_json(previous_path, current)
    save_json(LATEST, post)


def list_drafts() -> list[dict]:
    result = []
    if DRAFTS.is_dir():
        for path in sorted(DRAFTS.glob("*.json")):
            post = load_json(path, {})
            if isinstance(post, dict) and post.get("id"):
                result.append({"id": post["id"], "topic": post.get("topic", ""), "status": post.get("status", "")})
    return result
