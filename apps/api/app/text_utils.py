from __future__ import annotations

import re


_WS_RE = re.compile(r"\s+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def normalize_ws(text: str) -> str:
    return _WS_RE.sub(" ", text or "").strip()


def strip_htmlish(text: str) -> str:
    # RSS summaries often include embedded tags; keep this minimal to avoid extra deps.
    return normalize_ws(re.sub(r"<[^>]+>", " ", text or ""))


def split_sentences(text: str) -> list[str]:
    text = normalize_ws(text)
    if not text:
        return []
    sentences = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    return sentences

