from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass(frozen=True)
class HttpConfig:
    timeout_s: float = float(os.getenv("NEXUS_HTTP_TIMEOUT_S", "20"))
    user_agent: str = os.getenv(
        "NEXUS_USER_AGENT",
        "NexusAIDaily/0.1 (+https://localhost; ingestion)",
    )
    max_retries: int = int(os.getenv("NEXUS_HTTP_MAX_RETRIES", "2"))


def fetch_text(url: str, *, config: Optional[HttpConfig] = None) -> str:
    cfg = config or HttpConfig()
    headers = {"User-Agent": cfg.user_agent}
    last_exc: Exception | None = None
    for attempt in range(cfg.max_retries + 1):
        try:
            with httpx.Client(
                headers=headers,
                follow_redirects=True,
                timeout=cfg.timeout_s,
            ) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.text
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt >= cfg.max_retries:
                break
    raise RuntimeError(f"fetch failed for {url}: {last_exc}") from last_exc

