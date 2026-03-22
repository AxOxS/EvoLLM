"""EvoLLM dark/light theme constants and CSS."""

# ── Colours (dark) ───────────────────────────────────────────────────
BG_PRIMARY = "#1a1a2e"
BG_CARD = "#16213e"
BG_SURFACE = "#0f3460"
TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#a0a0b0"
ACCENT = "#4A90D9"

# ── Colours (light) ──────────────────────────────────────────────────
BG_PRIMARY_LIGHT = "#f0f2f5"
BG_CARD_LIGHT = "#ffffff"
BG_SURFACE_LIGHT = "#e0e4ea"
TEXT_PRIMARY_LIGHT = "#1a1a2e"
TEXT_SECONDARY_LIGHT = "#555566"

AGENT_COLORS = {
    "planner": "#4A90D9",
    "researcher": "#27AE60",
    "coder": "#E67E22",
    "reviewer": "#E74C3C",
}

AGENT_LABELS = {
    "planner": "Planner",
    "researcher": "Researcher",
    "coder": "Coder",
    "reviewer": "Reviewer",
}


def _build_css():
    v = {
        "bg": BG_PRIMARY, "card": BG_CARD, "surface": BG_SURFACE,
        "text": TEXT_PRIMARY, "text_sec": TEXT_SECONDARY,
        "bg_l": BG_PRIMARY_LIGHT, "card_l": BG_CARD_LIGHT,
        "surf_l": BG_SURFACE_LIGHT, "text_l": TEXT_PRIMARY_LIGHT,
        "text_sec_l": TEXT_SECONDARY_LIGHT,
    }
    return """
/* ===== BASE (DARK) ===== */
body, .q-page, .nicegui-content {{
    background-color: {bg} !important;
    color: {text} !important;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}}
.q-drawer {{ background-color: {card} !important; }}
.nicegui-content {{ padding: 0 !important; }}
.q-page-container {{ padding-top: 0 !important; }}

/* ===== LIGHT MODE ===== */
body.light-mode, body.light-mode .q-page, body.light-mode .nicegui-content {{
    background-color: {bg_l} !important; color: {text_l} !important;
}}
/* Global text color catch-all for light mode */
body.light-mode label,
body.light-mode span,
body.light-mode p,
body.light-mode div {{
    color: {text_l};
}}
body.light-mode .q-drawer {{ background-color: {card_l} !important; border-color: {surf_l} !important; }}
body.light-mode .q-header {{ background: {card_l} !important; border-color: {surf_l} !important; }}
/* messages – exclude code blocks from the catch-all */
body.light-mode .msg-user {{ background: {surf_l} !important; color: {text_l} !important; }}
body.light-mode .msg-assistant {{ background: {card_l} !important; color: {text_l} !important; border: 1px solid {surf_l}; }}
body.light-mode .msg-bubble > *,
body.light-mode .msg-bubble p,
body.light-mode .msg-bubble li,
body.light-mode .msg-bubble h1, body.light-mode .msg-bubble h2,
body.light-mode .msg-bubble h3, body.light-mode .msg-bubble h4,
body.light-mode .msg-bubble .assistant-name {{ color: {text_l} !important; }}
/* keep code-block content light (dark bg) even in light mode */
body.light-mode .code-block-wrapper *,
body.light-mode .code-header *,
body.light-mode .msg-bubble pre *,
body.light-mode .msg-bubble pre {{ color: inherit; }}
/* input area */
body.light-mode .input-wrapper {{ background: {card_l} !important; border-color: {surf_l} !important; }}
body.light-mode .input-area {{ background: transparent !important; }}
body.light-mode .input-area .q-field__control {{ background: {bg_l} !important; }}
body.light-mode .input-area textarea {{ color: {text_l} !important; }}
body.light-mode .input-area .q-field__label {{ color: {text_sec_l} !important; }}
body.light-mode .toggle-row .q-icon {{ color: inherit !important; }}
body.light-mode .toggle-row label,
body.light-mode .toggle-row span {{ color: {text_l} !important; }}
/* sidebar */
body.light-mode .sidebar-item {{ color: {text_sec_l} !important; }}
body.light-mode .sidebar-item * {{ color: inherit !important; }}
body.light-mode .sidebar-item:hover {{ background: {surf_l} !important; color: {text_l} !important; }}
body.light-mode .sidebar-item.active {{ background: {surf_l} !important; color: {text_l} !important; }}
body.light-mode .q-drawer .q-btn {{ color: {text_l} !important; }}
body.light-mode .sidebar-new-btn {{ background: {surf_l} !important; color: {text_l} !important; }}
body.light-mode .q-drawer .q-separator {{ background: {surf_l} !important; }}
body.light-mode .q-drawer label,
body.light-mode .q-drawer span {{ color: {text_sec_l} !important; }}
/* agent progress bar */
.agent-progress-bar {{ background: {card}; }}
body.light-mode .agent-progress-bar {{ background: {card_l} !important; border: 1px solid {surf_l}; }}

/* CODE: always dark (IDE style) – do NOT lighten */
.msg-bubble pre,
body.light-mode .msg-bubble pre {{
    background: #0d1117 !important;
    color: {text} !important;
    border-color: #30363d !important;
}}
.msg-bubble pre code,
body.light-mode .msg-bubble pre code {{ background: none !important; color: {text} !important; }}
body.light-mode .code-header {{ background: #161b22 !important; color: #8b949e !important; }}
body.light-mode .code-header .code-copy-btn {{ color: #8b949e !important; border-color: #30363d !important; }}
body.light-mode .code-block-wrapper {{ border-color: #30363d !important; }}
/* inline code in light mode */
body.light-mode .msg-bubble code {{ background: {surf_l} !important; color: {text_l} !important; }}

/* agent logs */
body.light-mode .agent-log-section {{ background: {bg_l} !important; color: {text_sec_l} !important; }}
body.light-mode .agent-log-section label,
body.light-mode .agent-log-section span {{ color: {text_sec_l} !important; }}
body.light-mode .q-expansion-item {{ color: {text_l} !important; }}
body.light-mode .q-expansion-item .q-item__label,
body.light-mode .q-expansion-item .q-icon {{ color: {text_l} !important; }}
body.light-mode .q-expansion-item .q-item {{ color: {text_l} !important; }}

/* panels and cards */
body.light-mode .info-panel {{ background: {card_l} !important; }}
body.light-mode .info-panel label,
body.light-mode .info-panel span,
body.light-mode .info-panel div {{ color: {text_l}; }}
body.light-mode .agent-card {{ background: {card_l} !important; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
body.light-mode .agent-card label,
body.light-mode .agent-card span {{ color: {text_l} !important; }}
/* header buttons */
body.light-mode .q-header .q-btn {{ color: {text_l} !important; }}
body.light-mode .q-header .q-icon {{ color: {text_l} !important; }}
/* rag page */
body.light-mode .rag-doc-card {{ background: {card_l} !important; border-color: {surf_l} !important; color: {text_l} !important; }}
body.light-mode .rag-doc-card * {{ color: {text_l}; }}
body.light-mode .rag-doc-card:hover {{ background: {surf_l} !important; }}
body.light-mode .rag-drop-zone {{ border-color: #c0c4cc !important; }}
body.light-mode .rag-stat-card {{ background: {card_l} !important; border-color: {surf_l} !important; }}
body.light-mode .rag-stat-card label,
body.light-mode .rag-stat-card span {{ color: {text_l} !important; }}
body.light-mode .rag-page label,
body.light-mode .rag-page span,
body.light-mode .rag-page div {{ color: {text_l}; }}
/* upload widget */
body.light-mode .q-uploader {{ background: {card_l} !important; color: {text_l} !important; border-color: {surf_l} !important; }}
body.light-mode .q-uploader__header {{ background: {surf_l} !important; color: {text_l} !important; }}
/* auth */
body.light-mode .auth-card {{ background: {card_l} !important; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
body.light-mode .auth-card .q-field__control {{ background: {bg_l} !important; }}
body.light-mode .auth-card label,
body.light-mode .auth-card input {{ color: {text_l} !important; }}

/* scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {surface}; border-radius: 3px; }}
body.light-mode ::-webkit-scrollbar-thumb {{ background: #c0c0c8; }}

/* ===== LAYOUT ===== */
.chat-container {{
    display: flex;
    flex-direction: column;
    height: calc(100vh - 56px);
    margin-top: 56px;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}}

/* sidebar */
.q-drawer {{ overflow-x: hidden !important; }}
.q-drawer__content {{ overflow-x: hidden !important; overflow-y: auto !important; }}

/* messages – wider, less side padding */
.messages-area {{
    flex: 1 1 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 20px 24px 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-width: 100%;
    width: 100%;
    box-sizing: border-box;
    min-height: 0;
}}

/* bubbles */
.msg-bubble {{
    max-width: 80%;
    padding: 16px 20px;
    border-radius: 18px;
    line-height: 1.6;
    word-wrap: break-word;
    overflow-wrap: break-word;
    font-size: 15px;
    flex-shrink: 0;
}}
.msg-user {{
    align-self: flex-end;
    background: {surface};
    border-bottom-right-radius: 4px;
    color: {text};
}}
.msg-assistant {{
    align-self: flex-start;
    background: {card};
    border-bottom-left-radius: 4px;
    color: {text};
    max-width: 88%;
}}

/* ===== CODE (IDE style – always dark) ===== */
.msg-bubble pre {{
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 0 0 10px 10px;
    padding: 16px;
    margin: 0;
    font-size: 13px;
    line-height: 1.55;
    overflow-x: auto;
    max-width: 100%;
    white-space: pre;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    color: {text};
}}
.msg-bubble code {{
    background: {bg};
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
}}
.msg-bubble pre code {{ background: none; padding: 0; border-radius: 0; }}
.code-block-wrapper {{
    margin: 10px 0;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #30363d;
}}
.code-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #161b22;
    padding: 6px 14px;
    font-size: 12px;
    color: #8b949e;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
}}
.code-header .code-copy-btn {{
    position: static; opacity: 1;
    background: transparent;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
    display: flex; align-items: center; gap: 4px;
}}
.code-header .code-copy-btn:hover {{ background: #4A90D9; color: white; border-color: #4A90D9; }}
.code-header .code-copy-btn.copied {{ background: #27AE60; color: white; border-color: #27AE60; }}
.code-block-wrapper pre {{ border: none !important; border-radius: 0 !important; margin: 0 !important; }}

/* ===== INPUT ===== */
.input-wrapper {{
    width: 100%;
    background: {card};
    border-top: 1px solid {surface};
    flex-shrink: 0;
}}
.input-area {{
    padding: 14px 24px 20px;
    background: transparent;
    width: 100%;
    box-sizing: border-box;
}}
.input-row {{
    display: flex;
    align-items: flex-end;
    gap: 12px;
    width: 100%;
}}
.input-row .q-field {{ flex: 1; min-width: 0; }}
.input-row textarea {{ min-height: 48px !important; }}
.chat-textarea .q-field__control {{ background: {bg} !important; }}
.chat-textarea textarea {{ color: {text} !important; }}
body.light-mode .chat-textarea .q-field__control {{ background: {bg_l} !important; }}
body.light-mode .chat-textarea textarea {{ color: {text_l} !important; }}
.toggle-row {{
    display: flex; gap: 20px; padding: 6px 0 10px;
    align-items: center; flex-wrap: wrap;
}}
/* header buttons base color */
.header-btn {{ color: {text} !important; }}
body.light-mode .header-btn {{ color: {text_l} !important; }}

/* ===== AGENT PROGRESS ===== */
.agent-step {{
    display: flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 20px;
    font-size: 13px; font-weight: 600;
    transition: all 0.3s ease;
}}
.agent-step.active {{ animation: pulse 1.5s ease-in-out infinite; }}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.97); }}
}}
.agent-step.done {{ opacity: 0.7; }}
.agent-step.pending {{ opacity: 0.3; }}
.agent-connector {{ width: 28px; height: 2px; background: {surface}; flex-shrink: 0; }}

/* ===== SIDEBAR ===== */
.sidebar-item {{
    padding: 10px 14px; border-radius: 8px; cursor: pointer;
    color: {text_sec}; font-size: 14px; transition: background 0.2s;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}
.sidebar-item:hover {{ background: {surface}; color: {text}; }}
.sidebar-item.active {{ background: {surface}; color: {text}; }}

/* ===== AUTH ===== */
.auth-card {{
    background: {card} !important;
    border-radius: 16px; padding: 40px; width: 100%; max-width: 420px;
}}

/* ===== AGENT LOGS ===== */
.agent-log-section {{
    margin-top: 10px; padding: 10px 14px;
    background: {bg}; border-radius: 8px; font-size: 13px; color: {text_sec};
}}

/* ===== WELCOME CARDS ===== */
.agent-card {{
    background: {card}; border-radius: 14px; padding: 20px; text-align: center;
    transition: transform 0.2s, box-shadow 0.2s; cursor: default;
    flex: 1; min-width: 140px; max-width: 200px;
}}
.agent-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
.agent-card img {{ width: 56px; height: 56px; margin-bottom: 10px; }}

/* ===== INFO PANEL ===== */
.info-panel {{
    background: {card}; border-radius: 14px; padding: 24px;
    max-width: 900px; width: 100%; margin: 0 auto; box-sizing: border-box;
    transition: max-height 0.4s ease, opacity 0.3s ease, padding 0.3s ease;
    overflow: hidden;
}}
.info-panel.collapsed {{
    max-height: 0 !important; opacity: 0;
    padding-top: 0; padding-bottom: 0; border: none;
}}

/* ===== RAG PAGE ===== */
.rag-page-wrapper {{
    height: calc(100vh - 56px);
    margin-top: 56px;
    overflow-y: auto;
    width: 100%;
    box-sizing: border-box;
}}
.rag-page {{
    max-width: 800px;
    margin: 0 auto;
    padding: 32px;
    width: 100%;
    box-sizing: border-box;
}}
.rag-drop-zone {{
    border: 2px dashed {surface};
    border-radius: 16px;
    padding: 40px 24px;
    text-align: center;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    box-sizing: border-box;
}}
.rag-drop-zone .q-uploader {{
    width: 100% !important;
    max-width: 100% !important;
}}
.rag-drop-zone.drag-over {{ border-color: #27AE60; background: rgba(39,174,96,0.08); }}
.rag-doc-card {{
    background: {card};
    border: 1px solid {surface};
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: background 0.2s;
    width: 100%;
    box-sizing: border-box;
}}
.rag-doc-card:hover {{ background: {surface}; }}
.rag-stat-card {{
    background: {card};
    border: 1px solid {surface};
    border-radius: 12px;
    padding: 20px 28px;
    text-align: center;
    flex: 1;
    min-width: 120px;
}}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {{
    .messages-area {{ padding: 16px 12px; }}
    .input-area {{ padding: 10px 12px 16px; }}
    .msg-bubble {{ max-width: 95%; }}
    .msg-assistant {{ max-width: 98%; }}
    .agent-step {{ padding: 4px 8px; font-size: 11px; }}
    .agent-connector {{ width: 12px; }}
    .agent-card {{ min-width: 100px; padding: 14px; }}
    .agent-card img {{ width: 40px; height: 40px; }}
    .auth-card {{ padding: 24px 20px; margin: 0 12px; }}
    .info-panel {{ padding: 16px; }}
    .rag-page {{ padding: 16px; }}
    /* Hide button text on mobile, show only icons */
    .header-btn .q-btn__content > span:not(.q-icon),
    .header-btn .q-btn__content > .block {{
        display: none !important;
    }}
}}
@media (max-width: 480px) {{
    .toggle-row {{ gap: 10px; }}
    .agent-step span {{ display: none; }}
}}
""".format(**v)


