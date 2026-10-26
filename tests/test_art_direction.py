"""Regression checks for varied, stable, automatically assigned carousel art directions."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from carousel.art_direction import DESIGNS, pick_direction, set_art_direction, pick_layout_family
from carousel.creative_direction import STORYBOARDS
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

    def test_new_drafts_vary_story_structure_and_visual_profile(self):
        slides = [
            {"type": "cover", "title": "Source verified change"},
            {"type": "cards", "title": "Features", "cards": [["01", "First", "Body"]]},
            {"type": "comparison", "title": "Before after", "left": {"items": ["Before"]}, "right": {"items": ["After"]}},
            {"type": "cards", "title": "Practical changes", "cards": [["01", "More", "Body"]]},
            {"type": "timeline", "title": "What to do", "events": [["01", "Review", "Impact"]]},
            {"type": "closing", "title": "Summary", "source": "https://shopify.dev"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            styles = []
            sequences = []
            for i in range(16):
                carousel = {"theme": "shopify", "slides": json.loads(json.dumps(slides))}
                direction = set_art_direction(carousel, f"sample-{i}", Path(tmp))
                profile = carousel["creative_profile"]
                self.assertEqual(len(profile["compositions"]), 6)
                self.assertIn(profile["layout_family"], ("editorial", "asymmetric", "technical", "typography"))
                self.assertEqual(len(carousel["slides"]), 6)
                self.assertEqual(carousel["slides"][0]["type"], "cover")
                self.assertEqual(carousel["slides"][-1]["type"], "closing")
                self.assertEqual([s["title"] for s in carousel["slides"]], [s["title"] for s in slides])
                self.assertIn(carousel["storyboard"], {f"sequence-{j+1}" for j in range(len(STORYBOARDS))})
                rendered = render_html(carousel)
                self.assertIn("compose-", rendered)
                self.assertIn("motif-", rendered)
                self.assertIn("font-", rendered)
                styles.append((direction, profile["typography"], profile["motif"]))
                sequences.append(carousel["storyboard"])
                (Path(tmp) / f"sample-{i}.json").write_text(json.dumps({"id": f"sample-{i}", "created_at": f"2026-10-{i+1:02d}T00:00:00Z", "document": {"carousel": carousel}}))
            self.assertGreater(len(set(styles)), 3)
            self.assertGreater(len(set(sequences)), 3)

    def test_feature_grid_count_classes_and_geometry_rules(self):
        for count in (2, 3, 4):
            carousel = {"design_version": "studio-v2", "theme": "shopify", "slides": [
                {"type": "cover", "title": "New useful Shopify feature"},
                {"type": "feature_grid", "title": "Developer implications",
                 "features": [[str(i), f"Point {i}", "Supported detail"] for i in range(count)]},
                {"type": "comparison", "title": "Compare behaviors"},
                {"type": "cards", "title": "Further details"},
                {"type": "timeline", "title": "Implementation steps"},
                {"type": "closing", "title": "Conclusion"},
            ]}
            html = render_html(carousel)
            self.assertIn(f"feature-grid card-count-{count}", html)
            self.assertIn(f".feature-grid.card-count-{count}", html)

    def test_family_rotation_skips_two_most_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, family in enumerate(("editorial", "technical")):
                (root / f"recent-{index}.json").write_text(json.dumps({
                    "id": f"recent-{index}", "created_at": f"2026-10-{index+20}T11:00:00Z",
                    "document": {"carousel": {"creative_profile": {"layout_family": family}}},
                }))
            self.assertIn(pick_layout_family("new-draft", root), ("asymmetric", "typography"))

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
