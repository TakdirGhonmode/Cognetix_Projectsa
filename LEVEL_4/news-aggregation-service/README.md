# News Aggregation & Categorization Service

A Python-based REST API service that integrates multiple third-party news APIs (NewsAPI, GNews), normalizes heterogeneous responses, categorizes news into 5 core topics using rule-based keyword matching, removes duplicates, handles API rate-limits, and persists structured historical news into a SQLite database (`news.db`).

---

## 📌 Project Objective & Flowchart

The goal of this service is to aggregate raw news content from multiple third-party APIs, clean and normalize fields into a unified schema, classify articles, eliminate duplicates, handle rate limits gracefully, and present categorized news feeds via RESTful API endpoints.

```
Configure API Keys (.env)
        ↓
Fetch News from Multiple APIs (NewsAPI & GNews)
        ↓
Normalize News Data (Unified Schema)
        ↓
Remove Duplicates (deduplicator.py)
        ↓
Categorize News by Keywords (Technology, Business, Sports, Politics, Health)
        ↓
Handle API Errors & Rate Limits (Backoff Retries, Graceful Failover)
        ↓
Store Aggregated News in SQLite (news.db)
        ↓
Return Structured JSON REST API Response
```

---

## 🛠️ Technology Stack & Libraries

- **Language**: Python 3.10+
- **REST API Framework**: FastAPI & Uvicorn
- **HTTP Client**: Requests with urllib3 retry adapters
- **Data Analytics & Reporting**: Pandas
- **Storage**: SQLite3 (`news.db`)
- **Environment Management**: Python-Dotenv

---

## 📂 Project Structure

```
news-aggregation-service/
│
├── .venv/               # Python virtual environment
├── .env                 # API keys and secret configuration
├── .env.example         # Template for environment configuration
├── .gitignore           # Git ignore file (excludes .env, news.db, .venv)
├── requirements.txt     # Python dependency specifications
├── README.md            # Comprehensive project documentation
│
├── config.py            # API key loader, endpoints, category keyword mappings
├── api_client.py        # NewsAPI, GNews, retry adapters, & fallback mock client
├── normalizer.py        # Standardized Article data structure & ISO date parsing
├── categorizer.py       # Rule-based keyword matching classification engine
├── deduplicator.py      # Duplicate detection (URL, Title & Jaccard similarity)
├── storage.py           # SQLite database persistence layer & Pandas reporting
├── main.py              # FastAPI REST endpoints & interactive dashboard UI
├── test_service.py      # Unit test suite
│
└── news.db              # SQLite database (auto-created on startup)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Verify Python version (3.10 or higher):
```bash
python --version
```

### 2. Environment Setup
Create and activate virtual environment (optional but recommended):
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and add your free API keys from [NewsAPI.org](https://newsapi.org) and [GNews.io](https://gnews.io):
```env
NEWS_API_KEY=your_newsapi_key_here
GNEWS_API_KEY=your_gnews_key_here
```
> *Note: If no API keys are provided in `.env`, the service automatically falls back to an internal `MockNewsClient` so you can test and demonstrate all features immediately.*

### 5. Run the Application
Start the service using `uvicorn`:
```bash
uvicorn main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## 📡 REST API Endpoints

### 1. Get Categorized News (Required Structured JSON)
- **Endpoint**: `GET /news/category/{category}`
- **Parameters**: `category` = `Technology`, `Business`, `Sports`, `Politics`, `Health`
- **Example Response**:
```json
{
  "category": "Technology",
  "total_articles": 15,
  "articles": [
    {
      "title": "NVIDIA Unveils Next-Gen AI Microchips for Cloud Data Centers",
      "source": "TechCrunch",
      "published_date": "2026-08-12 10:00:00Z",
      "url": "https://techcrunch.com/sample/nvidia-ai-chip-2026"
    }
  ]
}
```

### 2. Trigger Fresh News Aggregation
- **Endpoint**: `POST /news/fetch`
- **Description**: Triggers live fetching from NewsAPI and GNews, normalizes data, deduplicates, categorizes, and persists new articles to SQLite (`news.db`).

### 3. Get All News
- **Endpoint**: `GET /news?category=Business&limit=50`
- **Description**: Returns normalized articles stored in database with optional category filtering and pagination.

### 4. Search News by Keyword
- **Endpoint**: `GET /news/search?keyword=election`
- **Description**: Performs full-text keyword search across stored titles and descriptions.

### 5. List Category Statistics
- **Endpoint**: `GET /categories`
- **Description**: Returns list of all supported categories and total article counts per topic.

### 6. Category Breakdown & Historical Report (Pandas)
- **Endpoint**: `GET /reports/category`
- **Description**: Analytics report generated using Pandas showing category distribution and API call logs.

### 7. System Health Check
- **Endpoint**: `GET /health`
- **Description**: Status check verifying database health and API provider connectivity.

### 8. Interactive Dashboard & OpenAPI Docs
- **Web Dashboard**: Open `http://127.0.0.1:8000/` in browser.
- **Interactive Swagger Docs**: Open `http://127.0.0.1:8000/docs`.

---

## 🗄️ Database & Storage Architecture (`news.db`)

The SQLite database contains two main tables:
1. `articles`:
   - `id`: Auto-incrementing primary key
   - `article_hash`: SHA-256 unique identifier generated from canonical URL/title
   - `title`: Article title
   - `description`: Article summary/description
   - `source`: Publisher/source name
   - `category`: Assigned topic category
   - `published_date`: ISO-8601 string date
   - `url`: Canonical article URL
   - `provider`: Origin API (`NewsAPI` or `GNews`)
   - `fetched_at`: Fetch timestamp

2. `api_logs`:
   - Records API status codes, execution timestamps, fetched counts, and rate-limit warnings.

> *Note: Duplicate articles are avoided using `INSERT OR IGNORE INTO articles`, ensuring historical data is preserved across application runs.*

---

## ⚙️ API Rate-Limit & Resilience Strategy

- **HTTP 429 Handling**: Automatically detects `429 Too Many Requests` status codes from news APIs.
- **Exponential Backoff**: Requests session uses `urllib3.util.Retry` adapters to retry transient network errors (HTTP 429, 500, 502, 503, 504) with backoff delays.
- **Graceful Failover**: If one API provider (e.g. NewsAPI) experiences an outage or key error, the service logs the error and continues processing articles from GNews.

---

## 🧪 Running Automated Unit Tests

Run the complete test suite using Python `unittest`:
```bash
python -m unittest test_service.py
```
This tests text normalization, date parsing, keyword categorization across all 5 topics, URL/Title deduplication, SQLite persistence, and FastAPI REST endpoint responses.
