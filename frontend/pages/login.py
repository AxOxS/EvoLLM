"""Login page – simple form only."""

from nicegui import ui, app

from frontend.styles.theme import (
    BG_PRIMARY,
    BG_CARD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    ACCENT,
    GLOBAL_CSS,
)
from frontend.services import get_api


def login_page():
    """Render the login page."""
    mock_api = get_api()
    ui.add_css(GLOBAL_CSS)

    with ui.column().classes("items-center justify-center").style(
        "min-height: 100vh; width: 100%; padding: 24px 16px; box-sizing: border-box;"
    ):
        # Logo
        ui.image("/static/images/logo.svg").style("height: 48px; width: auto; margin-bottom: 8px;")

        # Card
        with ui.card().classes("auth-card items-center"):
            ui.label("Sign In").style(
                f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700; "
                f"margin-bottom: 4px;"
            )
            ui.label("Enter your credentials").style(
                f"color: {TEXT_SECONDARY}; font-size: 14px; margin-bottom: 20px;"
            )

            email = (
                ui.input(label="Email")
                .props("outlined dense dark")
                .classes("w-full")
                .style(f"color: {TEXT_PRIMARY};")
            )
            password = (
                ui.input(label="Password", password=True, password_toggle_button=True)
                .props("outlined dense dark")
                .classes("w-full")
                .style(f"color: {TEXT_PRIMARY};")
            )

            error_label = ui.label("").style(
                "color: #E74C3C; font-size: 13px; min-height: 20px;"
            )

            async def handle_login():
                error_label.set_text("")
                result = await mock_api.login(email.value, password.value)
                if result["ok"]:
                    app.storage.user["token"] = result["token"]
                    app.storage.user["email"] = result["email"]
                    ui.navigate.to("/")
                else:
                    error_label.set_text(result["error"])

            ui.button("Sign In", on_click=handle_login).props(
                "unelevated rounded"
            ).classes("w-full").style(
                f"background: {ACCENT}; color: white; margin-top: 8px; height: 44px;"
            )

            with ui.row().classes("items-center gap-1 q-mt-md"):
                ui.label("Don't have an account?").style(
                    f"color: {TEXT_SECONDARY}; font-size: 13px;"
                )
                ui.link("Register", "/register").style(
                    f"color: {ACCENT}; font-size: 13px; font-weight: 600;"
                )