GLOBAL_CSS = _build_css()

# ── JavaScript ───────────────────────────────────────────────────────
INTERACTIVE_JS = r"""
// 1. IDE-style code blocks with copy button
function initCopyButtons() {
    document.querySelectorAll('.msg-bubble pre').forEach(function(pre) {
        if (pre.parentElement && pre.parentElement.classList.contains('code-block-wrapper')) return;
        var code = pre.querySelector('code');
        var lang = '';
        if (code && code.className) {
            var m = code.className.match(/language-(\w+)/);
            if (m) lang = m[1];
        }
        var wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        var header = document.createElement('div');
        header.className = 'code-header';
        var langSpan = document.createElement('span');
        langSpan.textContent = lang || 'code';
        header.appendChild(langSpan);
        var btn = document.createElement('button');
        btn.className = 'code-copy-btn';
        btn.innerHTML = '<span>Copy</span>';
        btn.onclick = function() {
            var text = code ? code.textContent : pre.textContent;
            navigator.clipboard.writeText(text).then(function() {
                btn.innerHTML = '<span>Copied!</span>';
                btn.classList.add('copied');
                setTimeout(function() {
                    btn.innerHTML = '<span>Copy</span>';
                    btn.classList.remove('copied');
                }, 2000);
            });
        };
        header.appendChild(btn);
        wrapper.appendChild(header);
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
    });
}

// 2. Dark/light mode toggle
function toggleTheme() {
    document.body.classList.toggle('light-mode');
    var isLight = document.body.classList.contains('light-mode');
    document.querySelectorAll('.theme-icon').forEach(function(icon) {
        icon.textContent = isLight ? 'dark_mode' : 'light_mode';
    });
    localStorage.setItem('evollm-theme', isLight ? 'light' : 'dark');
}
function restoreTheme() {
    var saved = localStorage.getItem('evollm-theme');
    if (saved === 'light') {
        document.body.classList.add('light-mode');
        document.querySelectorAll('.theme-icon').forEach(function(icon) {
            icon.textContent = 'dark_mode';
        });
    }
}
restoreTheme();
setTimeout(restoreTheme, 200);

// 3. Toggle info panel
function toggleInfoPanel() {
    var panel = document.getElementById('info-panel');
    if (!panel) return;
    panel.classList.toggle('collapsed');
    var isHidden = panel.classList.contains('collapsed');
    var btn = document.getElementById('info-toggle-icon');
    if (btn) btn.textContent = isHidden ? 'expand_more' : 'expand_less';
}

// 4. RAG drag-and-drop
function initDragDrop() {
    var zone = document.getElementById('rag-drop-zone');
    if (!zone) return;
    zone.addEventListener('dragover', function(e) {
        e.preventDefault(); zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', function() {
        zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', function(e) {
        e.preventDefault(); zone.classList.remove('drag-over');
        var uploadInput = zone.querySelector('input[type="file"]');
        if (uploadInput && e.dataTransfer.files.length) {
            var dt = new DataTransfer();
            for (var i = 0; i < e.dataTransfer.files.length; i++) dt.items.add(e.dataTransfer.files[i]);
            uploadInput.files = dt.files;
            uploadInput.dispatchEvent(new Event('change', {bubbles: true}));
        }
    });
}

// MutationObserver for new messages
var _copyObserver = new MutationObserver(function() { initCopyButtons(); });
setTimeout(function() {
    initCopyButtons();
    var area = document.querySelector('.messages-area');
    if (area) _copyObserver.observe(area, {childList: true, subtree: true});
    initDragDrop();
}, 300);
"""
