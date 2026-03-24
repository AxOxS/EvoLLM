"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    email: str


# ── Task ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    prompt: str
    rag_enabled: bool = True
    web_search_enabled: bool = False


class SubtaskResponse(BaseModel):
    id: str
    description: str
    order_index: int
    status: str

    model_config = {"from_attributes": True}


class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    output: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: str
    task_prompt: str
    status: str
    result: str
    created_at: datetime
    agent_runs: list[AgentRunResponse] = []
    subtasks: list[SubtaskResponse] = []

    model_config = {"from_attributes": True}


class TaskStatusResponse(BaseModel):
    id: str
    status: str
    agent_runs: list[AgentRunResponse] = []
    subtasks: list[SubtaskResponse] = []

    model_config = {"from_attributes": True}


# ── RAG ───────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    size_kb: float
    doc_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
