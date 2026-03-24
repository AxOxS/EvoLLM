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

MAX_CODER_RETRIES = 2


async def run_pipeline(
    task_id: str,
    prompt: str,
    rag_enabled: bool,
    web_search_enabled: bool,
    user_id: str,
    db: Session,
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
    }

    try:
        # 1. Planner
        planner = PlannerAgent()
        await planner.run(context, db)

        # 2. Researcher
        researcher = ResearcherAgent()
        await researcher.run(context, db)

        # 3. Coder + 4. Reviewer (with retry loop)
        coder = CoderAgent()
        reviewer = ReviewerAgent()

        for attempt in range(MAX_CODER_RETRIES + 1):
            await coder.run(context, db)
            await reviewer.run(context, db)

            if context.get("approved", True):
                break

            if attempt < MAX_CODER_RETRIES:
                logger.info("Reviewer rejected (attempt %d), retrying Coder", attempt + 1)
            else:
                logger.warning("Reviewer rejected after %d attempts, using last result", MAX_CODER_RETRIES)

        # Save final result
        task.result = context.get("coder_result", "")
        task.status = "done"
        db.commit()

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
