"""Top navigation bar with sidebar toggle, logo, dark/light toggle, RAG link, and logout."""

from nicegui import ui, app

from frontend.styles.theme import BG_CARD, TEXT_PRIMARY, BG_SURFACE, ACCENT, TEXT_SECONDARY


def create_header(on_logout_click=None, drawer=None):
    """Render the top header bar.  *drawer* is an optional left_drawer to toggle."""
    with ui.header().classes("items-center justify-between").style(
        f"background: {BG_CARD}; border-bottom: 1px solid {BG_SURFACE}; "
        f"padding: 0 20px; height: 56px;"
    ):
        # Left: sidebar toggle + logo
        with ui.row().classes("items-center gap-2 no-wrap"):
            if drawer is not None:
                ui.button(
                    icon="menu",
                    on_click=lambda: drawer.toggle(),
                ).props("flat round dense").classes("header-btn")

            ui.image("/static/images/logo.svg").style("height: 32px; width: auto;")

        # Right: actions
        with ui.row().classes("items-center gap-2 no-wrap"):
            # Dark/light mode toggle
            theme_btn = ui.button(
                icon="light_mode",
                on_click=lambda: ui.run_javascript("toggleTheme()"),
            ).props("flat round dense").classes("header-btn")
            # Add class to the icon so JS can find it
            ui.run_javascript(
                "setTimeout(function(){"
                "  document.querySelectorAll('.header-btn .q-icon').forEach(function(el,i){"
                "    if(el.textContent.trim()==='light_mode' || el.textContent.trim()==='dark_mode')"
                "      el.classList.add('theme-icon');"
                "  });"
                "}, 200)"
            )

            # RAG page link
            ui.button(
                "RAG Dokumentai",
                icon="folder_open",
                on_click=lambda: ui.navigate.to("/rag"),
            ).props("flat dense").classes("header-btn")

            ui.button(
                "Atsijungti",
                icon="logout",
                on_click=on_logout_click,
            ).props("flat dense").classes("header-btn")
