"""Rotate professional editorial angles without fictional first-hand claims."""
from __future__ import annotations
from hashlib import sha256

ANGLES = (
    ("developer_consequence", "Take a specific developer-facing position: what should builders do differently? Explain one implementation detail and a caveat."),
    ("surprising_boundary", "Lead with a verified contrast: what the feature enables versus what it explicitly does not guarantee."),
    ("workflow_shift", "Explain the actual workflow change. Prefer precise verbs, tool names, and practical decisions over slogans."),
    ("merchant_decision", "Lead with an operational consequence for merchants, then explain a developer implication and a caveat."),
)
EDITORIAL_VOICE = (
    "Write like a technically literate developer sharing a thoughtful observation with peers. "
    "Calm, specific, credible and readable. Vary sentence length and use natural short paragraphs. "
    "Avoid a rigid hook/bullets/closing-question template. A genuine question is optional. "
    "Never claim 'I tested', 'I built', 'my client', or pretend to have first-hand experience. "
    "No generic enthusiasm, exaggerated urgency, emoji decoration or em-dash chains. "
    "Avoid 'not just X, but Y' and 'this changes everything'. "
    "Use real API names and source-grounded observations. Zero to two hashtags at the end."
)

def choose_angle(post_id: str) -> tuple[str, str]:
    index = sha256(post_id.encode("utf-8")).digest()[0] % len(ANGLES)
    return ANGLES[index]
