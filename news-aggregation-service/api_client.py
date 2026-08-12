import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from normalizer import normalize_newsapi_article, normalize_gnews_article

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsApiClient")

def get_resilient_session() -> requests.Session:
    """Create a requests Session equipped with automatic HTTP retry & backoff strategy."""
    session = requests.Session()
    retries = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class NewsAPIClient:
    """Client for NewsAPI (newsapi.org)."""
    BASE_URL = "https://newsapi.org/v2/top-headlines"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.NEWS_API_KEY
        self.session = get_resilient_session()

    def fetch_articles(self, query: str = "news", country: str = "us", category: str = None) -> tuple[list, dict]:
        """
        Fetch articles from NewsAPI.
        Returns tuple: (list of raw article dicts, log dict)
        """
        if not self.api_key:
            logger.warning("NewsAPI key is missing.")
            return [], {"provider": "NewsAPI", "status_code": 401, "articles_count": 0, "error": "API key missing"}

        params = {
            "apiKey": self.api_key,
            "language": "en",
            "pageSize": 20
        }
        if category:
            params["category"] = category.lower()
        else:
            params["q"] = query

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            
            if response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded (HTTP 429).")
                return [], {"provider": "NewsAPI", "status_code": 429, "articles_count": 0, "error": "Rate limit exceeded (429)"}
            
            response.raise_for_status()
            data = response.json()
            raw_articles = data.get("articles", [])
            normalized = [normalize_newsapi_article(art) for art in raw_articles if art.get("title")]
            
            return normalized, {"provider": "NewsAPI", "status_code": 200, "articles_count": len(normalized), "error": None}

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 500
            msg = f"NewsAPI HTTP Error {status_code}: {str(e)}"
            logger.error(msg)
            return [], {"provider": "NewsAPI", "status_code": status_code, "articles_count": 0, "error": msg}
        except requests.exceptions.RequestException as e:
            msg = f"NewsAPI Connection Error: {str(e)}"
            logger.error(msg)
            return [], {"provider": "NewsAPI", "status_code": 500, "articles_count": 0, "error": msg}


class GNewsClient:
    """Client for GNews (gnews.io)."""
    BASE_URL = "https://gnews.io/api/v4/top-headlines"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.GNEWS_API_KEY
        self.session = get_resilient_session()

    def fetch_articles(self, query: str = "general", category: str = None) -> tuple[list, dict]:
        """
        Fetch articles from GNews API.
        Returns tuple: (list of normalized article dicts, log dict)
        """
        if not self.api_key:
            logger.warning("GNews API key is missing.")
            return [], {"provider": "GNews", "status_code": 401, "articles_count": 0, "error": "API key missing"}

        params = {
            "token": self.api_key,
            "lang": "en",
            "max": 20
        }
        if category:
            params["category"] = category.lower()
        else:
            params["q"] = query

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=config.REQUEST_TIMEOUT)

            if response.status_code == 429:
                logger.error("GNews rate limit exceeded (HTTP 429).")
                return [], {"provider": "GNews", "status_code": 429, "articles_count": 0, "error": "Rate limit exceeded (429)"}

            response.raise_for_status()
            data = response.json()
            raw_articles = data.get("articles", [])
            normalized = [normalize_gnews_article(art) for art in raw_articles if art.get("title")]

            return normalized, {"provider": "GNews", "status_code": 200, "articles_count": len(normalized), "error": None}

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 500
            msg = f"GNews HTTP Error {status_code}: {str(e)}"
            logger.error(msg)
            return [], {"provider": "GNews", "status_code": status_code, "articles_count": 0, "error": msg}
        except requests.exceptions.RequestException as e:
            msg = f"GNews Connection Error: {str(e)}"
            logger.error(msg)
            return [], {"provider": "GNews", "status_code": 500, "articles_count": 0, "error": msg}


