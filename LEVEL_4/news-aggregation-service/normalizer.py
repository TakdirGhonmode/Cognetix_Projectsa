import re
import hashlib
from datetime import datetime, timezone

def clean_text(text: str) -> str:
    """Strip HTML tags and normalize extra whitespace."""
    if not text:
        return ""
    # Replace HTML tags with space to preserve separation between elements
    cleaned = re.sub(r'<[^>]+>', ' ', str(text))
    # Replace multiple spaces/newlines with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def parse_date(date_str: str) -> str:
    """Normalize date strings into ISO 8601 format (UTC)."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    # Common date formats return by various APIs
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S GMT"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%SZ")
        except ValueError:
            continue

    # Fallback to current time if unparseable
    return date_str.strip()

def generate_article_hash(url: str, title: str) -> str:
    """Generate a unique SHA-256 hash for an article based on canonical URL or title."""
    clean_url = re.sub(r'https?://(www\.)?', '', (url or "").strip().lower())
    clean_title = re.sub(r'[\W_]+', '', (title or "").strip().lower())
    identifier = clean_url if len(clean_url) > 10 else clean_title
    return hashlib.sha256(identifier.encode('utf-8')).hexdigest()

def normalize_newsapi_article(raw_item: dict) -> dict:
    """
    Normalize raw article JSON from NewsAPI.org.
    Expected fields from NewsAPI: title, description, source.name, publishedAt, url
    """
    title = clean_text(raw_item.get("title", ""))
    description = clean_text(raw_item.get("description", ""))
    source_info = raw_item.get("source") or {}
    source_name = clean_text(source_info.get("name", "NewsAPI Source")) if isinstance(source_info, dict) else "NewsAPI Source"
    published_date = parse_date(raw_item.get("publishedAt", ""))
    url = (raw_item.get("url") or "").strip()

    return {
        "title": title or "Untitled Article",
        "description": description or "No description available.",
        "source": source_name or "NewsAPI",
        "category": "Uncategorized",  # Will be set by categorizer
        "published_date": published_date,
        "url": url,
        "provider": "NewsAPI",
        "article_hash": generate_article_hash(url, title),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    }

def normalize_gnews_article(raw_item: dict) -> dict:
    """
    Normalize raw article JSON from GNews.io.
    Expected fields from GNews: title, description, source.name, publishedAt, url
    """
    title = clean_text(raw_item.get("title", ""))
    description = clean_text(raw_item.get("description", ""))
    source_info = raw_item.get("source") or {}
    source_name = clean_text(source_info.get("name", "GNews Source")) if isinstance(source_info, dict) else "GNews Source"
    published_date = parse_date(raw_item.get("publishedAt", ""))
    url = (raw_item.get("url") or "").strip()

    return {
        "title": title or "Untitled Article",
        "description": description or "No description available.",
        "source": source_name or "GNews",
        "category": "Uncategorized",  # Will be set by categorizer
        "published_date": published_date,
        "url": url,
        "provider": "GNews",
        "article_hash": generate_article_hash(url, title),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    }
