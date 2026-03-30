# EvoLLM Frontend

NiceGUI-based Python frontend for EvoLLM. Provides the chat interface, real-time agent progress visualization, conversation history, and RAG document management.

---

## Overview

The frontend is a single-process NiceGUI application that communicates with the FastAPI backend over HTTP. It uses browser local storage for JWT token persistence and polls the backend every 600ms to display streaming agent output and task progress.

---

## Structure

```
frontend/
├── pages/
│   ├── login.py         # Email/password login form
│   ├── register.py      # New account registration form
│   ├── chat.py          # Main chat interface (core of the app)
│   └── rag.py           # RAG document upload and management
├── components/
│   ├── agent_progress.py # Visual 4-agent progress tracker (colored status bars)
│   ├── chat_message.py   # Renders individual messages (user vs. assistant)
│   ├── chat_input.py     # Prompt input box with RAG/web search toggles
│   ├── header.py         # Top navigation bar
│   └── sidebar.py        # Conversation history sidebar (root tasks)
├── services/
│   ├── api.py            # Real HTTP client — all calls to the FastAPI backend
│   └── mock_api.py       # In-memory mock API for UI development without backend
├── styles/
│   └── theme.py          # Dark/light theme definitions and CSS utilities
├── static/
│   └── logo.png          # Application logo
└── main.py               # NiceGUI app entry point (route registration, startup)
```

---

## Pages

### Login (`pages/login.py`)

Standard email + password form. On success, stores the JWT token in browser local storage and redirects to `/chat`.

### Register (`pages/register.py`)

Registration form. Calls `POST /user/register`, then stores the returned token and redirects.

### Chat (`pages/chat.py`)

The primary interface. Key behaviors:

- **Sidebar** — lists root conversation tasks; clicking one loads the full thread
- **Message list** — renders the conversation chronologically; assistant messages show the streaming result as it builds
- **Agent progress panel** — shows the current status of each of the 4 agents (Planner, Researcher, Coder, Reviewer) with visual indicators
- **Input box** — text input with optional RAG and Web Search toggles; Enter submits
- **Polling** — a 600ms timer calls `GET /task/status/{id}` while a task is active; updates the UI with partial results

### RAG (`pages/rag.py`)

Document management for the knowledge base:

- Upload PDF, DOCX, or TXT files via drag-and-drop or file picker
- List all uploaded documents with filename, type, and size
- Delete documents (removes from both PostgreSQL and ChromaDB)

---

## Components

### `agent_progress.py`

Displays the 4-agent pipeline as a visual progress bar. Each agent transitions through states:

| State | Display |
|---|---|
| `pending` | Grey — not yet started |
| `running` | Animated — currently active |
| `done` | Green — completed successfully |
| `failed` | Red — encountered an error |

### `chat_message.py`

Renders a single message. User messages appear right-aligned; assistant messages appear left-aligned. During streaming, the component re-renders as new tokens arrive. Also shows collapsible agent run logs.

### `chat_input.py`

Input component with:
- Multi-line text area (Shift+Enter for newline, Enter to submit)
- **RAG toggle** — enable/disable document context for the task
- **Web Search toggle** — enable/disable Tavily web search (greyed out if no API key configured)

### `sidebar.py`

Lists conversations (root tasks only) grouped and labeled by AI-generated title. Clicking a conversation reloads the message list for that thread.

### `header.py`

Top navigation bar with links to Chat and RAG pages, plus a logout button that clears the local storage token.

---

## Services

### `services/api.py`

HTTP client singleton. Wraps all backend calls:

```python
# Authentication
api.register(email, password) -> token
api.login(email, password) -> token

# Tasks
api.submit_task(prompt, rag_enabled, web_search_enabled, conversation_id) -> task
api.get_task_status(task_id) -> task_with_progress
api.get_task_history() -> [task, ...]
api.get_conversation(conversation_id) -> [task, ...]
api.cancel_task(task_id)
api.delete_task(task_id)

# RAG
api.upload_document(file_bytes, filename) -> document
api.get_documents() -> [document, ...]
api.delete_document(doc_id)
```

All calls include the `Authorization: Bearer <token>` header automatically. On 401 responses, the client clears the token and redirects to `/login`.

### `services/mock_api.py`

Drop-in replacement for `api.py` that serves static in-memory data. Useful for developing UI components without running the full backend stack. To enable, swap the import in `main.py`.

---

## Real-Time Updates

There is no WebSocket connection. Updates work through polling:

1. User submits a task → `POST /task` → task created with status `pending`
2. A NiceGUI timer fires every **600ms** → `GET /task/status/{id}`
3. Response includes `result` (partial streamed text), `agent_runs`, and `subtasks`
4. UI re-renders the message and progress panel
5. Timer stops when task status is `done`, `failed`, or `cancelled`

The backend flushes the Coder's streamed output to the database every **400ms**, so end-to-end latency from LLM token to visible UI character is approximately 1 second.

---

## Running Locally

```bash
# From repo root
pip install -r requirements.txt
python run.py --frontend
```

The app will be available at [http://localhost:8080](http://localhost:8080).

To run without the backend (mock mode), set the mock API in `frontend/main.py`:

```python
# Change this import in frontend/main.py:
from frontend.services.mock_api import api
```

---

## Styling

Themes are defined in `styles/theme.py`. The app supports dark and light modes via NiceGUI's built-in theme system. Custom CSS is scoped to components using NiceGUI's `ui.add_css()` helper.

The color palette and spacing follow Quasar conventions (NiceGUI's underlying component framework). Utility classes from Tailwind-style shorthands are available for layout within NiceGUI element classes.
