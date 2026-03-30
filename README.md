# EvoLLM

A multi-agent AI assistant that processes user tasks through a 4-stage pipeline: **Planner → Researcher → Coder → Reviewer**. Built with FastAPI, NiceGUI, PostgreSQL, ChromaDB, and Ollama for fully local LLM inference.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Development](#local-development)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Backend Docs →](backend/README.md)
  - [Agent Pipeline](backend/README.md#agent-pipeline)
  - [API Endpoints](backend/README.md#api-endpoints)
  - [Data Models](backend/README.md#data-models)
  - [Services](backend/README.md#services)
  - [Authentication](backend/README.md#authentication)
  - [Environment Variables](backend/README.md#environment-variables)
- [Frontend Docs →](frontend/README.md)
  - [Pages](frontend/README.md#pages)
  - [Components](frontend/README.md#components)
  - [Real-Time Updates](frontend/README.md#real-time-updates)
  - [Mock API (dev mode)](frontend/README.md#services)
- [Server Migration →](MIGRATION.md)
  - [Exporting Data](MIGRATION.md#2-duomenų-eksportavimas-iš-seno-serverio)
  - [Installing on New Server](MIGRATION.md#3-diegimas-naujoje-aplinkoje)
  - [Post-Migration Checklist](MIGRATION.md#4-migravimo-patikrinimo-testai)

---

## Overview

EvoLLM is a self-hosted AI assistant that decomposes complex tasks into structured subtasks, then processes them through specialized agents. It supports:

- **Multi-agent task processing** with transparent per-agent progress
- **Retrieval-Augmented Generation (RAG)** from your own documents (PDF, DOCX, TXT)
- **Optional web search** via Tavily for up-to-date information
- **Conversation threading** for contextual multi-turn interactions
- **Real-time streaming** of agent responses

---

## Architecture

```
User Prompt
     │
     ▼
┌─────────────┐
│   Planner   │  Decomposes the task into a JSON array of subtasks
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Researcher  │  Queries RAG documents + optional web search for context
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Coder    │  Generates the final response (streams tokens in real time)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Reviewer   │  Validates output — approves or retries Coder (max 5 times)
└──────┬──────┘
       │
       ▼
  Final Result
```

The backend flushes streaming output to the database every **400ms**. The frontend polls task status every **600ms**. See [Frontend Docs → Real-Time Updates](frontend/README.md#real-time-updates) for the full flow.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (async Python) |
| Frontend UI | NiceGUI 2.0+ (Quasar-based) |
| Relational DB | PostgreSQL 15 |
| Vector Store | ChromaDB |
| LLM Inference | Ollama (local, no external API required) |
| Default Models | `qwen3:0.6b` (small tasks), `qwen3.5:9b` (main agents) |
| Authentication | JWT + bcrypt |
| Web Search | Tavily API (optional) |
| Containerization | Docker + Docker Compose |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- NVIDIA drivers + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for GPU acceleration
- Python 3.12+ for local development (Docker handles this automatically)

### Docker (Recommended)

**1. Clone the repository**

```bash
git clone https://github.com/your-org/EvoLLM.git
cd EvoLLM
```

**2. Configure environment**

```bash
cp .env.example .env
# Edit .env — at minimum set a strong JWT_SECRET
```

**3. Start all services**

```bash
docker compose up --build -d
```

**4. Pull Ollama models** (first run only — models are large, allow time to download)

```bash
docker exec evollm-ollama-1 ollama pull qwen3:0.6b
docker exec evollm-ollama-1 ollama pull qwen3.5:9b
```

**5. Open the app**

| Service | URL |
|---|---|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

**Useful commands**

```bash
docker compose logs -f           # Stream all service logs
docker compose logs -f backend   # Backend logs only
docker compose ps                # Check container statuses
docker compose down              # Stop all services
docker compose down -v           # Stop and wipe all volumes (destructive)
```

---

### Local Development

**1. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**2. Start external services via Docker**

```bash
docker compose up postgres ollama -d
```

**3. Configure `.env`** (see [Configuration](#configuration) below)

**4. Run the application**

```bash
python run.py              # Both backend and frontend
python run.py --backend    # FastAPI only  → http://localhost:8000
python run.py --frontend   # NiceGUI only  → http://localhost:8080
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/evollm` | PostgreSQL connection string |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL_SMALL` | `qwen3:0.6b` | Fast model — used for planning and title generation |
| `OLLAMA_MODEL_BIG` | `qwen3.5:9b` | Smart model — used for research, coding, and review |
| `CHROMADB_PATH` | `./chroma_data` | Local path for ChromaDB persistence |
| `JWT_SECRET` | `change-me-in-production` | **Must be changed before deploying** |
| `JWT_EXPIRE_HOURS` | `24` | Token lifetime in hours |
| `TAVILY_API_KEY` | *(empty)* | Optional — enables web search in the Researcher agent |

> **Note:** If you are migrating to a new server, `JWT_SECRET` must stay the same or all existing user sessions will be invalidated. See [Server Migration](MIGRATION.md#32-konfigūracijos-atnaujinimas).

---

## Usage

### Chat

1. Register or log in at [http://localhost:8080](http://localhost:8080)
2. Type a prompt and press Enter
3. Watch the 4-agent pipeline execute in the progress panel
4. The final answer streams in as the Coder generates tokens

### RAG — Using Your Own Documents

1. Go to the **RAG** page from the header
2. Upload PDF, DOCX, or TXT files
3. Back in Chat, enable the **RAG** toggle before submitting
4. The Researcher agent will search your documents for relevant context

### Web Search

Toggle **Web Search** in the chat input. Requires `TAVILY_API_KEY` set in `.env`.

### Conversations

- The left sidebar lists your previous conversations by AI-generated title
- Clicking a conversation loads its full message thread
- New messages sent within an open conversation automatically carry chat history to all agents

---

## Project Structure

```
EvoLLM/
├── backend/                   # FastAPI backend
│   ├── agents/                # Planner, Researcher, Coder, Reviewer + BaseAgent
│   ├── routers/               # API route handlers (user, task, rag)
│   ├── services/              # Orchestrator, LLM client, RAG service, web search
│   ├── main.py                # App factory, CORS, DB lifespan hooks
│   ├── models.py              # SQLAlchemy ORM (5 tables)
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── auth.py                # JWT + bcrypt auth
│   ├── config.py              # Settings from .env
│   └── database.py            # Engine and session factory
│
├── frontend/                  # NiceGUI frontend
│   ├── pages/                 # Login, Register, Chat, RAG
│   ├── components/            # AgentProgress, ChatMessage, ChatInput, Header, Sidebar
│   ├── services/              # api.py (real), mock_api.py (dev)
│   ├── styles/                # Theme and CSS utilities
│   └── main.py                # Route registration, app startup
│
├── docker-compose.yml         # Orchestrates postgres, ollama, backend, frontend
├── Dockerfile.backend
├── Dockerfile.frontend
├── run.py                     # Development runner (--backend / --frontend flags)
├── requirements.txt
├── .env.example
├── MIGRATION.md               # Server migration guide
├── backend/README.md          # Backend deep-dive →
└── frontend/README.md         # Frontend deep-dive →
```

### Docker volumes

| Volume | Contents | Migrate? |
|---|---|---|
| `evollm_postgres_data` | Users, tasks, document metadata | Yes |
| `evollm_chroma_data` | Vector embeddings (RAG) | Yes |
| `evollm_ollama_data` | LLM model weights | No — re-download on new host |

---

## Further Reading

| Document | Description |
|---|---|
| [backend/README.md](backend/README.md) | Agent pipeline, all API endpoints, database schema, services |
| [frontend/README.md](frontend/README.md) | Pages, components, polling/streaming flow, mock API |
| [MIGRATION.md](MIGRATION.md) | Full step-by-step guide for moving to a new server |
