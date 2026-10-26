"""Pre-publication *editorial* checks, not a claim of fact verification.

Generated copy remains untrusted and always requires human approval. The
gate rejects shallow content and clickbait rather than inventing a stronger claim.
"""
from __future__ import annotations

import re

BANNED = (
    "you won't believe", "this changes everything", "game changer",
    "the future is here", "unbelievable", "mind blowing", "must see",
    "breaking news", "ready to build", "core capabilities",
    "developer guidelines", "everything you need to know",
    "in today's fast-paced", "let's dive in", "the future of",
    "revolutionary", "unlock the power", "delve into",
    "exciting development", "here's why it matters",
)


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w’-]+\b", value))


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def review_generated(generated: dict) -> list[str]:
    issues = []
    slides = generated.get("slides")
    if not isinstance(slides, list) or len(slides) != 6:
        return ["Create exactly six slides."]
    if not all(isinstance(x, dict) for x in slides):
        return ["Every slide must be an object."]
    title = str(slides[0].get("title") or "").strip()
    if not 4 <= word_count(title) <= 14 or len(title) > 95:
        issues.append("Cover must use a concise, specific hook of 4-14 words and at most 95 characters.")
    if any(bad in title.lower() for bad in BANNED):
        issues.append("Cover uses generic or engagement-bait wording.")
    hooks = generated.get("hook_options")
    if not isinstance(hooks, list) or len(hooks) != 3:
        issues.append("Provide exactly three distinct candidate hooks.")
    else:
        hooks = [str(x).strip() for x in hooks]
        if len({normalize(x) for x in hooks}) != 3 or any(not 4 <= word_count(x) <= 14 or len(x) > 95 for x in hooks):
            issues.append("Each candidate hook must be distinct, meaningful, and fit the cover.")
        if normalize(title) not in {normalize(x) for x in hooks}:
            issues.append("The chosen cover title must be one of the three hook options.")
    caption = generated.get("caption")
    if not isinstance(caption, str):
        issues.append("Provide a substantive LinkedIn caption.")
    else:
        stripped = caption.strip()
        opening = stripped.split("\n", 1)[0].strip()
        words = word_count(stripped)
        if not 95 <= words <= 260:
            issues.append("Caption should contain 95-260 meaningful words.")
        if not 20 <= len(opening) <= 150:
            issues.append("Open with one strong, specific first line.")
        if any(bad in opening.lower() for bad in BANNED):
            issues.append("Caption opening uses generic or engagement-bait language.")
        if "\n\n" not in stripped:
            issues.append("Use short paragraphs to support mobile reading.")
        if stripped.count("#") > 2:
            issues.append("Use no more than two relevant hashtags.")
        if stripped.count("—") > 2:
            issues.append("Avoid repetitive em-dash phrasing.")
        if any(phrase in stripped.lower() for phrase in BANNED):
            issues.append("Caption contains generic hype or AI-template language.")
        if re.search(r"\b(?:i (?:tested|built|launched)|my client|we tested)\b", stripped, flags=re.IGNORECASE):
            issues.append("First-hand experience claims require explicit author approval.")
    vague_titles = ("core capabilities", "developer guidelines", "ready to build", "requirements & availability")
    for i, slide in enumerate(slides[1:], 2):
        head = str(slide.get("title") or "").strip()
        if not head or normalize(head) in {normalize(x) for x in vague_titles}:
            issues.append(f"Slide {i} needs a useful, specific title.")
    return issues
