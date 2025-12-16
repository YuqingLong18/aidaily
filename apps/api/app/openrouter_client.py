from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str = os.getenv("NEXUS_LLM_MODEL", "google/gemini-2.5-flash")
    base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    timeout_s: float = float(os.getenv("NEXUS_LLM_TIMEOUT_S", "60"))
    max_retries: int = int(os.getenv("NEXUS_LLM_MAX_RETRIES", "1"))
    referer: Optional[str] = os.getenv("OPENROUTER_HTTP_REFERER")
    title: Optional[str] = os.getenv("OPENROUTER_X_TITLE", "Nexus AI Daily")


def load_openrouter_config() -> OpenRouterConfig:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("NEXUS_OPENROUTER_API_KEY") or ""
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY (or NEXUS_OPENROUTER_API_KEY)")
    return OpenRouterConfig(api_key=api_key)


def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return t


def chat_json(
    *,
    system: str,
    user: str,
    config: Optional[OpenRouterConfig] = None,
) -> Any:
    cfg = config or load_openrouter_config()
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    if cfg.referer:
        headers["HTTP-Referer"] = cfg.referer
    if cfg.title:
        headers["X-Title"] = cfg.title

    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    last_exc: Exception | None = None
    for attempt in range(cfg.max_retries + 1):
        try:
            with httpx.Client(timeout=cfg.timeout_s) as client:
                resp = client.post(f"{cfg.base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(_strip_code_fences(content))
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt >= cfg.max_retries:
                break
    raise RuntimeError(f"OpenRouter request failed: {last_exc}") from last_exc

