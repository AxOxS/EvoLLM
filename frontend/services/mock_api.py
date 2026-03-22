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

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
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
        prompt="Sukurk Python Flask REST API su CRUD operacijomis",
        created_at="2026-03-20 14:30",
        result=(
            "Sukuriau Flask REST API su siais endpoint'ais:\n\n"
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
            "API palaiko GET, POST, PUT ir DELETE operacijas."
        ),
        agent_runs=[
            AgentRun("planner", "Uzduotis suskaidyta i 3 sub-uzduotis: API struktura, CRUD endpoint'ai, testavimas."),
            AgentRun("researcher", "Rasta informacija apie Flask best practices ir REST API dizaina."),
            AgentRun("coder", "Sugeneruotas Flask API kodas su visomis CRUD operacijomis."),
            AgentRun("reviewer", "Kodas patikrintas. Struktura tinkama, endpoint'ai atitinka REST standartus."),
        ],
    ),
    Task(
        id="sample-2",
        prompt="Paaisink kas yra RAG (Retrieval-Augmented Generation)",
        created_at="2026-03-21 09:15",
        result=(
            "**RAG (Retrieval-Augmented Generation)** - tai metodas, kuris sujungia informacijos paieska "
            "su teksto generavimu.\n\n"
            "### Kaip veikia:\n"
            "1. **Retrieval** - sistema iesko relevanciu dokumentu vektorineje duomenu bazeje\n"
            "2. **Augmented** - rasti dokumentai pridedami prie LLM uzklauso kaip kontekstas\n"
            "3. **Generation** - LLM generuoja atsakyma remdamasis pateiktu kontekstu\n\n"
            "### Privalumai:\n"
            "- Mazina haliucinacijas\n"
            "- Leidzia naudoti naujausius duomenis\n"
            "- Privatumas - duomenys lieka lokaliai"
        ),
        agent_runs=[
            AgentRun("planner", "Uzduotis: pateikti RAG paasikinima. Sub-uzduotys: apibrezimas, veikimo principas, privalumai."),
            AgentRun("researcher", "Surinkta informacija apie RAG is ziniu bazes dokumentu."),
            AgentRun("coder", "Sugeneruotas strukturizuotas paaiskinimas su pavyzdziais."),
            AgentRun("reviewer", "Paaiskinimas tikslus ir issamus. Patvirtinta."),
        ],
    ),
]

SAMPLE_RAG_DOCS: list[RagDocument] = [
    RagDocument(id="doc-1", filename="python_best_practices.pdf", size_kb=245.3, uploaded_at="2026-03-19 10:00", doc_type="pdf"),
    RagDocument(id="doc-2", filename="flask_documentation.txt", size_kb=89.1, uploaded_at="2026-03-19 11:30", doc_type="txt"),
    RagDocument(id="doc-3", filename="api_design_guide.docx", size_kb=156.7, uploaded_at="2026-03-20 08:45", doc_type="docx"),
]

MOCK_AGENT_OUTPUTS = {
    "planner": "Uzduotis isanalizuota ir suskaidyta i {n} sub-uzduotis.",
    "researcher": "Surinkta reikalinga informacija is {source}.",
    "coder": "Sugeneruotas atsakymas pagal surinkta informacija ir sub-uzduotis.",
    "reviewer": "Rezultatas patikrintas. Kokybe tinkama. Patvirtinta.",
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
            return {"ok": False, "error": "Iveskite teisinga el. pasto adresa"}
        if len(password) < 4:
            return {"ok": False, "error": "Slaptazodis per trumpas (min. 4 simboliai)"}
        return {"ok": True, "message": "Registracija sekminga!"}

    async def login(self, email: str, password: str) -> dict[str, Any]:
        await asyncio.sleep(0.5)
        if not email or not password:
            return {"ok": False, "error": "Iveskite el. pasta ir slaptazodi"}
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
    ) -> Task:
        """Simulate the 4-agent pipeline. If existing_task_id given, appends to that conversation."""
        if existing_task_id:
            task = self._find_task(existing_task_id)
            if task:
                task.messages.append(Message(role="user", content=prompt))
            else:
                task = Task(id=str(uuid.uuid4())[:8], prompt=prompt, status="in_progress")
                task.messages = [Message(role="user", content=prompt)]
                self._tasks.insert(0, task)
        else:
            task = Task(id=str(uuid.uuid4())[:8], prompt=prompt, status="in_progress")
            task.messages = [Message(role="user", content=prompt)]
            # Add to history immediately so sidebar shows it
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

            source = "ziniu bazes (RAG)" if rag_enabled else "konteksto"
            if agent == "researcher" and web_search_enabled:
                source = "ziniu bazes (RAG) ir interneto paieskos"
            elif agent == "researcher" and not rag_enabled:
                source = "bendro konteksto"

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
            "message": f"Dokumentas \"{filename}\" sekmingai ikeltas i RAG baze.",
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
        sources.append("RAG ziniu baze")
    if web:
        sources.append("interneto paieska")
    source_text = ", ".join(sources) if sources else "bendrasis kontekstas"

    return (
        f"### Rezultatas\n\n"
        f"Jusu uzduotis buvo isanalizuota ir ivykdyta naudojant: **{source_text}**.\n\n"
        f"**Uzduotis:** {prompt}\n\n"
        f"---\n\n"
        f"Atsakymas sugeneruotas 4 agentu pipeline:\n"
        f"1. **Planner** - suskaide uzduoti i sub-uzduotis\n"
        f"2. **Researcher** - surinko informacija\n"
        f"3. **Coder** - sugeneravo atsakyma\n"
        f"4. **Reviewer** - patikrino kokybe\n\n"
        f"*Tai yra demonstracinis atsakymas. Prijungus backend, cia bus tikras LLM rezultatas.*"
    )


# Singleton
mock_api = MockAPI()
