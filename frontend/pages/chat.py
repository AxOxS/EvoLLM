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
    all_tasks = await mock_api.get_task_history()
    # Sidebar shows only root tasks (first message in each conversation)
    task_history = [t for t in all_tasks if not t.conversation_id or t.conversation_id == t.id]
    active_task_id = None
    processing_task_ids = set()  # tasks with active pipelines
    show_welcome = True
    conversation_messages: list[dict] = []  # tracks current conversation for context
    conversation_root_id: str | None = None  # first task ID in current conversation

    # ── Logout handler ───────────────────────────────────────────────
    def handle_logout():
        app.storage.user.clear()
        ui.navigate.to("/login")

    # ── Sidebar ──────────────────────────────────────────────────────
    async def handle_task_click(task):
        nonlocal active_task_id, show_welcome, conversation_messages, conversation_root_id
        conv_id = task.conversation_id or task.id
        active_task_id = task.id
        conversation_root_id = conv_id
        show_welcome = False

        # Load all tasks in this conversation to rebuild full chat history
        conv_tasks = await mock_api.get_conversation(conv_id)
        if not conv_tasks:
            conv_tasks = [task]

        # Rebuild conversation_messages and render all messages
        conversation_messages = []
        messages_area.clear()
        with messages_area:
            for t in conv_tasks:
                for msg in t.messages:
                    conversation_messages.append({"role": msg.role, "content": msg.content})
                    if msg.role == "user":
                        render_user_message(msg.content)
                    else:
                        render_assistant_message(msg.content, msg.agent_runs)

        # Track last task id for progress display
        if conv_tasks:
            active_task_id = conv_tasks[-1].id

        if active_task_id in processing_task_ids:
            progress.show()
        else:
            progress.hide()
        _scroll_down()
        refresh_sidebar()

    def handle_new_task():
        nonlocal active_task_id, show_welcome, conversation_messages, conversation_root_id
        active_task_id = None
        conversation_root_id = None
        show_welcome = True
        conversation_messages = []
        messages_area.clear()
        with messages_area:
            _render_welcome()
        progress.hide()
        refresh_sidebar()

    async def handle_task_delete(task):
        nonlocal active_task_id, task_history, show_welcome, conversation_messages, conversation_root_id
        # Delete all tasks in the conversation
        conv_id = task.conversation_id or task.id
        conv_tasks = await mock_api.get_conversation(conv_id)
        for t in conv_tasks:
            await mock_api.delete_task(t.id)
        if not conv_tasks:
            await mock_api.delete_task(task.id)
        all_tasks = await mock_api.get_task_history()
        task_history = [t for t in all_tasks if not t.conversation_id or t.conversation_id == t.id]
        if active_task_id == task.id or conversation_root_id == conv_id:
            active_task_id = None
            conversation_root_id = None
            show_welcome = True
            conversation_messages = []
            messages_area.clear()
            with messages_area:
                _render_welcome()
            progress.hide()
        refresh_sidebar()

    _drawer, sidebar_content = create_sidebar(on_new_task=handle_new_task)

    # ── Header (after drawer so we can pass it) ────────────────────
    create_header(on_logout_click=handle_logout, drawer=_drawer)

    def refresh_sidebar():
        # Use conversation_root_id for active highlighting (sidebar shows root tasks)
        highlight_id = conversation_root_id or active_task_id
        populate_sidebar(
            sidebar_content,
            tasks=task_history,
            active_task_id=highlight_id,
            on_task_click=handle_task_click,
            on_task_delete=handle_task_delete,
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
            nonlocal active_task_id, task_history, show_welcome, conversation_messages

            chat_input.clear()

            # Clear welcome screen on first message
            if show_welcome:
                show_welcome = False
                messages_area.clear()

            # Add user message to view and conversation history
            with messages_area:
                render_user_message(text)
            _scroll_down()

            # Build chat_history from previous conversation (before this message)
            history_for_api = list(conversation_messages)
            # Add current user message to conversation tracking
            conversation_messages.append({"role": "user", "content": text})

            # Show progress and switch to cancel mode
            progress.show()
            chat_input.set_processing(True)

            # Save current state
            rag = chat_input.rag_enabled
            web = chat_input.web_search_enabled
            is_follow_up = len(conversation_messages) > 1  # >1 because we just appended user msg
            # Mutable container so callbacks can read the task id
            ctx = {"task_id": active_task_id}

            async def on_task_created(task):
                """Called immediately when task is created (before pipeline)."""
                nonlocal active_task_id, task_history, conversation_root_id
                ctx["task_id"] = task.id
                active_task_id = task.id
                processing_task_ids.add(task.id)
                if not is_follow_up:
                    conversation_root_id = task.id
                    all_tasks = await mock_api.get_task_history()
                    task_history = [t for t in all_tasks if not t.conversation_id or t.conversation_id == t.id]
                    refresh_sidebar()

            async def on_agent_start(agent_name: str):
                if active_task_id == ctx["task_id"]:
                    progress.set_active(agent_name)

            async def on_agent_done(agent_name: str, output: str):
                if active_task_id == ctx["task_id"]:
                    progress.set_done(agent_name)

            # Run pipeline with chat history and conversation grouping
            task = await mock_api.submit_task(
                prompt=text,
                rag_enabled=rag,
                web_search_enabled=web,
                on_agent_start=on_agent_start,
                on_agent_done=on_agent_done,
                on_task_created=on_task_created,
                chat_history=history_for_api,
                conversation_id=conversation_root_id if is_follow_up else None,
            )

            # Pipeline done – restore send button
            processing_task_ids.discard(task.id)
            chat_input.set_processing(False)

            # Handle cancelled tasks
            if task.status == "cancelled":
                if active_task_id == task.id:
                    progress.hide()
                    with messages_area:
                        render_assistant_message("*Query cancelled.*", [])
                    _scroll_down()
                conversation_messages.append({"role": "assistant", "content": "Query cancelled."})
                return

            # Add assistant response to conversation tracking
            conversation_messages.append({"role": "assistant", "content": task.result})

            # Only update the chat view if user is still looking at this task
            if active_task_id == task.id:
                progress.hide()
                with messages_area:
                    render_assistant_message(task.result, task.agent_runs)
                _scroll_down()

            # Update sidebar only for new conversations (not follow-ups)
            if not is_follow_up:
                all_tasks = await mock_api.get_task_history()
                task_history = [t for t in all_tasks if not t.conversation_id or t.conversation_id == t.id]
                refresh_sidebar()

        async def handle_cancel():
            """Cancel the currently running task."""
            task_id = active_task_id
            if task_id and task_id in processing_task_ids:
                await mock_api.cancel_task(task_id)

        chat_input = ChatInput(on_send=handle_send, on_cancel=handle_cancel).create()

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
