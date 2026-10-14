from __future__ import annotations
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from content_priority import today_local, local_date, manual_requests_on_day, automatic_ready_on_day
from post_store import create_draft, select_draft, load_json
import post_store
from unittest.mock import patch

class PriorityTests(unittest.TestCase):
    def test_pakistan_date(self):
        self.assertEqual(local_date("2026-10-13T20:01:00Z"), "2026-10-14")
        self.assertEqual(today_local(datetime(2026, 10, 14, 6, 0, tzinfo=timezone.utc)), "2026-10-14")

    def test_requested_topic_reserves_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "manual.json").write_text(json.dumps({
                "priority":"user_requested","requested_at":"2026-10-13T21:20:00Z","status":"needs_source"
            }))
            self.assertEqual(len(manual_requests_on_day(path,"2026-10-14")),1)
            self.assertEqual(len(manual_requests_on_day(path,"2026-10-13")),0)

    def test_only_one_automatic_draft_per_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "auto.json").write_text(json.dumps({
                "origin":"automatic","created_at":"2026-10-14T06:00:00Z"
            }))
            self.assertTrue(automatic_ready_on_day(path,"2026-10-14"))
            self.assertFalse(automatic_ready_on_day(path,"2026-10-15"))

    def test_manual_overrides_automatic_preserving_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(post_store,"ROOT",root), patch.object(post_store,"LATEST",root/"queue/latest.json"), patch.object(post_store,"DRAFTS",root/"queue/drafts"), patch.object(post_store,"HISTORY",root/"data/history.json"):
                base = {"status":"ready","caption":"Source-verified story","source_url":"https://shopify.dev/changelog","format":"text"}
                create_draft({**base,"id":"auto-2026-10-14-a","origin":"automatic"}, select=True)
                create_draft({**base,"id":"manual-topic"},select=False)
                select_draft("manual-topic")
                self.assertEqual(load_json(post_store.LATEST)["id"],"manual-topic")
                self.assertEqual(load_json(post_store.draft_path("auto-2026-10-14-a"))["status"],"ready")

if __name__=="__main__":
    unittest.main()
