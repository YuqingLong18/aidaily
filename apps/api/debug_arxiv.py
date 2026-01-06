
import sys
from datetime import datetime, timezone
from app.time_semantics import EditionWindow
from app.arxiv_source import fetch_arxiv_items
from app.http_client import fetch_text

# Define window for UTC 2025-12-19
start = datetime(2025, 12, 19, 0, 0, 0, tzinfo=timezone.utc)
end = datetime(2025, 12, 19, 23, 59, 59, tzinfo=timezone.utc)
window = EditionWindow(None, None, None, start, end)

print(f"Testing ArXiv fetch for window: {start} to {end}")

try:
    # 1. Fetch text directly to see raw response (using similar logic to source)
    categories = ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.SE", "cs.RO"]
    from app.arxiv_source import _arxiv_query_for_window
    query = _arxiv_query_for_window(categories, window)
    from urllib.parse import quote_plus
    query_qs = quote_plus(query)
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query={query_qs}"
        f"&start=0&max_results=10"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    print(f"URL: {url}")
    raw = fetch_text(url)
    print(f"Raw response length: {len(raw)}")
    print(f"Raw response snippet: {raw[:500]}...")

    # 2. Use the function
    items = fetch_arxiv_items(window, categories=categories, max_results=10)
    print(f"Items found via function: {len(items)}")
    for i in items:
        print(f" - {i.title} ({i.published_at_utc})")
    
except Exception as e:
    print(f"Error: {e}")
