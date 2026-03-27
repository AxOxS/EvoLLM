"""Mock API layer – simulates backend responses for standalone UI development."""

from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


# ── Data models ──────────────────────────────────────────────────────

@dataclass
class AgentRun:
    agent_name: str
    output: str
    status: str = "done"


@dataclass
class Message:
    role: str  # "user" or "assistant"
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
    conversation_id: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not self.conversation_id:
            self.conversation_id = self.id
        # Build messages from prompt/result if not set
        if not self.messages and self.prompt:
            self.messages.append(Message(role="user", content=self.prompt))
            if self.result:
                self.messages.append(Message(role="assistant", content=self.result, agent_runs=list(self.agent_runs)))


@dataclass
class RagDocument:
    id: str
    filename: str
    size_kb: float
    uploaded_at: str
    doc_type: str = "txt"


# ── Pre-built sample data ───────────────────────────────────────────

SAMPLE_TASKS: list[Task] = [
    Task(
        id="sample-1",
        prompt="Create a Python Flask REST API with CRUD operations",
        created_at="2026-03-20 14:30",
        result=(
            "Here is the Flask REST API with the following endpoints:\n\n"
            "```python\n"
            "from flask import Flask, jsonify, request\n\n"
            "app = Flask(__name__)\nitems = []\n\n"
            "@app.route('/items', methods=['GET'])\n"
            "def get_items():\n    return jsonify(items)\n\n"
            "@app.route('/items', methods=['POST'])\n"
            "def create_item():\n"
            "    item = request.json\n"
            "    items.append(item)\n"
            "    return jsonify(item), 201\n"
            "```\n\n"
            "The API supports GET, POST, PUT and DELETE operations."
        ),
        agent_runs=[
            AgentRun("planner", "Task decomposed into 3 sub-tasks: API structure, CRUD endpoints, testing."),
            AgentRun("researcher", "Found information about Flask best practices and REST API design."),
            AgentRun("coder", "Generated Flask API code with all CRUD operations."),
            AgentRun("reviewer", "Code verified. Structure is correct, endpoints follow REST standards."),
        ],
    ),
    Task(
        id="sample-2",
        prompt="Explain what RAG (Retrieval-Augmented Generation) is",
        created_at="2026-03-21 09:15",
        result=(
            "**RAG (Retrieval-Augmented Generation)** is a method that combines information retrieval "
            "with text generation.\n\n"
            "### How it works:\n"
            "1. **Retrieval** - the system searches for relevant documents in a vector database\n"
            "2. **Augmented** - found documents are added to the LLM query as context\n"
            "3. **Generation** - the LLM generates an answer based on the provided context\n\n"
            "### Advantages:\n"
            "- Reduces hallucinations\n"
            "- Allows using up-to-date data\n"
            "- Privacy - data stays local"
        ),
        agent_runs=[
            AgentRun("planner", "Task: provide RAG explanation. Sub-tasks: definition, working principle, advantages."),
            AgentRun("researcher", "Collected information about RAG from knowledge base documents."),
            AgentRun("coder", "Generated structured explanation with examples."),
            AgentRun("reviewer", "Explanation is accurate and comprehensive. Approved."),
        ],
    ),
]

SAMPLE_RAG_DOCS: list[RagDocument] = [
    RagDocument(id="doc-1", filename="python_best_practices.pdf", size_kb=245.3, uploaded_at="2026-03-19 10:00", doc_type="pdf"),
    RagDocument(id="doc-2", filename="flask_documentation.txt", size_kb=89.1, uploaded_at="2026-03-19 11:30", doc_type="txt"),
    RagDocument(id="doc-3", filename="api_design_guide.docx", size_kb=156.7, uploaded_at="2026-03-20 08:45", doc_type="docx"),
]

MOCK_AGENT_OUTPUTS = {
    "planner": "Task analyzed and decomposed into {n} sub-tasks.",
    "researcher": "Collected required information from {source}.",
    "coder": "Generated response based on collected information and sub-tasks.",
    "reviewer": "Result verified. Quality is acceptable. Approved.",
}


# ── Mock API class ───────────────────────────────────────────────────

