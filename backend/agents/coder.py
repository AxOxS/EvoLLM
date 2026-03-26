"""Coder agent – generates code or text based on research context."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.agents.base import BaseAgent

SYSTEM_PROMPT = """You are the Coder agent in a multi-agent AI system.
Your job is to generate a high-quality response (code and/or text) based on:
1. The original user task
2. The sub-tasks from the Planner
3. The research brief from the Researcher

If the task requires code, write clean, well-commented code with proper formatting.
If the task requires a text answer, be thorough and well-structured.
Use markdown formatting for readability."""


class CoderAgent(BaseAgent):
    name = "coder"

    async def run(self, context: dict, db: Session) -> str:
        task_id: str = context["task_id"]
        prompt: str = context["prompt"]
        subtasks: list[str] = context.get("subtasks", [])
        research: str = context.get("research", "")
        reviewer_feedback: str = context.get("reviewer_feedback", "")

        llm_prompt = f"User task: {prompt}\n\n"
        if subtasks:
            llm_prompt += f"Sub-tasks:\n" + "\n".join(f"- {s}" for s in subtasks) + "\n\n"
        if research:
            llm_prompt += f"Research brief:\n{research}\n\n"
        if reviewer_feedback:
            llm_prompt += f"Reviewer feedback (please address these issues):\n{reviewer_feedback}\n\n"

        llm_prompt += "Generate the response:"

        result = await self.call_llm(llm_prompt, system_prompt=SYSTEM_PROMPT)

        # Summary for agent log (full result goes to task.result via context)
        lines = [l for l in result.strip().splitlines() if l.strip()]
        preview = "\n".join(lines[:5])
        if len(lines) > 5:
            preview += f"\n... ({len(lines)} lines total)"
        output = f"Generated response ({len(result)} chars):\n{preview}"
        self.save_run(task_id, output, "done", db)

        context["coder_result"] = result
        return output
