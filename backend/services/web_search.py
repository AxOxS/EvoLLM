"""Tavily web search client."""

from __future__ import annotations

import httpx

from backend.config import settings

TAVILY_URL = "https://api.tavily.com/search"


async def search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via Tavily API.

    Returns list of {title, url, content} dicts.
    If no API key is configured or the call fails, returns an empty list (UC-04 fallback).
    """
    if not settings.tavily_api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                TAVILY_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                }
                for item in results
            ]
    except Exception:
        return []
