"""Agent pipeline orchestrator – runs the 4-agent sequential pipeline."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.models import Task
from backend.agents.planner import PlannerAgent
from backend.agents.researcher import ResearcherAgent
from backend.agents.coder import CoderAgent
from backend.agents.reviewer import ReviewerAgent

logger = logging.getLogger(__name__)

MAX_CODER_RETRIES = 5

TITLE_SYSTEM_PROMPT = (
    "Generate a very short title (3-6 words) for a conversation that starts with "
    "the user message below. Return ONLY the title text, nothing else. "
    "No quotes, no punctuation at the end, no explanation."
)


async def run_pipeline(
    task_id: str,
    prompt: str,
    rag_enabled: bool,
    web_search_enabled: bool,
    user_id: str,
    db: Session,
    chat_history: list[dict] | None = None,
):
    """Execute the full 4-agent pipeline for a task.

    Flow: Planner → Researcher → Coder → Reviewer
    If Reviewer rejects, loops back to Coder (max 2 retries).
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        logger.error("Task %s not found", task_id)
        return

    task.status = "in_progress"
    db.commit()

    context = {
        "task_id": task_id,
        "prompt": prompt,
        "rag_enabled": rag_enabled,
        "web_search_enabled": web_search_enabled,
        "user_id": user_id,
        "chat_history": chat_history or [],
    }

    def _is_cancelled() -> bool:
        """Check if the task has been cancelled by the user."""
        db.refresh(task)
        return task.status == "cancelled"

    try:
        # 1. Planner
        if _is_cancelled():
            return
        planner = PlannerAgent()
        await planner.run(context, db)

        # 2. Researcher
        if _is_cancelled():
            return
        researcher = ResearcherAgent()
        await researcher.run(context, db)

        # 3. Coder + 4. Reviewer (with retry loop)
        coder = CoderAgent()
        reviewer = ReviewerAgent()

        for attempt in range(MAX_CODER_RETRIES + 1):
            if _is_cancelled():
                return
            await coder.run(context, db)

            if _is_cancelled():
                return
            await reviewer.run(context, db)

            if context.get("approved", True):
                break

            if attempt < MAX_CODER_RETRIES:
                logger.info("Reviewer rejected (attempt %d), retrying Coder", attempt + 1)
            else:
                logger.warning("Reviewer rejected after %d attempts, using last result", MAX_CODER_RETRIES)

        # Check one final time before saving
        if _is_cancelled():
            return

        # Save final result
        task.result = context.get("coder_result", "")
        task.status = "done"
        db.commit()

        # Generate a conversation title for root tasks (conversation_id == task.id)
        if task.conversation_id == task.id:
            await _generate_title(task, db)

    except Exception as e:
        logger.exception("Pipeline failed for task %s: %s", task_id, e)
        task.status = "failed"
        task.result = f"Pipeline error: {e}"
        db.commit()

        # Record the failure as an agent run
        from backend.models import AgentRun
        fail_run = AgentRun(
            task_id=task_id,
            agent_name="orchestrator",
            output=f"Pipeline failed: {e}",
            status="failed",
        )
        db.add(fail_run)
        db.commit()


async def _generate_title(task: Task, db: Session):
    """Generate a short title for the conversation using the small model."""
    from backend.services.llm import generate

    try:
        raw = await generate(task.task_prompt, system_prompt=TITLE_SYSTEM_PROMPT)
        # Clean up: take first line, strip quotes/whitespace
        title = raw.strip().splitlines()[0].strip().strip('"').strip("'")
        if len(title) > 80:
            title = title[:77] + "..."
        task.title = title
        db.commit()
    except Exception as e:
        logger.warning("Title generation failed for task %s: %s", task.id, e)
