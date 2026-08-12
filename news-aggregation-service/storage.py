import sqlite3
import logging
from datetime import datetime, timezone
import pandas as pd
import config

logger = logging.getLogger("NewsStorage")

class NewsStorage:
    """SQLite Database Manager for persisting news articles and API call logs."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a sqlite3 Connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create required sqlite tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_hash TEXT UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    category TEXT,
                    published_date TEXT,
                    url TEXT,
                    provider TEXT,
                    fetched_at TEXT
                )
            """)

            # 2. API Execution Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    status_code INTEGER,
                    articles_count INTEGER,
                    error_message TEXT,
                    timestamp TEXT
                )
            """)

            conn.commit()
            logger.info(f"Database initialized at '{self.db_path}'.")

    def save_articles(self, articles: list) -> int:
        """
        Save normalized articles to database.
        Uses INSERT OR IGNORE to prevent duplicate hash entries and preserve history.
        Returns count of newly inserted articles.
        """
        if not articles:
            return 0

        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for art in articles:
                cursor.execute("""
                    INSERT OR IGNORE INTO articles 
                    (article_hash, title, description, source, category, published_date, url, provider, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    art.get("article_hash"),
                    art.get("title"),
                    art.get("description"),
                    art.get("source"),
                    art.get("category"),
                    art.get("published_date"),
                    art.get("url"),
                    art.get("provider"),
                    art.get("fetched_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()

        logger.info(f"Saved {inserted_count} new articles to database.")
        return inserted_count

    def log_api_call(self, log_dict: dict):
        """Save API call execution log."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_logs (provider, status_code, articles_count, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                log_dict.get("provider"),
                log_dict.get("status_code"),
                log_dict.get("articles_count"),
                log_dict.get("error"),
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
            ))
            conn.commit()

    def get_articles(self, category: str = None, search: str = None, limit: int = 50, offset: int = 0) -> list:
        """Query articles from database with optional category and search filters."""
        query = "SELECT * FROM articles WHERE 1=1"
        params = []

        if category and category.lower() != "all":
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)

        if search:
            query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ?)"
            search_param = f"%{search.lower()}%"
            params.extend([search_param, search_param])

        query += " ORDER BY published_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def count_articles(self, category: str = None) -> int:
        """Count total stored articles for a category or overall."""
        query = "SELECT COUNT(*) FROM articles"
        params = []
        if category and category.lower() != "all":
            query += " WHERE LOWER(category) = LOWER(?)"
            params.append(category)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_category_report(self) -> dict:
        """
        Generate category distribution and historical stats report using Pandas.
        Fulfills requirement for Pandas analytical report.
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT category, provider, published_date FROM articles", conn)

        if df.empty:
            return {"total_articles": 0, "categories": {}, "providers": {}}

        category_counts = df["category"].value_counts().to_dict()
        provider_counts = df["provider"].value_counts().to_dict()

        return {
            "total_articles": len(df),
            "categories": category_counts,
            "providers": provider_counts
        }

    def get_api_logs(self, limit: int = 20) -> list:
        """Retrieve recent API execution logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM api_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "provider": r[1],
                    "status_code": r[2],
                    "articles_count": r[3],
                    "error_message": r[4],
                    "timestamp": r[5]
                } for r in rows
            ]

