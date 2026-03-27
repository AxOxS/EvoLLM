"""Base agent class with common LLM call and DB logging."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from backend.models import AgentRun
from backend.services import llm
from backend.config import settings


class BaseAgent(ABC):
    """All agents inherit from this and implement ``run()``."""

    name: str = "base"
    model: str = ""  # override in subclass; empty = small model

    @abstractmethod
    async def run(self, context: dict, db: Session) -> str:
        """Execute agent logic. Returns output string."""

    async def call_llm(self, prompt: str, system_prompt: str | None = None) -> str:
        return await llm.generate(prompt, system_prompt, model=self.model or None)

    def save_run(self, task_id: str, output: str, status: str, db: Session) -> AgentRun:
        run = AgentRun(task_id=task_id, agent_name=self.name, output=output, status=status)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
