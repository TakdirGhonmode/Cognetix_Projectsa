import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "").strip()

# Database Path
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "news.db"))

# API Configuration
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5  # seconds for exponential backoff

# Mandatory Categories & Keyword Map for News Categorization
CATEGORY_KEYWORDS = {
    "Technology": [
        "tech", "technology", "software", "hardware", "ai", "artificial intelligence",
        "cyber", "cybersecurity", "apple", "google", "microsoft", "nvidia", "meta",
        "app", "apps", "gadget", "chip", "semiconductor", "cloud", "data", "robot",
        "robotics", "algorithm", "startup", "smartphone", "iphone", "android", "internet"
    ],
    "Business": [
        "business", "stock", "stocks", "market", "markets", "economy", "economic",
        "finance", "financial", "company", "trade", "trading", "bank", "banking",
        "dollar", "inflation", "ceo", "revenue", "profit", "quarterly", "investor",
        "investment", "shares", "commerce", "fund", "equity", "wall street"
    ],
    "Sports": [
        "sports", "sport", "football", "basketball", "nfl", "nba", "soccer",
        "tennis", "golf", "olympics", "score", "league", "match", "tournament",
        "championship", "stadium", "athlete", "coach", "player", "cup", "game",
        "team", "cricket", "baseball"
    ],
    "Politics": [
        "politics", "political", "election", "elections", "government", "president",
        "senate", "senator", "congress", "law", "policy", "vote", "voters",
        "minister", "parliament", "diplomacy", "white house", "campaign", "court",
        "supreme court", "governor", "republican", "democrat", "sanction"
    ],
    "Health": [
        "health", "healthy", "vaccine", "vaccination", "doctor", "hospital",
        "medicine", "medical", "cancer", "disease", "mental health", "fda",
        "wellness", "virus", "infection", "patient", "clinical", "pharma",
        "pharmaceutical", "drug", "treatment", "fitness", "nutrition"
    ]
}

# Fallback default category
DEFAULT_CATEGORY = "General"
