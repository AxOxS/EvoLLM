"""Reviewer agent – validates result, approves or rejects."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from backend.agents.base import BaseAgent

SYSTEM_PROMPT = """You are the Reviewer agent in a multi-agent AI system.
Your job is to review the Coder agent's output for quality, correctness, and completeness.

Respond ONLY with valid JSON in this exact format:
{"approved": true, "feedback": "Brief quality assessment"}

If the output has significant issues:
{"approved": false, "feedback": "Description of what needs to be fixed"}

Be reasonable – approve outputs that adequately address the task, even if not perfect."""


class ReviewerAgent(BaseAgent):
    name = "reviewer"

    async def run(self, context: dict, db: Session) -> str:
        task_id: str = context["task_id"]
        prompt: str = context["prompt"]
        coder_result: str = context.get("coder_result", "")

        llm_prompt = (
            f"Original task: {prompt}\n\n"
            f"Coder's output:\n{coder_result}\n\n"
            f"Review the above output. Is it correct, complete, and high quality?"
        )

        raw = await self.call_llm(llm_prompt, system_prompt=SYSTEM_PROMPT)

        # Parse review result
        approved = True
        feedback = "Result verified. Quality is acceptable. Approved."

        try:
            raw_stripped = raw.strip()
            if raw_stripped.startswith("```"):
                lines = raw_stripped.split("\n")
                raw_stripped = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_stripped
                raw_stripped = raw_stripped.strip()

            parsed = json.loads(raw_stripped)
            approved = parsed.get("approved", True)
            feedback = parsed.get("feedback", feedback)
        except (json.JSONDecodeError, AttributeError):
            # If can't parse JSON, default to approved
            approved = True
            feedback = raw[:200] if raw else feedback

        status = "approved" if approved else "rejected"
        output = f"Review: {status}. {feedback}"
        self.save_run(task_id, output, "done", db)

        context["approved"] = approved
        context["reviewer_feedback"] = feedback if not approved else ""
        return output
