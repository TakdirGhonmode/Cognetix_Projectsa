import logging
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, Path as APIPath
from fastapi.responses import HTMLResponse, JSONResponse

import config
from api_client import AggregatedNewsFetcher
from categorizer import categorize_articles
from deduplicator import deduplicate_articles
from storage import NewsStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsAggregationService")

# Initialize FastAPI App & Storage
app = FastAPI(
    title="News Aggregation & Categorization Service",
    description="Python service integrating third-party news APIs, normalizing data, categorizing by topic, deduplicating, and persisting in SQLite.",
    version="1.0.0"
)

storage = NewsStorage()
fetcher = AggregatedNewsFetcher()

# ----------------------------------------------------
# Core REST Endpoints
# ----------------------------------------------------

@app.get("/health", tags=["Health & System"])
def get_health_status():
    """System health check and database statistics."""
    total_articles = storage.count_articles()
    report = storage.get_category_report()
    return {
        "status": "healthy",
        "service": "News Aggregation & Categorization Service",
        "total_stored_articles": total_articles,
        "active_providers": list(report.get("providers", {}).keys()),
        "configured_apis": {
            "NewsAPI": bool(config.NEWS_API_KEY),
            "GNews": bool(config.GNEWS_API_KEY)
        }
    }


@app.post("/news/fetch", tags=["Aggregation"])
def fetch_and_process_news():
    """
    Trigger news fetch from NewsAPI and GNews APIs.
    Flow: Fetch -> Normalize -> Deduplicate -> Categorize -> Persist in SQLite
    """
    try:
        # 1. Fetch raw normalized articles and logs
        raw_articles, logs = fetcher.fetch_all()

        # Save API logs
        for log in logs:
            storage.log_api_call(log)

        if not raw_articles:
            return {
                "message": "No articles retrieved from news sources.",
                "articles_fetched": 0,
                "articles_stored": 0,
                "api_logs": logs
            }

        # 2. Deduplicate articles
        unique_articles = deduplicate_articles(raw_articles)

        # 3. Categorize articles by keywords
        categorized_articles = categorize_articles(unique_articles)

        # 4. Save to SQLite database
        newly_inserted = storage.save_articles(categorized_articles)

        return {
            "message": "News fetch, deduplication, categorization, and storage completed successfully.",
            "total_articles_fetched": len(raw_articles),
            "unique_articles": len(unique_articles),
            "new_articles_saved": newly_inserted,
            "api_execution_logs": logs
        }

    except Exception as e:
        logger.error(f"Error during news aggregation pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Aggregation failure: {str(e)}")


@app.get("/news/category/{category}", tags=["News & Filter"])
def get_news_by_category(
    category: str = APIPath(..., description="Category name (e.g. Technology, Business, Sports, Politics, Health)")
):
    """
    Return structured JSON matching the exact required output format:
    {
      "category": "Technology",
      "total_articles": 15,
      "articles": [
        {
          "title": "...",
          "source": "...",
          "published_date": "...",
          "url": "..."
        }
      ]
    }
    """
    # Capitalize category properly for matching
    cat_title = category.strip().title()
    
    # If database is empty, auto-trigger initial fetch
    if storage.count_articles() == 0:
        logger.info("Database empty on first query. Triggering initial fetch...")
        fetch_and_process_news()

    raw_articles = storage.get_articles(category=cat_title, limit=100)

    # Format into standard 4-field clean article list
    formatted_articles = [
        {
            "title": art["title"],
            "source": art["source"],
            "published_date": art["published_date"],
            "url": art["url"]
        } for art in raw_articles
    ]

    return {
        "category": cat_title,
        "total_articles": len(formatted_articles),
        "articles": formatted_articles
    }


@app.get("/news", tags=["News & Filter"])
def get_all_news(
    category: Optional[str] = Query(None, description="Filter by category (Technology, Business, Sports, Politics, Health)"),
    limit: int = Query(50, ge=1, le=200, description="Max articles to return"),
    offset: int = Query(0, ge=0, description="Offset pagination")
):
    """Get stored news articles with optional category filter and pagination."""
    if storage.count_articles() == 0:
        fetch_and_process_news()

    articles = storage.get_articles(category=category, limit=limit, offset=offset)
    total = storage.count_articles(category=category)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "articles": articles
    }


@app.get("/news/search", tags=["News & Filter"])
def search_news(
    keyword: str = Query(..., min_length=2, description="Search keyword in title or description"),
    limit: int = Query(50, ge=1, le=100)
):
    """Search stored news articles by keyword."""
    articles = storage.get_articles(search=keyword, limit=limit)
    return {
        "keyword": keyword,
        "total_matches": len(articles),
        "articles": articles
    }


@app.get("/categories", tags=["Reports & Stats"])
def list_categories():
    """List supported news categories and their current article counts."""
    report = storage.get_category_report()
    categories_stats = {}
    
    for cat in config.CATEGORY_KEYWORDS.keys():
        categories_stats[cat] = report.get("categories", {}).get(cat, 0)
        
    return {
        "supported_categories": list(config.CATEGORY_KEYWORDS.keys()),
        "category_counts": categories_stats,
        "total_stored_articles": report.get("total_articles", 0)
    }


