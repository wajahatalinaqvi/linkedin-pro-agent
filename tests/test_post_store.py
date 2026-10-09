"""Safety regression tests for saved LinkedIn draft management."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import post_store


class DraftStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(post_store, "ROOT", self.root),
            patch.object(post_store, "LATEST", self.root / "queue/latest.json"),
            patch.object(post_store, "DRAFTS", self.root / "queue/drafts"),
            patch.object(post_store, "HISTORY", self.root / "data/history.json"),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()

    def make_post(self, identifier, status="ready"):
        return {"id": identifier, "status": status, "topic": identifier,
                "caption": "Verified developer update", "source_url": "https://example.com/official",
                "format": "text"}

    def test_create_and_select_preserves_previous_ready_draft(self):
        a = self.make_post("first")
        b = self.make_post("second")
        post_store.save_json(post_store.LATEST, a)
        post_store.create_draft(b, select=True)
        self.assertEqual(post_store.load_json(post_store.LATEST)["id"], "second")
        self.assertEqual(post_store.load_json(post_store.draft_path("first"))["id"], "first")
        self.assertEqual(post_store.load_json(post_store.draft_path("second"))["id"], "second")

    def test_selected_draft_updates_matching_latest_only(self):
        post_store.create_draft(self.make_post("a"), select=True)
        post_store.create_draft(self.make_post("b"))
        post, path = post_store.load_post("b")
        post["status"] = "published"
        post_store.save_post(post, path)
        self.assertEqual(post_store.load_json(post_store.LATEST)["status"], "ready")
        self.assertEqual(post_store.load_json(post_store.draft_path("b"))["status"], "published")

    def test_matching_latest_updates_with_saved_draft(self):
        post_store.create_draft(self.make_post("a"), select=True)
        post, path = post_store.load_post("a")
        post["status"] = "published"
        post_store.save_post(post, path)
        self.assertEqual(post_store.load_json(post_store.LATEST)["status"], "published")

    def test_prevents_duplicate_id(self):
        post_store.create_draft(self.make_post("a"))
        with self.assertRaises(ValueError):
            post_store.create_draft(self.make_post("a"))

    def test_prevents_reusing_published_history_id(self):
        post_store.save_json(post_store.HISTORY, [{"id": "old"}])
        with self.assertRaises(ValueError):
            post_store.create_draft(self.make_post("old"))

    def test_rejects_path_traversal(self):
        for value in ("../file", "../../etc/passwd", "", ".", "foo/bar", "a b"):
            with self.assertRaises(ValueError):
                post_store.draft_path(value)


if __name__ == "__main__":
    unittest.main()
