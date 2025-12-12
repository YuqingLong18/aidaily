import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}


def _is_viable_image(url: str) -> bool:
    """
    Filter out obvious non-content images (icons, sprites, data URIs).
    """
    if not url:
        return False
    if url.startswith("data:"):
        return False
    lowered = url.lower()
    if lowered.startswith("//"):
        return False
    bad_tokens = ["sprite", "logo", "icon", "avatar", "blank", "tracking", "pixel"]
    return lowered.startswith("http") and not any(token in lowered for token in bad_tokens)


def _first_img_from_soup(soup: BeautifulSoup, base_url: str) -> str | None:
    """
    Return the first viable image URL from a parsed document.
    """
    for tag in soup.select("figure img, article img, img"):
        candidate = tag.get("src") or tag.get("data-src")
        if not candidate:
            continue
        full_url = urljoin(base_url, candidate)
        if _is_viable_image(full_url):
            return full_url
    return None


def fetch_arxiv_image(arxiv_url: str) -> str | None:
    """
    For arXiv papers, fetch the ar5iv HTML rendering and grab the first figure image.
    """
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(v\d+)?", arxiv_url)
    if not match:
        return None

    paper_id = "".join([m for m in match.groups() if m])
    html_url = f"https://ar5iv.org/html/{paper_id}"

    try:
        resp = requests.get(html_url, headers=DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prefer figure images; fall back to any image in the document.
    image_url = _first_img_from_soup(soup, html_url)
    if image_url:
        return image_url

    # As a fallback, try common meta image tags.
    for selector in [
        'meta[property="og:image"]',
        'meta[name="twitter:image"]',
        'meta[name="image"]',
    ]:
        tag = soup.select_one(selector)
        if tag:
            candidate = tag.get("content")
            if candidate and _is_viable_image(candidate):
                return urljoin(html_url, candidate)

    return None


def fetch_article_image(url: str) -> str | None:
    """
    For industry/news items, pull an illustrative image from meta tags or in-article images.
    """
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prioritize OpenGraph / Twitter cards which are usually main art.
    for selector in [
        'meta[property="og:image"]',
        'meta[property="twitter:image"]',
        'meta[name="og:image"]',
        'meta[name="twitter:image"]',
        'meta[name="image"]',
    ]:
        tag = soup.select_one(selector)
        if tag:
            candidate = tag.get("content")
            if candidate and _is_viable_image(candidate):
                return urljoin(url, candidate)

    # Fallback: find the first reasonable inline image.
    return _first_img_from_soup(soup, url)


def find_best_image(item: dict) -> str | None:
    """
    Route to the right strategy based on item type.
    """
    item_type = item.get("type")
    item_url = item.get("url", "")

    if item_type == "academic":
        return fetch_arxiv_image(item_url)
    return fetch_article_image(item_url)
