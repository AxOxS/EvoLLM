"""Chat message bubble component – user and assistant messages."""

from __future__ import annotations

from nicegui import ui

from frontend.styles.theme import (
    AGENT_COLORS,
    AGENT_LABELS,
)


def render_user_message(text: str):
    """Render a right-aligned user message bubble."""
    with ui.element("div").classes("msg-bubble msg-user"):
        ui.markdown(text)


def render_assistant_message(text: str, agent_runs: list | None = None):
    """Render a left-aligned assistant message with optional agent logs."""
    with ui.element("div").classes("msg-bubble msg-assistant"):
        # Avatar row
        with ui.row().classes("items-center gap-2 no-wrap").style("margin-bottom: 8px;"):
            ui.image("/static/images/logo.svg").style("height: 22px; width: auto;")
            ui.label("EvoLLM").classes("assistant-name").style(
                "font-weight: 600; font-size: 13px;"
            )

        # Main content
        ui.markdown(text)

        # Agent logs (expandable)
        if agent_runs:
            _render_agent_logs(agent_runs)


def _render_agent_logs(agent_runs: list):
    """Render expandable agent log section."""
    with ui.expansion("Agentu logai", icon="visibility").classes("w-full").style(
        "margin-top: 12px; font-size: 13px;"
    ):
        for run in agent_runs:
            color = AGENT_COLORS.get(run.agent_name, "#888")
            label = AGENT_LABELS.get(run.agent_name, run.agent_name)
            icon_map = {
                "planner": "/static/images/planner-agent.svg",
                "researcher": "/static/images/researcher-agent.svg",
                "coder": "/static/images/coder-agent.svg",
                "reviewer": "/static/images/reviewer-agent.svg",
            }
            with ui.element("div").classes("agent-log-section").style(
                f"border-left: 3px solid {color}; margin-bottom: 6px;"
            ):
                with ui.row().classes("items-center gap-2 no-wrap"):
                    svg = icon_map.get(run.agent_name)
                    if svg:
                        ui.image(svg).style("width: 20px; height: 20px;")
                    ui.label(label).style(
                        f"color: {color}; font-weight: 600; font-size: 13px;"
                    )
                ui.label(run.output).style(
                    "font-size: 12px; margin-top: 3px; opacity: 0.8;"
                )