class MockNewsClient:
    """Optional Fallback Mock News Client for testing when real API keys are missing."""

    def fetch_articles(self) -> tuple[list, dict]:
        logger.info("Generating realistic mock news data for keyless demonstration...")
        mock_data = [
            {
                "title": "NVIDIA Unveils Next-Gen AI Microchips for Cloud Data Centers",
                "description": "Tech giant NVIDIA announced groundbreaking AI hardware designed to boost neural network training speeds by 4x.",
                "source": "TechCrunch",
                "category": "Technology",
                "published_date": "2026-08-12T10:00:00Z",
                "url": "https://techcrunch.com/sample/nvidia-ai-chip-2026",
                "provider": "MockProvider",
                "article_hash": "mock_hash_tech_1",
                "fetched_at": "2026-08-12T12:00:00Z"
            },
            {
                "title": "Global Stock Markets Surge Following Inflation Drop Announcement",
                "description": "Wall Street shares rose sharply today after central banks reported a significant cooling of inflation rates.",
                "source": "Bloomberg",
                "category": "Business",
                "published_date": "2026-08-12T09:30:00Z",
                "url": "https://bloomberg.com/sample/markets-surge-2026",
                "provider": "MockProvider",
                "article_hash": "mock_hash_biz_1",
                "fetched_at": "2026-08-12T12:00:00Z"
            },
            {
                "title": "Champions League Finals: Thrilling Match Ends in Sudden Death Penalty Shootout",
                "description": "An intense football match ended dramatically as the visiting team claimed the European championship cup.",
                "source": "ESPN",
                "category": "Sports",
                "published_date": "2026-08-12T08:15:00Z",
                "url": "https://espn.com/sample/champions-league-finals",
                "provider": "MockProvider",
                "article_hash": "mock_hash_sports_1",
                "fetched_at": "2026-08-12T12:00:00Z"
            },
            {
                "title": "Parliament Approves New Healthcare Reform Law After Heated Debate",
                "description": "Lawmakers voted to pass new legislation aimed at expanding public hospital funding and medical coverage.",
                "source": "Reuters",
                "category": "Politics",
                "published_date": "2026-08-12T07:45:00Z",
                "url": "https://reuters.com/sample/parliament-healthcare-law",
                "provider": "MockProvider",
                "article_hash": "mock_hash_pol_1",
                "fetched_at": "2026-08-12T12:00:00Z"
            },
            {
                "title": "FDA Approves Breakthrough Cancer Vaccine for Clinical Trials",
                "description": "Medical researchers celebrate as the FDA grants approval for advanced mRNA vaccine testing against rare tumors.",
                "source": "Medical News Today",
                "category": "Health",
                "published_date": "2026-08-12T06:20:00Z",
                "url": "https://medicalnewstoday.com/sample/fda-cancer-vaccine",
                "provider": "MockProvider",
                "article_hash": "mock_hash_health_1",
                "fetched_at": "2026-08-12T12:00:00Z"
            },
            {
                "title": "Apple Prepares Software Update for iPhone Cyber Security Vulnerabilities",
                "description": "Apple engineers released an urgent software patch addressing critical system vulnerabilities across mobile devices.",
                "source": "The Verge",
                "category": "Technology",
                "published_date": "2026-08-12T11:10:00Z",
                "url": "https://theverge.com/sample/apple-security-patch",
                "provider": "MockProvider",
                "article_hash": "mock_hash_tech_2",
                "fetched_at": "2026-08-12T12:00:00Z"
            }
        ]
        return mock_data, {"provider": "MockProvider", "status_code": 200, "articles_count": len(mock_data), "error": None}


class AggregatedNewsFetcher:
    """Coordinates fetching from primary providers (NewsAPI and GNews) with graceful failover."""

    def __init__(self):
        self.news_api_client = NewsAPIClient()
        self.gnews_client = GNewsClient()
        self.mock_client = MockNewsClient()

    def fetch_all(self) -> tuple[list, list]:
        """
        Fetch news from all configured news APIs.
        Returns: (all_normalized_articles, list_of_logs)
        """
        all_articles = []
        logs = []

        # 1. Fetch from NewsAPI
        newsapi_articles, log1 = self.news_api_client.fetch_articles()
        all_articles.extend(newsapi_articles)
        logs.append(log1)

        # 2. Fetch from GNews
        gnews_articles, log2 = self.gnews_client.fetch_articles()
        all_articles.extend(gnews_articles)
        logs.append(log2)

        # 3. Optional fallback: If neither API key returned data, use MockNewsClient for demo
        if not all_articles:
            logger.info("No articles fetched from live APIs (missing/invalid keys). Falling back to MockNewsClient...")
            mock_articles, log_mock = self.mock_client.fetch_articles()
            all_articles.extend(mock_articles)
            logs.append(log_mock)

        return all_articles, logs
