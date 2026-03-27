"""Coder agent – generates code or text based on research context."""

from __future__ import annotations

import logging
import time

from sqlalchemy.orm import Session

from backend.agents.base import BaseAgent
from backend.config import settings
from backend.models import Task

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Response Generator agent in a multi-agent AI system.
Your job is to generate a high-quality response based on:
1. The original user message (and any previous conversation context)
2. The sub-tasks from the Planner
3. The research brief from the Researcher

IMPORTANT: Match your response to what the user is actually asking for:
- If the user asks a question, answer it directly in plain text.
- If the user asks for code, write clean, well-commented code.
- If the user asks for an explanation, explain clearly without generating code.
- If this is a follow-up message (e.g. "why?", "explain more", "can you clarify?"),
  respond in the context of the previous conversation.

Do NOT generate code unless the user explicitly asks for it.
Use markdown formatting for readability."""

# How often (seconds) to flush partial result to the DB during streaming
FLUSH_INTERVAL = 0.4


class CoderAgent(BaseAgent):
    name = "coder"
    model = settings.ollama_model_big

    async def run(self, context: dict, db: Session) -> str:
        task_id: str = context["task_id"]
        prompt: str = context["prompt"]
        subtasks: list[str] = context.get("subtasks", [])
        research: str = context.get("research", "")
        reviewer_feedback: str = context.get("reviewer_feedback", "")

        chat_history: list[dict] = context.get("chat_history", [])

        llm_prompt = ""
        if chat_history:
            llm_prompt += "Previous conversation:\n"
            for msg in chat_history:
                role = msg.get("role", "user").capitalize()
                llm_prompt += f"{role}: {msg.get('content', '')}\n"
            llm_prompt += "\n"

        llm_prompt += f"User task: {prompt}\n\n"
        if subtasks:
            llm_prompt += f"Sub-tasks:\n" + "\n".join(f"- {s}" for s in subtasks) + "\n\n"
        if research:
            llm_prompt += f"Research brief:\n{research}\n\n"
        if reviewer_feedback:
            llm_prompt += f"Reviewer feedback (please address these issues):\n{reviewer_feedback}\n\n"

        llm_prompt += "Generate the response:"

        # Stream tokens and periodically flush to task.result so the frontend
        # can show partial output while polling.
        result = ""
        last_flush = time.monotonic()

        try:
            async for token in self.call_llm_stream(llm_prompt, system_prompt=SYSTEM_PROMPT):
                result += token

                now = time.monotonic()
                if now - last_flush >= FLUSH_INTERVAL:
                    self._flush_partial(task_id, result, db)
                    last_flush = now
        except Exception as e:
            logger.warning("Streaming failed, falling back to non-streaming: %s", e)
            result = await self.call_llm(llm_prompt, system_prompt=SYSTEM_PROMPT)

        # Final flush to make sure complete result is in DB
        self._flush_partial(task_id, result, db)

        # Summary for agent log
        lines = [l for l in result.strip().splitlines() if l.strip()]
        preview = "\n".join(lines[:5])
        if len(lines) > 5:
            preview += f"\n... ({len(lines)} lines total)"
        output = f"Generated response ({len(result)} chars):\n{preview}"
        self.save_run(task_id, output, "done", db)

        context["coder_result"] = result
        return output

    def _flush_partial(self, task_id: str, text: str, db: Session):
        """Write current accumulated text to task.result so polling can see it."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.result = text
            db.commit()
