import base64
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup


def _log(message: str) -> None:
    """
    Lightweight logger with timestamp for debugging slow image fetches.
    """
    print(f"[images] {datetime.utcnow().isoformat()} {message}")

DEFAULT_HEADERS = {
    "User-Agent": "NexusDailyBot/1.0 (+https://example.com)",
}


def _arxiv_pdf_url(url: str) -> Optional[str]:
    """
    Convert an arXiv abs/ URL to its PDF URL.
    """
    if not url:
        return None

    if url.endswith(".pdf"):
        return url

    if "/abs/" in url:
        return url.replace("/abs/", "/pdf/") + ".pdf"

    return None


def _first_image_from_pdf(pdf_url: str, max_pages: int = 3, min_area: int = 40_000) -> Optional[str]:
    """
    Download the PDF and return the first reasonably sized image as a data URL.
    """
    start_time = time.time()
    _log(f"Fetching PDF for image search: {pdf_url}")
    try:
        response = requests.get(pdf_url, headers=DEFAULT_HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        _log(f"Failed to download PDF {pdf_url}: {e}")
        return None
    _log(f"Downloaded PDF in {time.time() - start_time:.2f}s (size={len(response.content) / 1_000_000:.2f}MB)")

    try:
        with fitz.open(stream=response.content, filetype="pdf") as doc:
            for page_index in range(min(max_pages, len(doc))):
                images = doc.get_page_images(page_index, full=True)
                for image in images:
                    xref = image[0]
                    pix = fitz.Pixmap(doc, xref)

                    # Skip tiny icons and badges.
                    if pix.width * pix.height < min_area:
                        continue

                    # Normalize colorspace for compatibility.
                    if pix.n >= 5:
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    png_bytes = pix.tobytes("png")
                    if not png_bytes:
                        continue

                    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
                    _log(f"Found image in PDF on page {page_index} after {time.time() - start_time:.2f}s")
                    return data_url
    except Exception as e:
        _log(f"Failed to parse PDF {pdf_url}: {e}")
        return None

    _log(f"No suitable image found in first {max_pages} pages ({time.time() - start_time:.2f}s)")
    return None


def _first_image_from_news(url: str) -> Optional[str]:
    """
    Parse a news article and return the first meaningful image URL.
    """
    start_time = time.time()
    _log(f"Fetching news article for image search: {url}")
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        _log(f"Failed to fetch news page {url}: {e}")
        return None

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        selectors = ["article img", "main img", "div img", "img"]

        for selector in selectors:
            for img in soup.select(selector):
                src = (
                    img.get("data-src")
                    or img.get("data-original")
                    or img.get("data-lazy-src")
                    or img.get("srcset")
                    or img.get("src")
                )

                if not src:
                    continue

                # If srcset, use the first entry.
                if " " in src and "," in src:
                    src = src.split(",")[0].strip().split(" ")[0]

                # Skip embedded SVG/base64 placeholders.
                if src.startswith("data:"):
                    continue

                full_url = urljoin(url, src)
                _log(f"Found inline image after {time.time() - start_time:.2f}s: {full_url}")
                return full_url
    except Exception as e:
        _log(f"Failed to parse HTML for {url}: {e}")
        return None

    _log(f"No image found in article after {time.time() - start_time:.2f}s")
    return None


def attach_images(items: List[Dict]) -> List[Dict]:
    """
    Add image_url/image_alt fields to ranked/selected items.
    Only runs after items are already scored/filtered to limit extra network calls.
    """
    _log(f"Attaching images to {len(items)} items")
    total_start = time.time()

    for index, item in enumerate(items, start=1):
        item_start = time.time()
        _log(f"[{index}/{len(items)}] Start image search type={item.get('type')} url={item.get('url')}")
        image_url = None

        if item.get("type") == "academic" and "arxiv.org" in item.get("url", ""):
            pdf_url = _arxiv_pdf_url(item["url"])
            if pdf_url:
                image_url = _first_image_from_pdf(pdf_url)
                item["image_alt"] = item.get("image_alt") or "First figure from the paper"

        elif item.get("type") == "industry":
            image_url = _first_image_from_news(item["url"])
            item["image_alt"] = item.get("image_alt") or f"Image from {item.get('source', 'news article')}"

        if image_url:
            item["image_url"] = image_url
            _log(f"[{index}/{len(items)}] Image attached in {time.time() - item_start:.2f}s (url length={len(str(image_url))})")
        else:
            _log(f"[{index}/{len(items)}] No image found in {time.time() - item_start:.2f}s")

    _log(f"Finished attaching images in {time.time() - total_start:.2f}s")
    return items
