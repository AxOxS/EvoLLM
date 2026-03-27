"""Agent pipeline progress indicator – horizontal stepper."""

from __future__ import annotations

from nicegui import ui

from frontend.styles.theme import AGENT_COLORS, AGENT_LABELS


AGENT_ORDER = ["planner", "researcher", "coder", "reviewer"]
AGENT_ICONS = {
    "planner": "account_tree",
    "researcher": "search",
    "coder": "code",
    "reviewer": "verified",
}


class AgentProgress:
    """Manages the agent pipeline progress bar."""

    def __init__(self):
        self._container = None
        self._current_agent: str | None = None
        self._done_agents: set[str] = set()
        self._visible = False

    def create(self):
        """Create the progress bar container (initially hidden)."""
        self._container = ui.row().classes(
            "items-center justify-center gap-0 w-full agent-progress-bar"
        ).style(
            "padding: 12px 16px; border-radius: 12px; "
            "box-sizing: border-box; flex-wrap: wrap;"
        )
        self._container.set_visibility(False)
        return self

    def show(self):
        """Show and reset the progress bar."""
        self._current_agent = None
        self._done_agents = set()
        self._visible = True
        if self._container:
            self._container.set_visibility(True)
        self._render()

    def hide(self):
        """Hide the progress bar."""
        self._visible = False
        if self._container:
            self._container.set_visibility(False)

    def set_active(self, agent_name: str):
        """Mark an agent as currently active.
        If coder becomes active again (retry), reset coder+reviewer state."""
        if agent_name == "coder" and "coder" in self._done_agents:
            self._done_agents.discard("coder")
            self._done_agents.discard("reviewer")
        self._current_agent = agent_name
        self._render()

    def set_done(self, agent_name: str):
        """Mark an agent as completed."""
        self._done_agents.add(agent_name)
        self._current_agent = None
        self._render()

    def _render(self):
        """Re-render all steps."""
        if not self._container:
            return
        self._container.clear()
        with self._container:
            for i, agent in enumerate(AGENT_ORDER):
                color = AGENT_COLORS[agent]
                icon = AGENT_ICONS[agent]
                label = AGENT_LABELS[agent]

                if agent in self._done_agents:
                    state = "done"
                elif agent == self._current_agent:
                    state = "active"
                else:
                    state = "pending"

                with ui.element("div").classes(f"agent-step {state}").style(
                    f"background: {color}20; color: {color};"
                ):
                    if state == "done":
                        ui.icon("check_circle").style(f"font-size: 18px; color: {color};")
                    else:
                        ui.icon(icon).style("font-size: 18px;")
                    ui.label(label)

                # Connector line (not after last)
                if i < len(AGENT_ORDER) - 1:
                    ui.element("div").classes("agent-connector")
