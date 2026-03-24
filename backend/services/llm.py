"""Ollama LLM HTTP client."""

from __future__ import annotations

import httpx

from backend.config import settings

TIMEOUT = 120.0


async def generate(prompt: str, system_prompt: str | None = None) -> str:
    """Call Ollama POST /api/generate and return the full response text.

    Retries once on failure (NFR-06).
    """
    payload: dict = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.post(f"{settings.ollama_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
        except Exception as e:
            last_error = e
            if attempt == 0:
                continue
            break

    raise RuntimeError(f"Ollama LLM call failed after 2 attempts: {last_error}")
