"""Researcher agent – gathers info from RAG and optionally web search."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.agents.base import BaseAgent
from backend.services.rag_service import rag_service
from backend.services import web_search

SYSTEM_PROMPT = """You are the Researcher agent in a multi-agent AI system.
Your role is to summarize the collected information into a concise research brief
that the Coder agent will use to generate the final answer.

Summarize the key points from the provided context. Be thorough but concise."""


class ResearcherAgent(BaseAgent):
    name = "researcher"

    async def run(self, context: dict, db: Session) -> str:
        task_id: str = context["task_id"]
        prompt: str = context["prompt"]
        rag_enabled: bool = context.get("rag_enabled", True)
        web_search_enabled: bool = context.get("web_search_enabled", False)
        subtasks: list[str] = context.get("subtasks", [])

        search_query = prompt
        gathered: list[str] = []
        sources: list[str] = []

        # 1. RAG search
        if rag_enabled:
            rag_results = rag_service.query(search_query, n_results=5)
            if rag_results:
                gathered.append("=== RAG Knowledge Base Results ===")
                for i, chunk in enumerate(rag_results, 1):
                    gathered.append(f"[RAG {i}] {chunk}")
                sources.append("RAG knowledge base")

        # 2. Web search (if enabled and RAG results insufficient)
        if web_search_enabled:
            web_results = await web_search.search(search_query, max_results=5)
            if web_results:
                gathered.append("=== Web Search Results ===")
                for item in web_results:
                    gathered.append(f"[Web] {item['title']}: {item['content'][:300]}")
                sources.append("web search")

        if not gathered:
            gathered.append("No external information found. The Coder agent will use its own knowledge.")
            sources.append("general context")

        # Summarize via LLM
        research_text = "\n".join(gathered)
        llm_prompt = (
            f"Task: {prompt}\n\n"
            f"Sub-tasks: {', '.join(subtasks)}\n\n"
            f"Collected information:\n{research_text}\n\n"
            f"Summarize the above into a concise research brief for the Coder agent."
        )
        summary = await self.call_llm(llm_prompt, system_prompt=SYSTEM_PROMPT)

        source_str = ", ".join(sources) if sources else "general context"
        output = f"Collected information from {source_str}."
        self.save_run(task_id, output, "done", db)

        context["research"] = summary
        context["research_raw"] = research_text
        return output
