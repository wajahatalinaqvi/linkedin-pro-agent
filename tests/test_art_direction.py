"""Regression checks for varied, stable, automatically assigned carousel art directions."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carousel.art_direction import DESIGNS, pick_direction, set_art_direction
from carousel.renderer import render_html


class VisualVarietyTests(unittest.TestCase):
    def test_eight_distinct_art_directions(self):
        self.assertEqual(len(DESIGNS), 8)
        self.assertEqual(len(set(DESIGNS)), 8)

    def test_consecutive_new_posts_rotate(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            seen = []
            for i in range(12):
                post_id = f"story-{i}"
                chosen = pick_direction(post_id, directory)
                if seen:
                    self.assertNotEqual(chosen, seen[-1])
                seen.append(chosen)
                (directory / f"{post_id}.json").write_text(json.dumps({
                    "id": post_id,
                    "created_at": f"2026-10-{i+1:02d}T00:00:00Z",
                    "document": {"carousel": {"art_direction": chosen}},
                }))
            self.assertEqual(set(seen[:8]), set(DESIGNS))

    def test_explicit_design_is_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            carousel = {"art_direction": "swiss"}
            self.assertEqual(set_art_direction(carousel, "x", Path(temp)), "swiss")

    def test_legacy_default_keeps_old_design(self):
        slides = [
            {"type": "cover", "title": "Published legacy cover"},
            {"type": "cards", "title": "One"},
            {"type": "cards", "title": "Two"},
            {"type": "comparison", "title": "Three"},
            {"type": "timeline", "title": "Four"},
            {"type": "closing", "title": "Five"},
        ]
        legacy = render_html({"theme": "claude", "slides": slides})
        modern = render_html({"theme": "claude", "art_direction": "swiss", "slides": slides})
        self.assertIn("art-classic", legacy)
        self.assertIn("art-swiss", modern)
        self.assertIn(".art-swiss.layout-cover", modern)


if __name__ == "__main__":
    unittest.main()
