"""Main chat page – assembles all components into the ChatGPT-like layout."""

from __future__ import annotations

from nicegui import ui, app

from frontend.styles.theme import (
    BG_SURFACE,
    ACCENT,
    AGENT_COLORS,
    GLOBAL_CSS,
    INTERACTIVE_JS,
)
from frontend.services import get_api
from frontend.components.header import create_header
from frontend.components.sidebar import create_sidebar, populate_sidebar
from frontend.components.chat_message import render_user_message, render_assistant_message
from frontend.components.agent_progress import AgentProgress
from frontend.components.chat_input import ChatInput


async def chat_page():
    """Render the main chat interface."""
    mock_api = get_api()
    ui.add_css(GLOBAL_CSS)

    # ── State ────────────────────────────────────────────────────────
    task_history = await mock_api.get_task_history()
    active_task_id = None
    processing_task_ids = set()  # tasks with active pipelines
    show_welcome = True

    # ── Logout handler ───────────────────────────────────────────────
    def handle_logout():
        app.storage.user.clear()
        ui.navigate.to("/login")

    # ── Sidebar ──────────────────────────────────────────────────────
    def handle_task_click(task):
        nonlocal active_task_id, show_welcome
        active_task_id = task.id
        show_welcome = False
        _render_task_view(task)
        refresh_sidebar()

    def _render_task_view(task):
        """Render a task's messages and show/hide progress bar accordingly."""
        messages_area.clear()
        with messages_area:
            for msg in task.messages:
                if msg.role == "user":
                    render_user_message(msg.content)
                else:
                    render_assistant_message(msg.content, msg.agent_runs)
        # Show progress bar only if THIS task is still processing
        if task.id in processing_task_ids:
            progress.show()
        else:
            progress.hide()
        _scroll_down()

    def handle_new_task():
        nonlocal active_task_id, show_welcome
        active_task_id = None
        show_welcome = True
        messages_area.clear()
        with messages_area:
            _render_welcome()
        progress.hide()
        refresh_sidebar()

    _drawer, sidebar_content = create_sidebar(on_new_task=handle_new_task)

    # ── Header (after drawer so we can pass it) ────────────────────
    create_header(on_logout_click=handle_logout, drawer=_drawer)

    def refresh_sidebar():
        populate_sidebar(
            sidebar_content,
            tasks=task_history,
            active_task_id=active_task_id,
            on_task_click=handle_task_click,
        )

    refresh_sidebar()

    # ── Main content area ────────────────────────────────────────────
    with ui.column().classes("chat-container"):

        # Messages area
        messages_area = ui.element("div").classes("messages-area")
        with messages_area:
            _render_welcome()

        # Agent progress bar
        progress = AgentProgress().create()

        # Input area
        async def handle_send(text: str):
            nonlocal active_task_id, task_history, show_welcome

            chat_input.clear()

            # Clear welcome screen on first message
            if show_welcome:
                show_welcome = False
                messages_area.clear()

            # Add user message
            with messages_area:
                render_user_message(text)
            _scroll_down()

            # Show progress for this chat
            progress.show()

            # Save current state
            rag = chat_input.rag_enabled
            web = chat_input.web_search_enabled
            send_task_id = active_task_id  # the task we're sending FROM
            # Mutable container so callbacks can read the task id
            ctx = {"task_id": send_task_id}

            async def on_task_created(task):
                """Called immediately when task is created (before pipeline)."""
                nonlocal active_task_id, task_history
                ctx["task_id"] = task.id
                active_task_id = task.id
                processing_task_ids.add(task.id)
                task_history = await mock_api.get_task_history()
                refresh_sidebar()

            async def on_agent_start(agent_name: str):
                # Only update progress bar if user is still viewing this task
                if active_task_id == ctx["task_id"]:
                    progress.set_active(agent_name)

            async def on_agent_done(agent_name: str, output: str):
                if active_task_id == ctx["task_id"]:
                    progress.set_done(agent_name)

            # Run pipeline
            task = await mock_api.submit_task(
                prompt=text,
                rag_enabled=rag,
                web_search_enabled=web,
                on_agent_start=on_agent_start,
                on_agent_done=on_agent_done,
                existing_task_id=send_task_id,
                on_task_created=on_task_created,
            )

            # Pipeline done
            processing_task_ids.discard(task.id)

            # Only update the chat view if user is still looking at this task
            if active_task_id == task.id:
                progress.hide()
                with messages_area:
                    render_assistant_message(task.result, task.agent_runs)
                _scroll_down()

            # Update sidebar (status changed from in_progress to done)
            task_history = await mock_api.get_task_history()
            refresh_sidebar()

        chat_input = ChatInput(on_send=handle_send).create()

    # ── Inject interactive JavaScript ────────────────────────────────
    ui.add_body_html(f"<script>{INTERACTIVE_JS}</script>")


