"""Ollama LLM HTTP client."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx

from backend.config import settings

TIMEOUT = 120.0


async def generate(prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
    """Call Ollama POST /api/generate and return the full response text.

    Retries once on failure (NFR-06).
    """
    payload: dict = {
        "model": model or settings.ollama_model_small,
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


async def generate_stream(
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream tokens from Ollama. Yields each token as it arrives."""
    payload: dict = {
        "model": model or settings.ollama_model_small,
        "prompt": prompt,
        "stream": True,
    }
    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        async with client.stream(
            "POST", f"{settings.ollama_url}/api/generate", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    return
