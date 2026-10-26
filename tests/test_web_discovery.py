"""Broad discovery must never pass a news redirect or unverified publisher to Gemini."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from xml.sax.saxutils import escape
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from web_discovery import _canonical_bing_url, _source_url, parse_news_rss, discover_web_stories

NOW = datetime(2026,10,26,11,tzinfo=timezone.utc)

class WebDiscoveryTests(unittest.TestCase):
    def test_bing_url_unwrapped(self):
        link = "https://www.bing.com/news/apiclick.aspx?foo=x&url=https%3A%2F%2Fshopify.dev%2Fchangelog%2Fnew-api"
        self.assertEqual(_source_url(link, provider="bing"), "https://shopify.dev/changelog/new-api")

    def test_external_and_google_links_never_become_authoritative(self):
        self.assertEqual(_source_url("https://news.google.com/rss/articles/CBMi",provider="google"), "")
        self.assertEqual(_source_url("https://example.org/opinion",provider="bing"), "")
        self.assertEqual(_source_url("http://shopify.dev/changelog/test",provider="bing"), "")

    def test_search_crawls_count_only_recent_originals(self):
        data = """<rss><channel>
        <item><title>Developers get a new Shopify API</title><link>https://shopify.dev/changelog/test</link><pubDate>Mon, 26 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>Random coverage</title><link>https://example.org/blog</link><pubDate>Mon, 26 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>Old Shopify item</title><link>https://shopify.dev/changelog/old</link><pubDate>Tue, 20 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        items, leads = parse_news_rss(data.encode(), "Shopify", "bing", NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(leads,1)

    @patch("web_discovery._rss_search")
    @patch("web_discovery._brave_search")
    def test_multi_index_with_no_key_remains_available(self,brave,rss):
        rss.return_value = ([{
            "topic":"Shopify API update", "source_url":"https://shopify.dev/changelog/test",
            "category":"Shopify", "published": NOW, "discovered_via":"bing-news"
        }],0)
        with patch.dict("os.environ", {"BRAVE_SEARCH_API_KEY": ""}):
            results, stats = discover_web_stories(NOW)
        self.assertEqual(len(results),1)
        self.assertGreater(stats["successful_queries"],10)
        self.assertFalse(stats["brave_enabled"])
        brave.assert_not_called()

if __name__ == "__main__":
    unittest.main()
