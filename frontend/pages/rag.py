"""RAG document management page – upload, view, delete documents."""

from __future__ import annotations

from nicegui import ui, app

from frontend.styles.theme import (
    BG_CARD,
    BG_SURFACE,
    TEXT_SECONDARY,
    ACCENT,
    AGENT_COLORS,
    GLOBAL_CSS,
    INTERACTIVE_JS,
)
from frontend.services import get_api


async def rag_page():
    """Render the RAG document management page."""
    mock_api = get_api()
    ui.add_css(GLOBAL_CSS)

    docs = await mock_api.get_rag_documents()

    # ── Header ───────────────────────────────────────────────────────
    with ui.header().classes("items-center justify-between").style(
        f"background: {BG_CARD}; border-bottom: 1px solid {BG_SURFACE}; "
        f"padding: 0 20px; height: 56px;"
    ):
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.image("/static/images/logo.svg").style("height: 32px; width: auto;")

        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.button(
                icon="light_mode",
                on_click=lambda: ui.run_javascript("toggleTheme()"),
            ).props("flat round dense").classes("header-btn")
            ui.run_javascript(
                "setTimeout(function(){"
                "  document.querySelectorAll('.header-btn .q-icon').forEach(function(el){"
                "    if(el.textContent.trim()==='light_mode' || el.textContent.trim()==='dark_mode')"
                "      el.classList.add('theme-icon');"
                "  });"
                "}, 200)"
            )

            ui.button(
                "Back to Chat",
                icon="chat",
                on_click=lambda: ui.navigate.to("/"),
            ).props("flat dense").classes("header-btn")

    # ── Main content (centered, proportional) ───────────────────────
    with ui.element("div").classes("rag-page-wrapper"):
        with ui.column().classes("rag-page"):

            # Title
            with ui.row().classes("items-center gap-3 no-wrap"):
                ui.icon("storage").style(
                    f"font-size: 36px; color: {AGENT_COLORS['researcher']};"
                )
                ui.label("RAG Document Management").style(
                    f"font-size: 22px; font-weight: 700;"
                )

            ui.label(
                "Upload documents to the vector knowledge base (ChromaDB). "
                "The system will use them to generate responses via the Researcher agent."
            ).style(
                f"font-size: 14px; line-height: 1.6; margin: 8px 0 24px; opacity: 0.7;"
            )

            # ── Stats row (dynamic) ────────────────────────────────
            stats_container = ui.row().classes("w-full gap-4").style("margin-bottom: 24px;")

            def _refresh_stats():
                stats_container.clear()
                with stats_container:
                    with ui.element("div").classes("rag-stat-card"):
                        ui.label(str(len(docs))).style(
                            f"color: {AGENT_COLORS['researcher']}; font-size: 28px; font-weight: 700;"
                        )
                        ui.label("Documents").style("font-size: 12px; opacity: 0.7;")

                    total_kb = sum(d.size_kb for d in docs)
                    with ui.element("div").classes("rag-stat-card"):
                        ui.label(f"{total_kb:.0f}").style(
                            f"color: {ACCENT}; font-size: 28px; font-weight: 700;"
                        )
                        ui.label("KB total").style("font-size: 12px; opacity: 0.7;")

            _refresh_stats()

            # ── Upload zone (drag and drop) ─────────────────────────
            with ui.element("div").classes("rag-drop-zone").props('id=rag-drop-zone'):
                ui.icon("cloud_upload").style(
                    f"font-size: 48px; color: {AGENT_COLORS['researcher']}; opacity: 0.7;"
                )
                ui.label("Drag and drop files here or click the button below").style(
                    "font-size: 14px; margin: 12px 0 4px; opacity: 0.7;"
                )
                ui.label("Supported formats: PDF, TXT, DOCX").style(
                    "font-size: 12px; margin-bottom: 16px; opacity: 0.5;"
                )

                upload_status = ui.label("").style(
                    "font-size: 13px; margin-top: 8px;"
                )

                async def handle_upload(e):
                    upload_status.set_text("Uploading...")
                    try:
                        if hasattr(e, 'file'):
                            # NiceGUI >= 3.x: e.file.name, await e.file.read()
                            filename = e.file.name
                            data = await e.file.read()
                        else:
                            # NiceGUI 2.x: e.name, e.content (BinaryIO)
                            filename = e.name
                            e.content.seek(0)
                            data = e.content.read()
                    except Exception as ex:
                        upload_status.set_text(f"Upload error: {ex}")
                        upload_status.style(f"color: {AGENT_COLORS['reviewer']};")
                        return
                    if not data:
                        upload_status.set_text("Error: file is empty")
                        upload_status.style(f"color: {AGENT_COLORS['reviewer']};")
                        return
                    result = await mock_api.upload_document(filename, data)
                    if result.get("ok"):
                        upload_status.set_text(result["message"])
                        upload_status.style(f"color: {AGENT_COLORS['researcher']};")
                        nonlocal docs
                        docs = await mock_api.get_rag_documents()
                        _refresh_docs()
                        _refresh_stats()
                    else:
                        upload_status.set_text(result.get("error", "Error"))
                        upload_status.style(f"color: {AGENT_COLORS['reviewer']};")

                ui.upload(
                    label="Choose file",
                    auto_upload=True,
                    on_upload=handle_upload,
                ).props("accept='.pdf,.txt,.docx' flat bordered").classes("w-full")

            # ── Document list ───────────────────────────────────────
            ui.label("Uploaded Documents").style(
                "font-size: 18px; font-weight: 700; margin-top: 32px;"
            )

            doc_list_container = ui.column().classes("w-full gap-2").style("margin-top: 12px;")

            def _refresh_docs():
                doc_list_container.clear()
                with doc_list_container:
                    if not docs:
                        ui.label("No documents uploaded yet").style(
                            "font-size: 14px; padding: 16px; opacity: 0.6;"
                        )
                    else:
                        for doc in docs:
                            _render_doc_card(doc)

            def _render_doc_card(doc):
                icon_map = {"pdf": "picture_as_pdf", "txt": "description", "docx": "article"}
                color_map = {"pdf": "#E74C3C", "txt": "#4A90D9", "docx": "#27AE60"}
                icon = icon_map.get(doc.doc_type, "insert_drive_file")
                color = color_map.get(doc.doc_type, TEXT_SECONDARY)

                with ui.element("div").classes("rag-doc-card"):
                    ui.icon(icon).style(f"font-size: 32px; color: {color};")
                    with ui.column().classes("gap-0").style("flex: 1; min-width: 0;"):
                        ui.label(doc.filename).style(
                            "font-size: 14px; font-weight: 600;"
                        )
                        ui.label(f"{doc.size_kb} KB  ·  Uploaded: {doc.uploaded_at}").style(
                            "font-size: 12px; opacity: 0.6;"
                        )

                    async def delete_doc(d=doc):
                        await mock_api.delete_rag_document(d.id)
                        nonlocal docs
                        docs = await mock_api.get_rag_documents()
                        _refresh_docs()
                        _refresh_stats()

                    ui.button(icon="delete", on_click=delete_doc).props(
                        "flat round dense"
                    ).style(f"color: {AGENT_COLORS['reviewer']};")

            _refresh_docs()

    # JS for drag-drop and theme
    ui.add_body_html(f"<script>{INTERACTIVE_JS}</script>")
    ui.run_javascript("setTimeout(initDragDrop, 500)")
