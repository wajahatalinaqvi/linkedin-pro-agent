"""Action summaries never mark failed runs as published."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from actions_summary import format_summary

class ActionSummaryTests(unittest.TestCase):
    def test_failed_publish_never_claims_published(self):
        summary = format_summary("publish", "", "failure")
        self.assertIn("needs attention", summary)
        self.assertNotIn("publication recorded", summary)

    def test_empty_daily_output_is_not_published(self):
        summary = format_summary("daily", "", "success")
        self.assertIn("no new draft", summary)

if __name__ == "__main__":
    unittest.main()