def _render_welcome():
    """Render the welcome screen with real system info and agent visuals."""
    with ui.column().classes("items-center").style(
        "gap: 20px; padding: 40px 16px 20px; width: 100%;"
    ):
        ui.image("/static/images/logo.svg").style("height: 56px; width: auto; opacity: 0.9;")
        ui.label("Hello! How can I help you?").style(
            "font-size: 24px; font-weight: 700; margin-top: 4px;"
        )
        ui.label(
            "EvoLLM is a multi-agent AI system that analyzes, researches, "
            "generates and reviews your tasks using 4 specialized agents."
        ).style(
            "font-size: 15px; text-align: center; "
            "max-width: 600px; line-height: 1.7; opacity: 0.7;"
        )

        # Agent cards with SVG images
        agents_info = [
            ("/static/images/planner-agent.svg", "Planner",
             "Analyzes the task and decomposes it into structured sub-tasks.",
             AGENT_COLORS["planner"]),
            ("/static/images/researcher-agent.svg", "Researcher",
             "Searches for information in the RAG knowledge base and web (Tavily/SerpAPI).",
             AGENT_COLORS["researcher"]),
            ("/static/images/coder-agent.svg", "Coder",
             "Generates code or text responses based on collected information.",
             AGENT_COLORS["coder"]),
            ("/static/images/reviewer-agent.svg", "Reviewer",
             "Verifies result quality, logic and code. Can return for revision.",
             AGENT_COLORS["reviewer"]),
        ]

        with ui.row().classes("gap-4 justify-center").style(
            "flex-wrap: wrap; max-width: 860px;"
        ):
            for svg_path, name, desc, color in agents_info:
                with ui.element("div").classes("agent-card").style(
                    f"border: 1px solid {color}30;"
                ):
                    ui.image(svg_path).style("width: 56px; height: 56px; margin: 0 auto 10px;")
                    ui.label(name).style(f"color: {color}; font-weight: 700; font-size: 15px;")
                    ui.label(desc).style(
                        "font-size: 12px; line-height: 1.5; margin-top: 6px; opacity: 0.7;"
                    )

        # Collapsible info panel (interactive element #3)
        with ui.row().classes("items-center gap-1"):
            ui.button(
                "How does the system work?",
                on_click=lambda: ui.run_javascript("toggleInfoPanel()"),
            ).props("flat rounded dense").style(f"color: {ACCENT}; font-size: 13px;")
            ui.icon("expand_more").props('id=info-toggle-icon').style(f"color: {ACCENT};")

        with ui.element("div").classes("info-panel collapsed").props('id=info-panel'):
            ui.label("How does EvoLLM work?").style(
                "font-size: 18px; font-weight: 700; margin-bottom: 12px;"
            )
            steps = [
                ("1", "Task Submission", "The user enters a text task and chooses whether to use the RAG knowledge base and/or web search.", AGENT_COLORS["planner"]),
                ("2", "Planning (Planner)", "The Planner agent analyzes the task and decomposes it into structured sub-tasks in JSON format.", AGENT_COLORS["planner"]),
                ("3", "Research (Researcher)", "The Researcher searches for information in the ChromaDB vector database. If enabled, it also uses Tavily/SerpAPI web search.", AGENT_COLORS["researcher"]),
                ("4", "Generation (Coder)", "The Coder agent generates code or a text response based on collected information.", AGENT_COLORS["coder"]),
                ("5", "Review (Reviewer)", "The Reviewer checks the result: whether the logic is correct and the code works. Can return to Coder for fixes (up to 2 times).", AGENT_COLORS["reviewer"]),
            ]
            for num, title, desc, color in steps:
                with ui.row().classes("items-start gap-3 no-wrap").style("margin-bottom: 14px;"):
                    with ui.element("div").style(
                        f"background: {color}; color: white; border-radius: 50%; "
                        f"width: 28px; height: 28px; min-width: 28px; display: flex; align-items: center; "
                        f"justify-content: center; font-weight: 700; font-size: 14px;"
                    ):
                        ui.label(num)
                    with ui.column().classes("gap-0"):
                        ui.label(title).style("font-weight: 600; font-size: 14px;")
                        ui.label(desc).style("font-size: 13px; line-height: 1.5; opacity: 0.7;")

            ui.separator().style(f"background: {BG_SURFACE}; margin: 10px 0;")
            with ui.row().classes("gap-6 flex-wrap"):
                for tech, detail in [
                    ("Ollama", "Local LLM (llama3, mistral)"),
                    ("ChromaDB", "Vector RAG database"),
                    ("FastAPI", "Backend REST API"),
                    ("NiceGUI", "Frontend UI framework"),
                ]:
                    with ui.column().classes("gap-0"):
                        ui.label(tech).style(f"color: {ACCENT}; font-weight: 600; font-size: 13px;")
                        ui.label(detail).style("font-size: 12px; opacity: 0.7;")

        # Feature hints
        with ui.row().classes("gap-4 justify-center").style("flex-wrap: wrap;"):
            for icon, label, color in [
                ("storage", "RAG Knowledge Base", "#27AE60"),
                ("language", "Web Search", "#4A90D9"),
                ("smart_toy", "4 AI Agents", "#E67E22"),
                ("history", "Task History", "#E74C3C"),
            ]:
                with ui.element("div").style(
                    f"background: {color}12; border: 1px solid {color}25; "
                    f"border-radius: 12px; padding: 12px 18px; text-align: center;"
                ):
                    ui.icon(icon).style(f"font-size: 22px; color: {color};")
                    ui.label(label).style("font-size: 12px; margin-top: 4px; opacity: 0.7;")


def _scroll_down():
    """Scroll the messages area to the bottom."""
    ui.run_javascript(
        "setTimeout(function(){"
        "  var a = document.querySelector('.messages-area');"
        "  if(a) a.scrollTop = a.scrollHeight;"
        "}, 100)"
    )
