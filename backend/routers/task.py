"""Task endpoints – submit, status, history, detail."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db, SessionLocal
from backend.models import User, Task
from backend.schemas import TaskCreate, TaskResponse, TaskStatusResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/task", tags=["tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(
    req: TaskCreate,
    bg: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # FR-15: one active task per user
    active = db.query(Task).filter(
        Task.user_id == user.id, Task.status.in_(["pending", "in_progress"])
    ).first()
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active task. Please wait for it to finish.",
        )

    task = Task(user_id=user.id, task_prompt=req.prompt, status="pending")
    db.add(task)
    db.flush()  # get the generated id before commit
    # conversation_id: use provided value for follow-ups, or self-id for new conversations
    task.conversation_id = req.conversation_id or task.id
    db.commit()
    db.refresh(task)

    # Serialize chat history for background task
    history = [{"role": m.role, "content": m.content} for m in req.chat_history]

    # Launch pipeline in background so the endpoint returns immediately
    bg.add_task(
        _run_pipeline_background,
        task.id,
        req.prompt,
        req.rag_enabled,
        req.web_search_enabled,
        user.id,
        history,
    )

    return task


def _run_pipeline_background(
    task_id: str,
    prompt: str,
    rag_enabled: bool,
    web_search_enabled: bool,
    user_id: str,
    chat_history: list[dict] | None = None,
):
    """Wrapper that runs the async orchestrator in a fresh event loop + DB session."""
    from backend.services.orchestrator import run_pipeline

    db = SessionLocal()
    try:
        asyncio.run(run_pipeline(task_id, prompt, rag_enabled, web_search_enabled, user_id, db, chat_history or []))
    finally:
        db.close()


@router.get("/history", response_model=list[TaskResponse])
def task_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id)
        .order_by(Task.created_at.desc())
        .all()
    )
    return tasks


@router.get("/conversation/{conversation_id}", response_model=list[TaskResponse])
def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all tasks in a conversation, ordered chronologically."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.conversation_id == conversation_id)
        .order_by(Task.created_at.asc())
        .all()
    )
    return tasks


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def task_status(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status in ("pending", "in_progress"):
        task.status = "cancelled"
        db.commit()
    return {"ok": True}


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
