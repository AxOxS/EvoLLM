"""Real API client – HTTP calls to FastAPI backend.

Matches the same interface as mock_api.py so the frontend can
swap between them without changes.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

BASE_URL = "http://localhost:8000"

AGENT_ORDER = ["planner", "researcher", "coder", "reviewer"]


# ── Data models (same shape as mock_api) ──────────────────────────────

@dataclass
class AgentRun:
    agent_name: str
    output: str
    status: str = "done"


@dataclass
class Message:
    role: str
    content: str
    agent_runs: list[AgentRun] = field(default_factory=list)


@dataclass
class Task:
    id: str
    prompt: str
    status: str = "done"
    created_at: str = ""
    agent_runs: list[AgentRun] = field(default_factory=list)
    result: str = ""
    messages: list[Message] = field(default_factory=list)


@dataclass
class RagDocument:
    id: str
    filename: str
    size_kb: float
    uploaded_at: str
    doc_type: str = "txt"


# ── API Client ────────────────────────────────────────────────────────

class API:
    """HTTP client for the EvoLLM FastAPI backend."""

    def __init__(self):
        self._token: Optional[str] = None

    @property
    def _auth_headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    # ── Auth ──────────────────────────────────────────────────────────

    async def register(self, email: str, password: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/user/register",
                json={"email": email, "password": password},
            )
            if r.status_code == 200:
                data = r.json()
                self._token = data["token"]
                return {"ok": True, "message": "Registration successful!", "token": data["token"], "email": data["email"]}
            return {"ok": False, "error": r.json().get("detail", "Error")}

    async def login(self, email: str, password: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE_URL}/user/login",
                json={"email": email, "password": password},
            )
            if r.status_code == 200:
                data = r.json()
                self._token = data["token"]
                return {"ok": True, "token": data["token"], "email": data["email"]}
            return {"ok": False, "error": r.json().get("detail", "Error")}

    # ── Tasks ─────────────────────────────────────────────────────────

    async def submit_task(
        self,
        prompt: str,
        rag_enabled: bool = True,
        web_search_enabled: bool = False,
        on_agent_start: Optional[Callable] = None,
        on_agent_done: Optional[Callable] = None,
        existing_task_id: Optional[str] = None,
        on_task_created: Optional[Callable] = None,
    ) -> Task:
        """Submit a task and poll for progress until done."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{BASE_URL}/task",
                json={
                    "prompt": prompt,
                    "rag_enabled": rag_enabled,
                    "web_search_enabled": web_search_enabled,
                },
                headers=self._auth_headers,
            )
            if r.status_code != 200:
                detail = r.json().get("detail", "Error creating task")
                raise RuntimeError(detail)

            data = r.json()
            task = _parse_task(data)

            # Notify caller about creation
            if on_task_created:
                result = on_task_created(task)
                if asyncio.iscoroutine(result):
                    await result

        # Poll for status until done/failed
        seen_agents: set[str] = set()
        while task.status in ("pending", "in_progress"):
            await asyncio.sleep(1.5)

            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{BASE_URL}/task/status/{task.id}",
                    headers=self._auth_headers,
                )
                if r.status_code != 200:
                    break

                status_data = r.json()
                task.status = status_data["status"]

                # Fire agent callbacks based on new agent_runs
                for run_data in status_data.get("agent_runs", []):
                    agent = run_data["agent_name"]
                    if agent not in seen_agents:
                        seen_agents.add(agent)
                        if on_agent_start:
                            result = on_agent_start(agent)
                            if asyncio.iscoroutine(result):
                                await result
                        if on_agent_done:
                            result = on_agent_done(agent, run_data.get("output", ""))
                            if asyncio.iscoroutine(result):
                                await result

        # Fetch final task data
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{BASE_URL}/task/{task.id}",
                headers=self._auth_headers,
            )
            if r.status_code == 200:
                task = _parse_task(r.json())

        return task

    async def get_task_history(self) -> list[Task]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{BASE_URL}/task/history",
                headers=self._auth_headers,
            )
            if r.status_code == 200:
                return [_parse_task(t) for t in r.json()]
            return []

    # ── RAG ───────────────────────────────────────────────────────────

    async def upload_document(self, filename: str, content: bytes) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{BASE_URL}/rag/upload",
                files={"file": (filename, content)},
                headers=self._auth_headers,
            )
            if r.status_code == 200:
                return {"ok": True, "message": f'Document "{filename}" successfully uploaded to RAG database.'}
            return {"ok": False, "error": r.json().get("detail", "Error")}

    async def get_rag_documents(self) -> list[RagDocument]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{BASE_URL}/rag/documents",
                headers=self._auth_headers,
            )
            if r.status_code == 200:
                return [_parse_doc(d) for d in r.json()]
            return []

    async def delete_rag_document(self, doc_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.delete(
                f"{BASE_URL}/rag/documents/{doc_id}",
                headers=self._auth_headers,
            )
            return {"ok": r.status_code == 200}


# ── Helpers ───────────────────────────────────────────────────────────

def _parse_task(data: dict) -> Task:
    agent_runs = [
        AgentRun(
            agent_name=ar.get("agent_name", ""),
            output=ar.get("output", ""),
            status=ar.get("status", "done"),
        )
        for ar in data.get("agent_runs", [])
    ]

    task = Task(
        id=data.get("id", ""),
        prompt=data.get("task_prompt", ""),
        status=data.get("status", "done"),
        created_at=data.get("created_at", ""),
        agent_runs=agent_runs,
        result=data.get("result", ""),
    )

    # Build messages for the chat UI
    if task.prompt:
        task.messages.append(Message(role="user", content=task.prompt))
    if task.result:
        task.messages.append(Message(role="assistant", content=task.result, agent_runs=agent_runs))

    return task


def _parse_doc(data: dict) -> RagDocument:
    return RagDocument(
        id=data.get("id", ""),
        filename=data.get("filename", ""),
        size_kb=data.get("size_kb", 0.0),
        uploaded_at=data.get("uploaded_at", ""),
        doc_type=data.get("doc_type", "txt"),
    )


# Singleton
api = API()
