import re
from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    """Canonicalize URL by removing query parameters, scheme, and trailing slashes."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    # Canonical host + path without query parameters or anchors
    canonical = f"{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
    canonical = re.sub(r'^www\.', '', canonical)
    return canonical

def normalize_title(title: str) -> str:
    """Normalize title by lowercasing and keeping only alphanumeric characters."""
    if not title:
        return ""
    return re.sub(r'[\W_]+', '', title.strip().lower())

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate token-level Jaccard similarity between two strings."""
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)

def deduplicate_articles(articles: list, similarity_threshold: float = 0.80) -> list:
    """
    Filter duplicate articles based on:
    1. Canonical URL matching
    2. Normalized title exact matching
    3. Token Jaccard similarity threshold
    """
    seen_urls = set()
    seen_titles = set()
    unique_articles = []

    for article in articles:
        url = article.get("url", "")
        title = article.get("title", "")
        
        norm_url = normalize_url(url)
        norm_title = normalize_title(title)

        # 1. Direct URL match check
        if norm_url and norm_url in seen_urls:
            continue

        # 2. Direct title match check
        if norm_title and norm_title in seen_titles:
            continue

        # 3. Content text similarity check against existing unique articles
        is_fuzzy_duplicate = False
        full_text = f"{title} {article.get('description', '')}"
        
        for unique_art in unique_articles:
            existing_text = f"{unique_art.get('title', '')} {unique_art.get('description', '')}"
            similarity = calculate_jaccard_similarity(full_text, existing_text)
            
            if similarity >= similarity_threshold:
                is_fuzzy_duplicate = True
                break

        if not is_fuzzy_duplicate:
            if norm_url:
                seen_urls.add(norm_url)
            if norm_title:
                seen_titles.add(norm_title)
            unique_articles.append(article)

    return unique_articles
