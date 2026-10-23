"""Meaning-driven diagrams; never invent steps, features, or metrics."""
from __future__ import annotations

def apply_visual_storytelling(carousel: dict) -> list[str]:
    if carousel.get("design_version") != "studio-v2":
        return []
    changed: list[str] = []
    for slide in carousel.get("slides", []):
        if not isinstance(slide, dict):
            continue
        intent = slide.get("visual_intent")
        kind = slide.get("type")
        if intent == "process" and kind in ("timeline", "workflow"):
            steps = slide.get("steps") or slide.get("events") or []
            if isinstance(steps, list) and 3 <= len(steps) <= 4:
                slide["type"] = "process_map"
                slide["steps"] = steps
                changed.append("process_map")
        if intent == "editorial_insights" and kind in ("cards", "feature_grid"):
            cards = slide.get("cards") or slide.get("features") or []
            if isinstance(cards, list) and 2 <= len(cards) <= 4:
                slide["type"] = "insight_list"
                slide["cards"] = cards
                changed.append("insight_list")
    return changed
