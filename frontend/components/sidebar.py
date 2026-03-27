"""Left sidebar – task history list (ChatGPT-style)."""

from __future__ import annotations

from nicegui import ui

from frontend.styles.theme import BG_SURFACE


def create_sidebar(on_new_task=None):
    """Create the left drawer (must be called as direct child of the page).

    Returns (drawer, content_container) – populate content_container
    via ``populate_sidebar()``.
    """
    drawer = ui.left_drawer(value=True, bordered=False).classes("q-pa-none sidebar-drawer").style(
        f"width: 260px; border-right: 1px solid {BG_SURFACE};"
    )
    with drawer:
        # New task button
        with ui.column().classes("w-full items-center").style("padding: 16px;"):
            ui.button(
                "New Task",
                icon="add",
                on_click=on_new_task,
            ).props("unelevated rounded").classes("w-full sidebar-new-btn")

        # Divider
        ui.separator()

        # Scrollable task list container
        content = ui.column().classes("w-full q-pa-sm gap-1")

    return drawer, content


def populate_sidebar(
    container,
    tasks: list,
    active_task_id: str | None = None,
    on_task_click=None,
    on_task_delete=None,
):
    """Fill the sidebar content container with task items."""
    container.clear()
    with container:
        ui.label("Task History").style(
            "font-size: 12px; text-transform: uppercase; letter-spacing: 1px; "
            "padding: 4px 10px; opacity: 0.6;"
        )

        if not tasks:
            ui.label("No tasks yet").style(
                "font-size: 13px; padding: 10px; opacity: 0.6;"
            )
        else:
            for task in tasks:
                _render_task_item(task, active_task_id, on_task_click, on_task_delete)


def _render_task_item(task, active_task_id, on_task_click, on_task_delete):
    """Render a single task entry in the sidebar."""
    is_active = task.id == active_task_id
    css_class = "sidebar-item active" if is_active else "sidebar-item"

    with ui.element("div").classes(css_class).style(
        "position: relative; width: 100%; box-sizing: border-box; padding-right: 28px;"
    ):
        with ui.element("div").style(
            "cursor: pointer; width: 100%;"
        ).on("click", lambda t=task: on_task_click(t) if on_task_click else None):
            label_text = task.prompt[:40] + ("..." if len(task.prompt) > 40 else "")
            ui.label(label_text).style("font-size: 14px;")
            ui.label(task.created_at).style(
                "font-size: 11px; margin-top: 2px; opacity: 0.6;"
            )
        if on_task_delete:
            ui.button(
                icon="close",
                on_click=lambda t=task: on_task_delete(t),
            ).props("flat round dense size=xs").style(
                "position: absolute; top: 50%; right: 4px; transform: translateY(-50%); "
                "opacity: 0.3; min-width: 20px;"
            )
