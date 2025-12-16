from __future__ import annotations

from bs4 import BeautifulSoup

from app.http_client import fetch_text
from app.text_utils import normalize_ws


def scrape_article_text(url: str, *, max_chars: int = 12_000) -> str:
    html = fetch_text(url)
    soup = BeautifulSoup(html, "lxml")

    for t in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        t.decompose()

    article = soup.find("article")
    root = article if article is not None else soup.body if soup.body is not None else soup

    parts: list[str] = []

    for meta_name in ["description", "og:description"]:
        m = soup.find("meta", attrs={"name": meta_name}) or soup.find("meta", attrs={"property": meta_name})
        if m and m.get("content"):
            parts.append(str(m.get("content")))

    for p in root.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if txt and len(txt) >= 40:
            parts.append(txt)

    text = normalize_ws("\n".join(parts))
    return text[:max_chars]

