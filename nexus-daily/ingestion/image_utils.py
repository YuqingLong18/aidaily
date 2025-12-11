import base64
from typing import Dict, List, Optional
from urllib.parse import urljoin

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

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
    try:
        response = requests.get(pdf_url, headers=DEFAULT_HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to download PDF {pdf_url}: {e}")
        return None

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
                    return data_url
    except Exception as e:
        print(f"Failed to parse PDF {pdf_url}: {e}")
        return None

    return None


def _first_image_from_news(url: str) -> Optional[str]:
    """
    Parse a news article and return the first meaningful image URL.
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch news page {url}: {e}")
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
                return full_url
    except Exception as e:
        print(f"Failed to parse HTML for {url}: {e}")
        return None

    return None


def attach_images(items: List[Dict]) -> List[Dict]:
    """
    Add image_url/image_alt fields to ranked/selected items.
    Only runs after items are already scored/filtered to limit extra network calls.
    """
    for item in items:
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

    return items
