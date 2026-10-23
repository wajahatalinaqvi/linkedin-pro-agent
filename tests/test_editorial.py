"""No external services required for editorial ranking and copy checks."""
from __future__ import annotations
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from editorial import editorial_score, ranked_candidates
from editorial_quality import review_generated


class EditorialTests(unittest.TestCase):
    def test_high_impact_beats_minor_changelog(self):
        now = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
        major = {"topic": "New Shopify checkout API enables AI agents",
                 "category": "Shopify", "published": now}
        minor = {"topic": "Minor documentation correction",
                 "category": "Shopify", "published": now}
        self.assertGreater(editorial_score(major, now), editorial_score(minor, now))
        self.assertEqual(ranked_candidates([minor, major], now)[0]["topic"], major["topic"])

    def test_boring_updates_can_be_skipped(self):
        now = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
        low = {"topic": "Minor documentation correction", "category": "GitHub", "published": now}
        self.assertEqual(ranked_candidates([low], now), [])

    def test_copy_gate_rejects_clickbait(self):
        content = self.example()
        content["slides"][0]["title"] = "This changes everything"
        self.assertTrue(review_generated(content))

    def test_copy_gate_rejects_unsubstantial_caption(self):
        content = self.example()
        content["caption"] = "Shopify now has a new feature. #Shopify"
        self.assertTrue(any("95-260" in x for x in review_generated(content)))

    def test_copy_gate_accepts_factual_longform_structure(self):
        self.assertEqual(review_generated(self.example()), [])

    def example(self):
        cover = "AI agents can now discover nearby Shopify retail locations"
        p = ("Developers now have a way to build location-aware commerce experiences.\n\n"
             "For merchants with active retail locations, this opens another discovery "
             "path beyond a traditional shopping page. Rather than promise local pickup, "
             "an agent can first search for relevant stores and then look up known ones. "
             "That distinction matters because location discovery is not a guarantee "
             "of available inventory or a supported fulfillment option.\n\n"
             "Before building, check whether the merchant qualifies and whether the "
             "storefront exposes the required capabilities. Keep customer location "
             "sharing intentional, validate the locations returned, and confirm final "
             "availability through the applicable buying flow. These checks make the "
             "experience more useful without misleading customers.\n\n"
             "Where would location-aware shopping fit into an existing commerce workflow?"
             "\n\n#ShopifyDev #AICommerce")
        return {"caption": p, "hook_options": [
            cover, "Shopping agents are getting closer to physical retail",
            "What Shopify location discovery changes for developers"
        ], "slides": [
            {"type": "cover", "title": cover},
            {"type": "cards", "title": "Give shoppers a useful place to start"},
            {"type": "comparison", "title": "Search versus lookup is the important distinction"},
            {"type": "cards", "title": "Check what the merchant actually supports"},
            {"type": "timeline", "title": "Build safer location discovery experiences"},
            {"type": "closing", "title": "Commerce agents should verify before they promise"},
        ]}


if __name__ == "__main__":
    unittest.main()
