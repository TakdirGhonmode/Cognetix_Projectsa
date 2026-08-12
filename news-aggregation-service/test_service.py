import os
import tempfile
import unittest
from fastapi.testclient import TestClient

import config
from normalizer import normalize_newsapi_article, normalize_gnews_article, clean_text, parse_date
from categorizer import categorize_text, categorize_article
from deduplicator import deduplicate_articles, normalize_url, normalize_title
from storage import NewsStorage
from main import app

class TestNewsAggregationService(unittest.TestCase):

    def setUp(self):
        """Set up temporary SQLite database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.storage = NewsStorage(db_path=self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        """Clean up temporary database."""
        self.temp_db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass


    # ----------------------------------------------------
    # 1. Normalization Tests
    # ----------------------------------------------------
    def test_clean_text(self):
        html_input = "<h1>Title</h1><p>This is <b>bold</b> &amp; clean.</p>"
        cleaned = clean_text(html_input)
        self.assertNotIn("<h1>", cleaned)
        self.assertNotIn("<b>", cleaned)
        self.assertIn("Title This is bold &amp; clean.", cleaned)

    def test_parse_date(self):
        iso_date = "2026-08-12T17:00:00Z"
        parsed = parse_date(iso_date)
        self.assertEqual(parsed, "2026-08-12 17:00:00Z")

    def test_normalize_newsapi_article(self):
        raw = {
            "title": "Google Unveils Quantum AI Chip",
            "description": "Tech giant introduces next-gen processor.",
            "source": {"name": "TechCrunch"},
            "publishedAt": "2026-08-12T12:00:00Z",
            "url": "https://techcrunch.com/quantum-chip"
        }
        normalized = normalize_newsapi_article(raw)
        self.assertEqual(normalized["title"], "Google Unveils Quantum AI Chip")
        self.assertEqual(normalized["source"], "TechCrunch")
        self.assertEqual(normalized["provider"], "NewsAPI")
        self.assertTrue(len(normalized["article_hash"]) > 10)

    def test_normalize_gnews_article(self):
        raw = {
            "title": "Stock Market Surge Boosts Wall Street",
            "description": "Investors celebrate market gains.",
            "source": {"name": "Reuters"},
            "publishedAt": "2026-08-12T10:00:00Z",
            "url": "https://reuters.com/markets"
        }
        normalized = normalize_gnews_article(raw)
        self.assertEqual(normalized["title"], "Stock Market Surge Boosts Wall Street")
        self.assertEqual(normalized["source"], "Reuters")
        self.assertEqual(normalized["provider"], "GNews")

    # ----------------------------------------------------
    # 2. Categorization Tests
    # ----------------------------------------------------
    def test_categorization_topics(self):
        # Technology
        self.assertEqual(categorize_text("Apple releases new iPhone AI software", ""), "Technology")
        # Business
        self.assertEqual(categorize_text("Wall Street stock market gains revenue", ""), "Business")
        # Sports
        self.assertEqual(categorize_text("NFL championship football game score", ""), "Sports")
        # Politics
        self.assertEqual(categorize_text("Senate election policy vote and congress", ""), "Politics")
        # Health
        self.assertEqual(categorize_text("FDA approves new vaccine for hospital patients", ""), "Health")

    # ----------------------------------------------------
    # 3. Deduplication Tests
    # ----------------------------------------------------
    def test_deduplicate_urls(self):
        articles = [
            {"title": "Article 1", "url": "https://example.com/news?utm_source=twitter"},
            {"title": "Article 1 Copy", "url": "https://example.com/news"}
        ]
        unique = deduplicate_articles(articles)
        self.assertEqual(len(unique), 1)

    def test_deduplicate_titles(self):
        articles = [
            {"title": "Breaking News: Major Election Results!", "url": "https://siteA.com/news"},
            {"title": "breaking news major election results", "url": "https://siteB.com/news"}
        ]
        unique = deduplicate_articles(articles)
        self.assertEqual(len(unique), 1)

    # ----------------------------------------------------
    # 4. Storage & Persistence Tests
    # ----------------------------------------------------
    def test_storage_save_and_retrieve(self):
        articles = [
            {
                "article_hash": "hash_123",
                "title": "Tech AI Breakthrough",
                "description": "Software update details",
                "source": "TechNews",
                "category": "Technology",
                "published_date": "2026-08-12T10:00:00Z",
                "url": "https://technews.com/ai",
                "provider": "NewsAPI",
                "fetched_at": "2026-08-12T12:00:00Z"
            }
        ]

        inserted = self.storage.save_articles(articles)
        self.assertEqual(inserted, 1)

        # Duplicate insertion attempt should be ignored
        inserted_dup = self.storage.save_articles(articles)
        self.assertEqual(inserted_dup, 0)

        retrieved = self.storage.get_articles(category="Technology")
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0]["title"], "Tech AI Breakthrough")

    # ----------------------------------------------------
    # 5. FastAPI Endpoints Tests
    # ----------------------------------------------------
    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_category_structured_json_endpoint(self):
        response = self.client.get("/news/category/Technology")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify exact required JSON schema
        self.assertIn("category", data)
        self.assertIn("total_articles", data)
        self.assertIn("articles", data)
        self.assertEqual(data["category"], "Technology")
        self.assertIsInstance(data["articles"], list)


if __name__ == "__main__":
    unittest.main()