class MockAPI:
    """Simulates all backend endpoints with realistic delays."""

    def __init__(self):
        self._token: Optional[str] = None
        self._tasks: list[Task] = list(SAMPLE_TASKS)
        self._rag_docs: list[RagDocument] = list(SAMPLE_RAG_DOCS)

    # ── Auth ─────────────────────────────────────────────────────────

    async def register(self, email: str, password: str) -> dict[str, Any]:
        await asyncio.sleep(0.5)
        import re
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return {"ok": False, "error": "Please enter a valid email address"}
        if len(password) < 4:
            return {"ok": False, "error": "Password is too short (min. 4 characters)"}
        return {"ok": True, "message": "Registration successful!"}

    async def login(self, email: str, password: str) -> dict[str, Any]:
        await asyncio.sleep(0.5)
        if not email or not password:
            return {"ok": False, "error": "Please enter email and password"}
        self._token = f"mock-jwt-{uuid.uuid4().hex[:12]}"
        return {"ok": True, "token": self._token, "email": email}

    # ── Tasks ────────────────────────────────────────────────────────

    async def submit_task(
        self,
        prompt: str,
        rag_enabled: bool = True,
        web_search_enabled: bool = False,
        on_agent_start: Optional[Callable[[str], Any]] = None,
        on_agent_done: Optional[Callable[[str, str], Any]] = None,
        existing_task_id: Optional[str] = None,
        on_task_created: Optional[Callable] = None,
        chat_history: Optional[list[dict]] = None,
        conversation_id: Optional[str] = None,
        on_partial_result: Optional[Callable] = None,
    ) -> Task:
        """Simulate the 4-agent pipeline."""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            prompt=prompt,
            status="in_progress",
            conversation_id=conversation_id or task_id,
        )
        task.messages = [Message(role="user", content=prompt)]
        self._tasks.insert(0, task)

        # Notify caller that task is created (for immediate sidebar update)
        if on_task_created:
            await _maybe_await(on_task_created(task))

        agents = ["planner", "researcher", "coder", "reviewer"]
        delays = [1.5, 2.0, 2.5, 1.5]
        current_runs = []

        for agent, delay in zip(agents, delays):
            if on_agent_start:
                await _maybe_await(on_agent_start(agent))
            await asyncio.sleep(delay)

            source = "knowledge base (RAG)" if rag_enabled else "general context"
            if agent == "researcher" and web_search_enabled:
                source = "knowledge base (RAG) and web search"
            elif agent == "researcher" and not rag_enabled:
                source = "general context"

            n = random.randint(2, 4)
            output = MOCK_AGENT_OUTPUTS[agent].format(n=n, source=source)
            run = AgentRun(agent_name=agent, output=output)
            task.agent_runs.append(run)
            current_runs.append(run)

            if on_agent_done:
                await _maybe_await(on_agent_done(agent, output))

        task.status = "done"
        result = _generate_mock_result(prompt, rag_enabled, web_search_enabled)
        task.result = result
        task.messages.append(Message(role="assistant", content=result, agent_runs=current_runs))

        return task

    def _find_task(self, task_id: str) -> Optional[Task]:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None

    async def get_conversation(self, conversation_id: str) -> list[Task]:
        """Get all tasks in a conversation, oldest first."""
        return list(reversed([t for t in self._tasks if t.conversation_id == conversation_id]))

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        task = self._find_task(task_id)
        if task and task.status in ("pending", "in_progress"):
            task.status = "cancelled"
        return {"ok": True}

    async def delete_task(self, task_id: str) -> dict[str, Any]:
        self._tasks = [t for t in self._tasks if t.id != task_id]
        return {"ok": True}

    async def get_task_history(self) -> list[Task]:
        await asyncio.sleep(0.1)
        return list(self._tasks)

    # ── RAG ──────────────────────────────────────────────────────────

    async def upload_document(self, filename: str, content: bytes) -> dict[str, Any]:
        await asyncio.sleep(1.0)
        doc = RagDocument(
            id=f"doc-{uuid.uuid4().hex[:6]}",
            filename=filename,
            size_kb=round(len(content) / 1024, 1) if content else round(random.uniform(10, 500), 1),
            uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            doc_type=filename.rsplit(".", 1)[-1] if "." in filename else "txt",
        )
        self._rag_docs.insert(0, doc)
        return {
            "ok": True,
            "message": f"Document \"{filename}\" successfully uploaded to RAG database.",
        }

    async def get_rag_documents(self) -> list[RagDocument]:
        await asyncio.sleep(0.2)
        return list(self._rag_docs)

    async def delete_rag_document(self, doc_id: str) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        self._rag_docs = [d for d in self._rag_docs if d.id != doc_id]
        return {"ok": True}


# ── Helpers ──────────────────────────────────────────────────────────

async def _maybe_await(result):
    if asyncio.iscoroutine(result):
        await result


def _generate_mock_result(prompt: str, rag: bool, web: bool) -> str:
    sources = []
    if rag:
        sources.append("RAG knowledge base")
    if web:
        sources.append("web search")
    source_text = ", ".join(sources) if sources else "general context"

    return (
        f"### Result\n\n"
        f"Your task was analyzed and executed using: **{source_text}**.\n\n"
        f"**Task:** {prompt}\n\n"
        f"---\n\n"
        f"Response generated by the 4-agent pipeline:\n"
        f"1. **Planner** - decomposed the task into sub-tasks\n"
        f"2. **Researcher** - gathered information\n"
        f"3. **Coder** - generated the response\n"
        f"4. **Reviewer** - verified quality\n\n"
        f"*This is a demo response. Once the backend is connected, this will be a real LLM result.*"
    )


# Singleton
mock_api = MockAPI()
