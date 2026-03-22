"""EvoLLM Frontend – NiceGUI application entry point."""

from pathlib import Path

from nicegui import ui, app

from frontend.pages.login import login_page
from frontend.pages.register import register_page
from frontend.pages.chat import chat_page
from frontend.pages.rag import rag_page

# ── Static files ─────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.add_static_files("/static", str(STATIC_DIR))

# ── Auth middleware ──────────────────────────────────────────────────
UNPROTECTED = {"/login", "/register"}


@app.middleware("http")
async def auth_guard(request, call_next):
    """Redirect unauthenticated users to login (except auth pages)."""
    if not request.url.path.startswith("/_nicegui") and request.url.path not in UNPROTECTED:
        pass
    return await call_next(request)


# ── Pages ────────────────────────────────────────────────────────────

@ui.page("/login")
def _login():
    login_page()


@ui.page("/register")
def _register():
    register_page()


@ui.page("/")
async def _chat():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    await chat_page()


@ui.page("/rag")
async def _rag():
    token = app.storage.user.get("token")
    if not token:
        ui.navigate.to("/login")
        return
    await rag_page()


# ── Run ──────────────────────────────────────────────────────────────
ui.run(
    title="EvoLLM",
    port=8080,
    dark=True,
    storage_secret="evollm-dev-secret-change-me",
    favicon="🤖",
)
