# EvoLLM Backend

FastAPI backend for EvoLLM. Handles authentication, task orchestration through the 4-agent AI pipeline, RAG document management, and real-time streaming.

---

## Overview

The backend exposes a REST API consumed by the NiceGUI frontend. Tasks submitted by users are processed asynchronously in background threads by the **Orchestrator**, which runs the Planner → Researcher → Coder → Reviewer agent pipeline.

---

## Structure

```
backend/
├── agents/
│   ├── base.py          # Abstract BaseAgent — LLM calls, DB run persistence
│   ├── planner.py       # Decomposes user prompt into a JSON subtask list
│   ├── researcher.py    # Gathers context from RAG + optional web search
│   ├── coder.py         # Generates final response; streams tokens to DB
│   └── reviewer.py      # Validates Coder output; approves or sends feedback
├── routers/
│   ├── user.py          # POST /user/register, POST /user/login
│   ├── task.py          # Task lifecycle (submit, status, history, cancel, delete)
│   └── rag.py           # Document upload, list, delete
├── services/
│   ├── orchestrator.py  # Runs the agent pipeline, handles retries
│   ├── llm.py           # Ollama HTTP client (blocking generate + streaming)
│   ├── rag_service.py   # ChromaDB wrapper (chunk, embed, query, delete)
│   └── web_search.py    # Tavily API client (optional web search)
├── main.py              # FastAPI app instantiation, CORS, DB lifespan hooks
├── models.py            # SQLAlchemy ORM table definitions
├── schemas.py           # Pydantic request/response models
├── auth.py              # JWT generation, bcrypt verification, user dependency
├── config.py            # Settings object loaded from .env
└── database.py          # SQLAlchemy engine, session factory, get_db dependency
```

---

## Agent Pipeline

Each agent extends `BaseAgent` and must implement `run(task, db)`.

### 1. Planner (`agents/planner.py`)

- **Model:** `OLLAMA_MODEL_SMALL`
- **Input:** User task prompt
- **Output:** JSON array of subtask descriptions, saved to the `subtasks` table
- **Purpose:** Structured decomposition so downstream agents work on focused chunks

### 2. Researcher (`agents/researcher.py`)

- **Model:** `OLLAMA_MODEL_BIG`
- **Input:** Task prompt + subtasks + (optional) RAG chunks + (optional) web search results
- **Output:** A context brief summarizing relevant information
- **RAG:** Queries ChromaDB for top-5 document chunks (cosine distance)
- **Web:** Calls Tavily if `web_search_enabled` is set on the task

### 3. Coder (`agents/coder.py`)

- **Model:** `OLLAMA_MODEL_BIG`
- **Input:** Task prompt + researcher brief + conversation history
- **Output:** Streamed final response, flushed to `tasks.result` every 0.4 seconds
- **Streaming:** Uses Ollama `/api/generate?stream=true` with token accumulation

### 4. Reviewer (`agents/reviewer.py`)

- **Model:** `OLLAMA_MODEL_BIG`
- **Input:** Original task + Coder output
- **Output:** JSON `{"approved": true/false, "feedback": "..."}`
- **Retry logic:** If not approved, feedback is passed back to Coder; up to 5 retry attempts total

---

## Data Models

### `users`
| Column | Type | Notes |
|---|---|---|
| id | String | 12-char hex |
| email | String | Unique |
| password_hash | String | bcrypt |
| created_at | DateTime | UTC |

### `tasks`
| Column | Type | Notes |
|---|---|---|
| id | String | 12-char hex |
| user_id | String | FK → users |
| task_prompt | String | User's input |
| status | String | pending / in_progress / done / failed / cancelled |
| result | Text | Final output (streamed, flushed periodically) |
| conversation_id | String | Groups related tasks; root task's own id for roots |
| title | String | AI-generated title (small model, root tasks only) |
| rag_enabled | Boolean | Whether RAG was enabled for this task |
| web_search_enabled | Boolean | Whether web search was enabled |
| created_at | DateTime | UTC |

### `agent_runs`
| Column | Type | Notes |
|---|---|---|
| id | String | 12-char hex |
| task_id | String | FK → tasks |
| agent_name | String | planner / researcher / coder / reviewer / orchestrator |
| output | Text | Agent log text |
| status | String | running / done / failed |
| created_at | DateTime | UTC |

