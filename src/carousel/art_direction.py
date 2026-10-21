"""Choose and persist a visually distinct cover-and-pages design for each new story.

Never retrofit published legacy carousels. Design is stored in each new post JSON so
rerenders are stable and past previews do not change based on repository activity.
"""
from __future__ import annotations

import json
from pathlib import Path

from .creative_direction import apply_creative_profile

DESIGNS = (
    "editorial",     # paper, newspaper columns, serif headline
    "neon",          # dark electric poster with diagonals
    "swiss",         # minimalist grid and oversized geometric type
    "collage",       # warm cut-paper shapes and off-center composition
    "blueprint",     # technical blueprint gridding and annotations
    "gradient",      # bright color field and floating geometry
    "brutalist",     # punchy high-contrast angular headlines
    "journal",       # refined monochrome journal and ruled dividers
)
LEGACY = "classic"


def validate_direction(value: str) -> str:
    if value not in (LEGACY, *DESIGNS):
        raise ValueError(f"Unknown art_direction {value!r}. Choose from: {', '.join(DESIGNS)}")
    return value


def pick_direction(post_id: str, drafts_dir: Path) -> str:
    """Round-robin across saved posts; never repeat the most recent direction."""
    existing = []
    if drafts_dir.is_dir():
        for path in drafts_dir.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if not isinstance(item, dict) or item.get("id") == post_id:
                continue
            carousel = (item.get("document") or {}).get("carousel") or {}
            variant = carousel.get("art_direction", LEGACY)
            existing.append((item.get("created_at", ""), str(item.get("id", "")), variant))
    existing.sort()
    # Include older legacy posts in the rotation; repeating the same brand is OK,
    # but the next new publication always receives a fresh visual composition.
    chosen_index = len(existing) % len(DESIGNS)
    if existing and existing[-1][2] == DESIGNS[chosen_index]:
        chosen_index = (chosen_index + 1) % len(DESIGNS)
    return DESIGNS[chosen_index]


def set_art_direction(carousel: dict, post_id: str, drafts_dir: Path) -> str:
    """Preserve an explicit approved design; otherwise assign and record one."""
    existing = carousel.get("art_direction")
    if existing:
        direction = validate_direction(existing)
    else:
        direction = pick_direction(post_id, drafts_dir)
        carousel["art_direction"] = direction
    # Called only for new drafts. Published legacy files are never migrated.
    apply_creative_profile(carousel, post_id, direction)
    return direction
