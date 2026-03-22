"""Chat input area with RAG/Web Search toggles and send button."""

from __future__ import annotations

from nicegui import ui

from frontend.styles.theme import (
    BG_CARD,
    BG_SURFACE,
    BG_PRIMARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    ACCENT,
    AGENT_COLORS,
)


class ChatInput:
    """Bottom input area with toggles and send button – full width."""

    def __init__(self, on_send=None):
        self._on_send = on_send
        self._textarea = None
        self._rag_switch = None
        self._web_switch = None
        self._send_btn = None
        self._disabled = False

    @property
    def rag_enabled(self) -> bool:
        return self._rag_switch.value if self._rag_switch else True

    @property
    def web_search_enabled(self) -> bool:
        return self._web_switch.value if self._web_switch else False

    def create(self):
        """Build the input area UI."""
        # Outer wrapper stretches full width of chat-container
        with ui.element("div").classes("input-wrapper"):
            with ui.element("div").classes("input-area"):
                # Toggle row
                with ui.element("div").classes("toggle-row"):
                    # RAG toggle
                    with ui.row().classes("items-center gap-1 no-wrap"):
                        ui.icon("storage").style(
                            f"font-size: 18px; color: {AGENT_COLORS['researcher']};"
                        )
                        ui.label("RAG").style(
                            "font-size: 13px; font-weight: 600;"
                        )
                        self._rag_switch = ui.switch(value=True).props("dense color=green")

                    # Web Search toggle
                    with ui.row().classes("items-center gap-1 no-wrap"):
                        ui.icon("language").style(
                            f"font-size: 18px; color: {ACCENT};"
                        )
                        ui.label("Web paieska").style(
                            "font-size: 13px; font-weight: 600;"
                        )
                        self._web_switch = ui.switch(value=False).props("dense color=blue")

                # Input row – textarea fills all available width
                with ui.element("div").classes("input-row"):
                    self._textarea = (
                        ui.textarea(placeholder="Iveskite uzduoti...")
                        .props("autogrow outlined dense")
                        .classes("chat-textarea")
                        .on("keydown.enter.prevent", self._handle_send)
                    )

                    self._send_btn = (
                        ui.button(icon="send", on_click=self._handle_send)
                        .props("round unelevated")
                        .style(
                            f"background: {ACCENT}; color: white; "
                            f"min-width: 46px; min-height: 46px; flex-shrink: 0;"
                        )
                    )

        return self

    def set_disabled(self, disabled: bool):
        """Disable/enable the input area (FR15 – one task at a time)."""
        self._disabled = disabled
        if self._textarea:
            self._textarea.set_enabled(not disabled)
        if self._send_btn:
            self._send_btn.set_enabled(not disabled)

    def clear(self):
        """Clear the text input."""
        if self._textarea:
            self._textarea.set_value("")

    async def _handle_send(self):
        """Handle send button click or Enter key."""
        if self._disabled:
            return
        text = self._textarea.value.strip() if self._textarea else ""
        if not text:
            return
        if self._on_send:
            await self._on_send(text)
