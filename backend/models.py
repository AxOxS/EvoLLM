"""ORM models – 5 tables per ER diagram."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(12), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(12), primary_key=True, default=_uuid)
    user_id = Column(String(12), ForeignKey("users.id"), nullable=False)
    task_prompt = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending / in_progress / done / failed / cancelled
    result = Column(Text, default="")
    conversation_id = Column(String(12), nullable=True)  # root task id to group conversations
    title = Column(String(255), nullable=True)  # AI-generated conversation title
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="tasks")
    agent_runs = relationship("AgentRun", back_populates="task", cascade="all, delete-orphan", order_by="AgentRun.created_at")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan", order_by="Subtask.order_index")

    __table_args__ = (Index("ix_tasks_user_status", "user_id", "status"),)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(12), primary_key=True, default=_uuid)
    task_id = Column(String(12), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(20), nullable=False)  # planner / researcher / coder / reviewer
    output = Column(Text, default="")
    status = Column(String(20), default="running")  # running / done / failed
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    task = relationship("Task", back_populates="agent_runs")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(String(12), primary_key=True, default=_uuid)
    task_id = Column(String(12), ForeignKey("tasks.id"), nullable=False)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending / done

    task = relationship("Task", back_populates="subtasks")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(12), primary_key=True, default=_uuid)
    user_id = Column(String(12), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_text = Column(Text, default="")
    doc_type = Column(String(10), default="txt")  # pdf / txt / docx
    size_kb = Column(Float, default=0.0)
    chromadb_id = Column(String(64), default="")
    uploaded_at = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="documents")
