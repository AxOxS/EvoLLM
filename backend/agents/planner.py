"""Planner agent – decomposes task into JSON subtasks."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.agents.base import BaseAgent
from backend.models import Subtask

SYSTEM_PROMPT = """You are the Planner agent in a multi-agent AI system.
Your job is to analyze the user's task and decompose it into clear, sequential sub-tasks.

IMPORTANT: Respond ONLY with a valid JSON array of strings. Each string is one sub-task.
Example: ["Research the topic", "Write the code", "Add error handling", "Write tests"]

Do NOT include any other text, explanations, or markdown – just the JSON array."""


class PlannerAgent(BaseAgent):
    name = "planner"

    async def run(self, context: dict, db: Session) -> str:
        task_id: str = context["task_id"]
        prompt: str = context["prompt"]

        llm_prompt = f"Decompose this task into sub-tasks:\n\n{prompt}"

        # Retry up to 2 times for valid JSON (UC-03)
        subtasks_list: list[str] = []
        last_error = ""
        for attempt in range(2):
            raw = await self.call_llm(llm_prompt, system_prompt=SYSTEM_PROMPT)
            try:
                # Try to extract JSON array from the response
                raw_stripped = raw.strip()
                # Handle case where LLM wraps in markdown code block
                if raw_stripped.startswith("```"):
                    lines = raw_stripped.split("\n")
                    raw_stripped = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_stripped
                    raw_stripped = raw_stripped.strip()

                parsed = json.loads(raw_stripped)
                if isinstance(parsed, list) and all(isinstance(s, str) for s in parsed):
                    subtasks_list = parsed
                    break
                last_error = "LLM returned non-string-array JSON"
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON: {e}"

        if not subtasks_list:
            # Fallback: treat the entire task as a single subtask
            subtasks_list = [prompt]
            output = f"Could not decompose into subtasks ({last_error}). Using task as single unit."
        else:
            output = f"Task decomposed into {len(subtasks_list)} sub-tasks."

        # Save subtasks to DB
        for i, desc in enumerate(subtasks_list):
            st = Subtask(task_id=task_id, description=desc, order_index=i, status="pending")
            db.add(st)
        db.commit()

        self.save_run(task_id, output, "done", db)
        context["subtasks"] = subtasks_list
        return output