@app.get("/reports/category", tags=["Reports & Stats"])
def get_category_historical_report():
    """Historical breakdown report generated via Pandas."""
    report = storage.get_category_report()
    api_logs = storage.get_api_logs(limit=10)
    return {
        "report_type": "Historical Category Distribution",
        "summary": report,
        "recent_api_execution_logs": api_logs
    }


# ----------------------------------------------------
# Optional Simple Interactive Web Dashboard UI
# ----------------------------------------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page():
    """Simple interactive Web Dashboard for demonstrating the service visually."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>News Aggregation & Categorization Dashboard</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --accent-hover: #0284c7;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --border-color: #334155;
            --badge-bg: #0369a1;
        }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }
        h1 {
            margin: 0;
            font-size: 1.8rem;
            color: var(--accent);
        }
        .btn {
            background-color: var(--accent);
            color: #0f172a;
            border: none;
            padding: 10px 20px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover {
            background-color: var(--accent-hover);
            color: white;
        }
        .categories-bar {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .cat-btn {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
        }
        .cat-btn.active {
            background: var(--accent);
            color: #0f172a;
            font-weight: bold;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card h3 {
            margin: 0 0 10px 0;
            font-size: 1.1rem;
            line-height: 1.4;
        }
        .card p {
            color: var(--text-sub);
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        .meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-sub);
        }
        .badge {
            background-color: var(--badge-bg);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        .status-box {
            background: var(--card-bg);
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-family: monospace;
            color: #4ade80;
            border: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>📰 News Aggregation & Categorization Service</h1>
                <p style="color: var(--text-sub); margin: 4px 0 0 0;">Multi-API REST Aggregator | SQLite | Keyword Categorization</p>
            </div>
            <div>
                <button class="btn" onclick="fetchNews()">🔄 Fetch Fresh News</button>
                <a href="/docs" target="_blank" style="margin-left: 10px; color: var(--accent); text-decoration: none; font-weight: bold;">Swagger API Docs →</a>
            </div>
        </header>

        <div class="categories-bar" id="categoryBar">
            <button class="cat-btn active" onclick="filterCategory('All')">All</button>
            <button class="cat-btn" onclick="filterCategory('Technology')">Technology</button>
            <button class="cat-btn" onclick="filterCategory('Business')">Business</button>
            <button class="cat-btn" onclick="filterCategory('Sports')">Sports</button>
            <button class="cat-btn" onclick="filterCategory('Politics')">Politics</button>
            <button class="cat-btn" onclick="filterCategory('Health')">Health</button>
        </div>

        <div class="status-box" id="statusBox">System Ready. Select a category or fetch fresh news.</div>

        <div class="grid" id="newsGrid">
            <p style="color: var(--text-sub);">Loading articles...</p>
        </div>
    </div>

    <script>
        let currentCategory = 'All';

        async function loadNews() {
            const statusBox = document.getElementById('statusBox');
            const grid = document.getElementById('newsGrid');
            
            let url = currentCategory === 'All' ? '/news?limit=30' : `/news/category/${currentCategory}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                
                let articles = data.articles || [];
                statusBox.innerText = `Displaying ${articles.length} articles for '${currentCategory}'. Total Stored: ${data.total_articles || data.total || articles.length}`;

                if (articles.length === 0) {
                    grid.innerHTML = '<p style="color: var(--text-sub);">No articles found for this category.</p>';
                    return;
                }

                grid.innerHTML = articles.map(art => `
                    <div class="card">
                        <div>
                            <span class="badge">${art.category || currentCategory}</span>
                            <h3 style="margin-top: 8px;"><a href="${art.url}" target="_blank" style="color: white; text-decoration: none;">${art.title}</a></h3>
                            <p>${art.description || 'No description provided.'}</p>
                        </div>
                        <div class="meta">
                            <span>Source: <strong>${art.source}</strong></span>
                            <span>${art.published_date ? art.published_date.substring(0,10) : ''}</span>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                statusBox.innerText = `Error loading news: ${err.message}`;
            }
        }

        async function fetchNews() {
            const statusBox = document.getElementById('statusBox');
            statusBox.innerText = "Fetching fresh articles from NewsAPI & GNews...";
            try {
                const res = await fetch('/news/fetch', { method: 'POST' });
                const data = await res.json();
                statusBox.innerText = `${data.message} (${data.new_articles_saved} new saved)`;
                loadNews();
            } catch (err) {
                statusBox.innerText = `Fetch failed: ${err.message}`;
            }
        }

        function filterCategory(cat) {
            currentCategory = cat;
            document.querySelectorAll('.cat-btn').forEach(btn => {
                btn.classList.toggle('active', btn.innerText === cat);
            });
            loadNews();
        }

        loadNews();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
