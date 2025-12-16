from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


_DROP_QUERY_KEYS_PREFIXES = ("utm_", "ref_", "spm", "fbclid", "gclid", "mc_cid", "mc_eid")


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url

    kept = []
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        lk = k.lower()
        if any(lk.startswith(p) for p in _DROP_QUERY_KEYS_PREFIXES):
            continue
        if lk in {"ref", "source", "src"}:
            continue
        kept.append((k, v))

    new_query = urlencode(kept, doseq=True)
    cleaned = parsed._replace(query=new_query, fragment="")
    return urlunparse(cleaned)

