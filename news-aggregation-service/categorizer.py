import re
import config

def categorize_text(title: str, description: str) -> str:
    """
    Categorize text using rule-based keyword matching.
    Scour title and description for keywords matching the 5 target categories:
    Technology, Business, Sports, Politics, Health.
    """
    combined_text = f"{title or ''} {description or ''}".lower()

    scores = {category: 0 for category in config.CATEGORY_KEYWORDS}

    # Match tokenized words against category keyword lists
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        for kw in keywords:
            # Word boundary matching for exact or multi-word keyword presence
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = len(re.findall(pattern, combined_text))
            
            # Title matches count for double weight
            title_matches = len(re.findall(pattern, (title or '').lower()))
            
            scores[category] += matches + title_matches

    # Find category with maximum score
    max_score = 0
    best_category = config.DEFAULT_CATEGORY

    for category, score in scores.items():
        if score > max_score:
            max_score = score
            best_category = category

    return best_category

def categorize_article(article: dict) -> dict:
    """Categorize an individual article dict and update its 'category' field."""
    title = article.get("title", "")
    description = article.get("description", "")
    article["category"] = categorize_text(title, description)
    return article

def categorize_articles(articles: list) -> list:
    """Categorize a batch list of normalized articles."""
    return [categorize_article(art) for art in articles]
