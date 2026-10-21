"""Deterministic creative art direction for NEW carousel drafts only.

Changes composition, narrative rhythm, graphics and typography rather than
merely swapping colors. Never adds claims or quote text.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

TYPOGRAPHY = {
    "editorial": "literary",
    "neon": "poster",
    "swiss": "grotesk",
    "collage": "humanist",
    "blueprint": "technical",
    "gradient": "contrast",
    "brutalist": "condensed",
    "journal": "journal",
}
MOTIFS = {
    "editorial": "rules",
    "neon": "rays",
    "swiss": "blocks",
    "collage": "cutouts",
    "blueprint": "diagram",
    "gradient": "orbs",
    "brutalist": "stamps",
    "journal": "arches",
}
COMPOSITIONS = ("mosaic", "rail", "spotlight", "tiles")
# Slot IDs reference the model's VERIFIED six-slide draft. Only the order
# changes; no facts or attribution are synthesized.
STORYBOARDS = (
    (0, 1, 2, 3, 4, 5),
    (0, 2, 1, 4, 3, 5),
    (0, 1, 4, 2, 3, 5),
    (0, 3, 2, 1, 4, 5),
    (0, 4, 1, 3, 2, 5),
    (0, 2, 4, 1, 3, 5),
    (0, 3, 1, 4, 2, 5),
    (0, 1, 3, 4, 2, 5),
)

def stable_number(key: str) -> int:
    return int.from_bytes(sha256(key.encode("utf-8")).digest()[:8], "big")


def remix_storyboard(carousel: dict, post_id: str, direction: str) -> None:
    slides = carousel.get("slides")
    if not isinstance(slides, list) or len(slides) != 6:
        return
    if [s.get("type") for s in slides] != [
        "cover", "cards", "comparison", "cards", "timeline", "closing"
    ]:
        return
    # Stable differences across posts, even with the same topic and direction.
    index = stable_number(f"{post_id}|{direction}|storyboard") % len(STORYBOARDS)
    order = STORYBOARDS[index]
    reordered = [deepcopy(slides[i]) for i in order]
    for slot, slide in enumerate(reordered[1:-1], start=1):
        # Turn some conventional rectangular-card layouts into alternative
        # visual grammars while retaining the original verified content.
        if slide["type"] == "cards" and (slot + index) % 2 == 0:
            slide["type"] = "feature_grid"
            slide["features"] = slide.pop("cards", [])
        elif slide["type"] == "timeline" and (slot + index) % 2 == 1:
            slide["type"] = "workflow"
            slide["steps"] = slide.pop("events", [])
        elif slide["type"] == "comparison" and (slot + index) % 2 == 0:
            slide["type"] = "before_after"
    carousel["slides"] = reordered
    carousel["storyboard"] = f"sequence-{index + 1}"


def apply_creative_profile(carousel: dict, post_id: str, direction: str) -> dict:
    existing = carousel.get("creative_profile")
    if existing is not None:
        # An approved, explicit visual system must remain stable.
        if not isinstance(existing, dict):
            raise ValueError("creative_profile must be an object.")
        return existing
    if direction not in TYPOGRAPHY:
        return {}
    remix_storyboard(carousel, post_id, direction)
    offset = stable_number(f"{post_id}|{direction}|composition") % len(COMPOSITIONS)
    # Assign one distinct composition per page, not one template per deck.
    styles = [COMPOSITIONS[(offset + (i * 3)) % len(COMPOSITIONS)] for i in range(len(carousel.get("slides", [])))]
    profile = {
        "typography": TYPOGRAPHY[direction],
        "motif": MOTIFS[direction],
        "compositions": styles,
        "edition": stable_number(post_id) % 900 + 100,
    }
    carousel["creative_profile"] = profile
    return profile