### `subtasks`
| Column | Type | Notes |
|---|---|---|
| id | String | 12-char hex |
| task_id | String | FK → tasks |
| description | String | Subtask text from Planner |
| order_index | Integer | Sequence position |
| status | String | pending / done |

### `documents`
| Column | Type | Notes |
|---|---|---|
| id | String | 12-char hex |
| user_id | String | FK → users |
| filename | String | Original filename |
| content_text | Text | Extracted plain text |
| doc_type | String | pdf / txt / docx |
| size_kb | Float | File size |
| chromadb_id | String | Collection ID in ChromaDB |
| uploaded_at | DateTime | UTC |

---

## API Endpoints

All endpoints except `/user/register`, `/user/login`, and `/health` require:

```
Authorization: Bearer <jwt_token>
```

### User

```
POST /user/register
  Body: { "email": "...", "password": "..." }
  Returns: { "access_token": "...", "token_type": "bearer" }

POST /user/login
  Body: { "email": "...", "password": "..." }
  Returns: { "access_token": "...", "token_type": "bearer" }
```

### Tasks

```
POST /task
  Body: {
    "task_prompt": "...",
    "rag_enabled": false,
    "web_search_enabled": false,
    "chat_history": [],       # optional conversation context
    "conversation_id": null   # omit to start a new conversation
  }
  Returns: Task object (status: pending)

GET /task/history
  Returns: List of root Task objects for the current user

GET /task/conversation/{conversation_id}
  Returns: Ordered list of all Tasks in a conversation thread

GET /task/status/{task_id}
  Returns: Task with partial result + agent_runs + subtasks (for polling)

GET /task/{task_id}
  Returns: Full Task object

POST /task/{task_id}/cancel
  Cancels an in-progress task

DELETE /task/{task_id}
  Deletes task and cascades to agent_runs/subtasks
```

### RAG

```
POST /rag/upload
  Body: multipart/form-data with file (PDF, DOCX, or TXT)
  Returns: Document metadata object

GET /rag/documents
  Returns: List of Document objects for the current user

DELETE /rag/documents/{doc_id}
  Removes document metadata from DB and embeddings from ChromaDB
```

### Health

```
GET /health
  Returns: { "status": "ok" }
```

---

## Services

### `services/orchestrator.py`

The central coordinator. Called in a `BackgroundTasks` thread after task creation:

1. Sets task status to `in_progress`
2. Runs Planner → saves subtasks
3. Runs Researcher → builds context brief
4. Runs Coder → streams result to DB
5. Runs Reviewer → if rejected, retries Coder with feedback (max 5 total attempts)
6. Sets final status to `done` or `failed`

### `services/llm.py`

Thin async wrapper around Ollama's HTTP API:

- `generate(model, prompt)` → blocking, returns full response text
- `generate_stream(model, prompt)` → async generator yielding token strings

### `services/rag_service.py`

ChromaDB operations:

- `add_document(user_id, doc_id, text)` → chunks text (500 chars, 50 overlap), embeds and stores
- `query(user_id, query_text, n_results=5)` → semantic search, returns top chunks
- `delete_document(doc_id)` → removes all chunks for a document

### `services/web_search.py`

Calls Tavily `/search` endpoint. Returns a list of `{title, url, content}` dicts. No-op if `TAVILY_API_KEY` is unset.

---

## Authentication

- Passwords hashed with **bcrypt** (cost factor 12)
- JWT tokens signed with `JWT_SECRET`, expire after `JWT_EXPIRE_HOURS`
- `auth.get_current_user` FastAPI dependency — inject into any route handler to require authentication

---

## Running Locally

```bash
# From repo root
pip install -r requirements.txt

# Requires PostgreSQL and Ollama to be accessible (see .env)
python run.py --backend
# or
uvicorn backend.main:app --reload --port 8000
```

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OLLAMA_URL` | Yes | Ollama base URL |
| `OLLAMA_MODEL_SMALL` | Yes | Fast model (planning, titling) |
| `OLLAMA_MODEL_BIG` | Yes | Smart model (research, coding, review) |
| `CHROMADB_PATH` | Yes | Directory for ChromaDB persistence |
| `JWT_SECRET` | Yes | **Must be changed in production** |
| `JWT_EXPIRE_HOURS` | No | Default: 24 |
| `TAVILY_API_KEY` | No | Enables web search if set |
