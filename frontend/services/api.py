"""Real API client – HTTP calls to FastAPI backend.

This is a stub. Replace mock_api imports with this module
once the backend is running.
"""

from __future__ import annotations

import httpx
from typing import Any, Callable, Optional


BASE_URL = "http://localhost:8000"


class API:
    """HTTP client for the EvoLLM FastAPI backend."""

    def __init__(self):
        self._token: Optional[str] = None

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def register(self, username: str, password: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/user/register",
                json={"username": username, "password": password},
            )
            if r.status_code == 200:
                return {"ok": True, "message": "Registration successful!"}
            return {"ok": False, "error": r.json().get("detail", "Error")}

    async def login(self, username: str, password: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/user/login",
                json={"username": username, "password": password},
            )
            if r.status_code == 200:
                data = r.json()
                self._token = data["token"]
                return {"ok": True, "token": data["token"], "username": username}
            return {"ok": False, "error": r.json().get("detail", "Error")}

    async def submit_task(
        self,
        prompt: str,
        rag_enabled: bool = True,
        web_search_enabled: bool = False,
        on_agent_start: Optional[Callable] = None,
        on_agent_done: Optional[Callable] = None,
    ):
        # TODO: Implement with SSE or polling for real-time agent progress
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/task",
                json={
                    "prompt": prompt,
                    "rag_enabled": rag_enabled,
                    "web_search_enabled": web_search_enabled,
                },
                headers=self._headers,
                timeout=120,
            )
            return r.json()

    async def get_task_history(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{BASE_URL}/task/history",
                headers=self._headers,
            )
            return r.json()

    async def upload_document(self, filename: str, content: bytes) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/rag/upload",
                files={"file": (filename, content)},
                headers={"Authorization": f"Bearer {self._token}"} if self._token else {},
            )
            if r.status_code == 200:
                return {"ok": True, "message": r.json().get("message", "Uploaded")}
            return {"ok": False, "error": r.json().get("detail", "Error")}


api = API()
