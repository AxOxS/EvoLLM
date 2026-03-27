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


class StreamingMessage:
    """A mutable assistant message with typewriter animation.

    Instead of dumping big chunks at once (which feels chunky), this
    reveals text word-by-word using a NiceGUI timer so it feels like
    the model is typing in real time.
    """

    # Reveal one word every TICK_MS milliseconds
    TICK_S = 0.035  # 35ms ≈ ~28 words/sec – fast enough to keep up with LLM output

    def __init__(self):
        self._container = None
        self._markdown = None
        self._logs_container = None
        self._timer = None
        # Typewriter state
        self._target_text: str = ""       # full text received so far
        self._shown_pos: int = 0          # character index shown so far
        self._target_words: list[str] = []
        self._shown_word_count: int = 0

    def create(self):
        """Create the streaming message bubble. Call inside a `with messages_area:` block."""
        self._container = ui.element("div").classes("msg-bubble msg-assistant")
        with self._container:
            with ui.row().classes("items-center gap-2 no-wrap").style("margin-bottom: 8px;"):
                ui.image("/static/images/logo.svg").style("height: 22px; width: auto;")
                ui.label("EvoLLM").classes("assistant-name").style(
                    "font-weight: 600; font-size: 13px;"
                )
            self._markdown = ui.markdown("")
            self._logs_container = ui.element("div")
            # Timer drives the typewriter; starts deactivated
            self._timer = ui.timer(self.TICK_S, self._tick, active=False)
        return self

    def update(self, text: str):
        """Called when a new polling chunk arrives. Feeds the typewriter."""
        if text == self._target_text:
            return

        # Detect text reset (reviewer rejected → coder restarted).
        # If new text doesn't start with what we've already shown, reset.
        currently_visible = self._target_text[:self._shown_pos]
        if currently_visible and not text.startswith(currently_visible):
            self._reset_typewriter()

        self._target_text = text
        self._target_words = text.split()
        if self._timer and not self._timer.active:
            self._timer.activate()

    def reset(self, placeholder: str = ""):
        """Clear the streamed text and show a placeholder (e.g. revision note)."""
        self._reset_typewriter()
        self._target_text = ""
        if self._markdown:
            self._markdown.set_content(placeholder)

    def _reset_typewriter(self):
        """Reset typewriter state to the beginning."""
        self._shown_pos = 0
        self._shown_word_count = 0
        self._target_text = ""
        self._target_words = []

    def _tick(self):
        """Reveal the next word."""
        if self._shown_word_count < len(self._target_words):
            self._shown_word_count += 1
            # Reconstruct text up to current word count.
            # We use the original text up to the end of the Nth word so that
            # whitespace (newlines, indentation) is preserved exactly.
            word = self._target_words[self._shown_word_count - 1]
            # Find this word's end position in the original text
            pos = self._target_text.find(word, self._shown_pos)
            if pos >= 0:
                self._shown_pos = pos + len(word)
            else:
                # Fallback – just join words
                self._shown_pos = len(" ".join(self._target_words[:self._shown_word_count]))
            visible = self._target_text[:self._shown_pos]
            if self._markdown:
                self._markdown.set_content(visible)
        else:
            # Caught up with target – pause until next update() call
            if self._timer:
                self._timer.deactivate()

    def finalize(self, text: str, agent_runs: list | None = None):
        """Set the final text and add agent logs."""
        if self._timer:
            self._timer.deactivate()
        if self._markdown:
            self._markdown.set_content(text)
        if agent_runs and self._logs_container:
            with self._logs_container:
                _render_agent_logs(agent_runs)

    def delete(self):
        """Remove this message from the DOM."""
        if self._timer:
            self._timer.deactivate()
        if self._container:
            self._container.delete()


def _render_agent_logs(agent_runs: list):
    """Render expandable agent log section."""
    with ui.expansion("Agent Logs", icon="visibility").classes("w-full").style(
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
